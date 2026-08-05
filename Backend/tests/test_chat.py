from tests.conftest import create_and_generate_campaign


def _completed_image_asset(campaign: dict) -> dict:
    return next(a for a in campaign["assets"] if a["type"] == "image" and a["status"] == "completed")


def test_entire_campaign_scope_regenerates_images(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    image_before = _completed_image_asset(campaign)

    response = client.post(
        f"/api/campaigns/{campaign['id']}/chat",
        json={"message": "Make the visual style more energetic", "scope": "campaign"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["type"] == "regenerate_all_images"

    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    image_after = next(
        a for a in updated_campaign["assets"] if a["id"] != image_before["id"] and a["type"] == "image"
    )
    assert image_after["version"] == image_before["version"] + 1


def test_selected_asset_scope_revises_that_asset_only(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    target = _completed_image_asset(campaign)
    other_ids = {a["id"] for a in campaign["assets"] if a["id"] != target["id"]}

    response = client.post(
        f"/api/campaigns/{campaign['id']}/chat",
        json={
            "message": "Make this one darker and more premium",
            "scope": "selected_asset",
            "selectedAssetId": target["id"],
        },
    )
    assert response.status_code == 200

    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    updated_ids = {a["id"] for a in updated_campaign["assets"]}
    # The target's id changed (new version); every other asset id is untouched.
    assert target["id"] not in updated_ids
    assert other_ids <= updated_ids


def test_caption_only_scope_leaves_visuals_untouched(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    target = _completed_image_asset(campaign)

    response = client.post(
        f"/api/campaigns/{campaign['id']}/chat",
        json={
            "message": "Make the caption punchier",
            "scope": "caption_only",
            "selectedAssetId": target["id"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["type"] == "revise_caption"

    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    updated_asset = next(a for a in updated_campaign["assets"] if a["id"] == target["id"])
    # Same asset id/version (visuals untouched), caption text changed.
    assert updated_asset["version"] == target["version"]
    assert updated_asset["previewUrl"] == target["previewUrl"]
    assert updated_asset["caption"] != target["caption"]


def test_visual_only_scope_leaves_caption_untouched(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    target = _completed_image_asset(campaign)

    response = client.post(
        f"/api/campaigns/{campaign['id']}/chat",
        json={
            "message": "Make the background darker",
            "scope": "visual_only",
            "selectedAssetId": target["id"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["type"] == "revise_image"

    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    new_asset = next(
        a for a in updated_campaign["assets"] if a["id"] != target["id"] and a["title"] == target["title"]
    )
    assert new_asset["version"] == target["version"] + 1
    # Caption text carries over unchanged from the visual-only revision.
    assert new_asset["caption"] == target["caption"]


def test_caption_only_scope_rejects_image_action(client, product_image_bytes):
    """Even if the model tried to sneak a revise_image action into a
    caption_only turn, server-side validation must drop it."""
    from app.models.enums import ChatActionType
    from app.schemas.plan import ChatActionPlanItem
    from app.services.chat_service import _validate_actions

    actions = [
        ChatActionPlanItem(type=ChatActionType.REVISE_IMAGE, asset_id="asset_1", instruction="x"),
        ChatActionPlanItem(type=ChatActionType.REVISE_CAPTION, asset_id="asset_1", instruction="y"),
    ]
    validated = _validate_actions(
        actions, scope="caption_only", selected_asset_id="asset_1", campaign_asset_ids={"asset_1"}
    )
    assert [a.type for a in validated] == [ChatActionType.REVISE_CAPTION]


def test_scoped_action_cannot_target_a_foreign_asset_id(client):
    from app.models.enums import ChatActionType
    from app.schemas.plan import ChatActionPlanItem
    from app.services.chat_service import _validate_actions

    actions = [
        ChatActionPlanItem(type=ChatActionType.REVISE_IMAGE, asset_id="someone_elses_asset", instruction="x")
    ]
    validated = _validate_actions(
        actions, scope="selected_asset", selected_asset_id="asset_1", campaign_asset_ids={"asset_1"}
    )
    # The action gets force-pointed at the caller's selected_asset_id, never
    # at whatever assetId the model returned.
    assert len(validated) == 1
    assert validated[0].asset_id == "asset_1"


def test_missing_selected_asset_id_drops_all_actions_for_scoped_requests(client):
    from app.models.enums import ChatActionType
    from app.schemas.plan import ChatActionPlanItem
    from app.services.chat_service import _validate_actions

    actions = [ChatActionPlanItem(type=ChatActionType.REVISE_CAPTION, instruction="x")]
    validated = _validate_actions(
        actions, scope="caption_only", selected_asset_id=None, campaign_asset_ids={"asset_1"}
    )
    assert validated == []


def test_invalid_scope_returns_400(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    response = client.post(
        f"/api/campaigns/{campaign['id']}/chat",
        json={"message": "hello", "scope": "not_a_real_scope"},
    )
    assert response.status_code == 400
