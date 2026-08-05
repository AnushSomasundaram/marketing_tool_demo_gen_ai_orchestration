from tests.conftest import create_and_generate_campaign


def _completed_image_asset(campaign: dict) -> dict:
    return next(a for a in campaign["assets"] if a["type"] == "image" and a["status"] == "completed")


def test_caption_generation_service_produces_hashtags_and_cta(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    for asset in campaign["assets"]:
        if asset["status"] != "completed":
            continue
        assert asset["caption"]
        assert len(asset["hashtags"]) > 0
        assert all(tag.startswith("#") for tag in asset["hashtags"])
        assert asset["callToAction"]


def _current_caption_id(client, campaign_id: str, asset_id: str) -> str:
    response = client.post(
        f"/api/campaigns/{campaign_id}/captions", json={"assetId": asset_id, "tone": "professional"}
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_update_caption_creates_new_version(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset = _completed_image_asset(campaign)
    caption_id = _current_caption_id(client, campaign["id"], asset["id"])

    response = client.patch(
        f"/api/captions/{caption_id}", json={"caption": "A brand new caption", "hashtags": ["#New"]}
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] != caption_id
    assert updated["version"] == 2
    assert updated["caption"] == "A brand new caption"

    versions = client.get(f"/api/captions/{updated['id']}/versions").json()
    assert [v["version"] for v in versions] == [1, 2]


def test_generate_alternative_caption_respects_tone(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset = _completed_image_asset(campaign)
    caption_id = _current_caption_id(client, campaign["id"], asset["id"])

    response = client.post(f"/api/captions/{caption_id}/alternatives", json={"tone": "luxury"})
    assert response.status_code == 200
    assert response.json()["caption"] != ""


def test_restore_caption_version(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset = _completed_image_asset(campaign)
    caption_id = _current_caption_id(client, campaign["id"], asset["id"])
    original_text = client.get(f"/api/captions/{caption_id}/versions").json()[0]["caption"]

    revised = client.post(f"/api/captions/{caption_id}/revise", json={"instruction": "make it shorter"})
    assert revised.status_code == 200
    revised_id = revised.json()["id"]

    restored = client.post(f"/api/captions/{revised_id}/restore/{caption_id}")
    assert restored.status_code == 200
    assert restored.json()["caption"] == original_text
    assert restored.json()["version"] == 3


def test_create_caption_for_unknown_asset_returns_404(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    response = client.post(f"/api/campaigns/{campaign['id']}/captions", json={"assetId": "not-a-real-asset"})
    assert response.status_code == 404
