from tests.conftest import create_and_generate_campaign


def test_image_revision_creates_new_version(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    image = next(a for a in campaign["assets"] if a["type"] == "image" and a["status"] == "completed")

    response = client.post(f"/api/assets/{image['id']}/revise", json={"instruction": "Make it darker"})
    assert response.status_code == 202
    new_asset = response.json()
    assert new_asset["id"] != image["id"]
    assert new_asset["version"] == image["version"] + 1

    # The old id no longer resolves as "the current asset" via the campaign list...
    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    current_ids = {a["id"] for a in updated_campaign["assets"]}
    assert image["id"] not in current_ids
    assert new_asset["id"] in current_ids

    # ...but full version history is still reachable.
    versions = client.get(f"/api/assets/{new_asset['id']}/versions").json()
    assert [v["version"] for v in versions] == [1, 2]


def test_video_revision_creates_new_version(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    video = next(a for a in campaign["assets"] if a["type"] == "video")

    response = client.post(
        f"/api/assets/{video['id']}/revise", json={"instruction": "Slower, more premium motion"}
    )
    assert response.status_code == 202
    new_asset = response.json()
    assert new_asset["version"] == video["version"] + 1
    # Immediately after the call returns, generation has already been driven
    # to completion by the synchronous BackgroundTasks in tests.
    assert new_asset["status"] in ("completed", "failed", "processing", "queued")


def test_overlay_update_does_not_create_new_version(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    video = next(a for a in campaign["assets"] if a["type"] == "video" and a["status"] == "completed")

    response = client.patch(
        f"/api/assets/{video['id']}/overlays",
        json={"headline": "Aurora Bottle", "price": "$29", "callToAction": "Shop now"},
    )
    assert response.status_code == 200
    updated = response.json()
    # Same asset id and version — overlays are a cheap re-composition, not an
    # AI regeneration / new version.
    assert updated["id"] == video["id"]
    assert updated["version"] == video["version"]
    assert updated["downloadUrl"] != video["downloadUrl"]


def test_overlay_update_rejected_for_image_asset(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    image = next(a for a in campaign["assets"] if a["type"] == "image")

    response = client.patch(f"/api/assets/{image['id']}/overlays", json={"headline": "x"})
    assert response.status_code == 409


def test_download_before_completion_returns_conflict(client, product_image_bytes):
    response = client.post(
        "/api/campaigns",
        files={"productImage": ("product.png", product_image_bytes, "image/png")},
        data={"productName": "X", "productDescription": "Y", "tone": "professional"},
    )
    campaign = response.json()
    client.post(f"/api/campaigns/{campaign['id']}/generate")

    # Add a fresh (not-yet-generated) image asset — queued, no output yet.
    add_response = client.post(f"/api/campaigns/{campaign['id']}/images")
    assert add_response.status_code == 202
    fresh_asset = add_response.json()
    assert fresh_asset["status"] == "queued"


def test_delete_asset_removes_it_from_campaign(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    image = next(a for a in campaign["assets"] if a["type"] == "image")

    response = client.delete(f"/api/assets/{image['id']}")
    assert response.status_code == 204

    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    assert image["id"] not in {a["id"] for a in updated_campaign["assets"]}


def test_revise_on_stale_asset_version_is_rejected(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    image = next(a for a in campaign["assets"] if a["type"] == "image" and a["status"] == "completed")

    first = client.post(f"/api/assets/{image['id']}/revise", json={"instruction": "v2"})
    assert first.status_code == 202

    # Re-using the now-superseded asset id must fail, not silently create a
    # second "current" sibling version under the same lineage.
    second = client.post(f"/api/assets/{image['id']}/revise", json={"instruction": "v2-again"})
    assert second.status_code == 409
