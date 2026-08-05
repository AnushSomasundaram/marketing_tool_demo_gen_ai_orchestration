from tests.conftest import create_and_generate_campaign


def test_instagram_connect_reports_demo_mode(client):
    response = client.get("/api/instagram/connect")
    assert response.status_code == 200
    assert response.json()["demoMode"] is True


def test_demo_publish_flow_completes_and_is_marked_simulated(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset = next(a for a in campaign["assets"] if a["status"] == "completed")

    response = client.post(
        "/api/instagram/publish",
        json={"campaignId": campaign["id"], "assetId": asset["id"], "isAiGenerated": True},
    )
    assert response.status_code == 202
    job = response.json()
    assert job["isSimulated"] is True
    assert job["status"] in ("queued", "container_created", "processing", "publishing", "completed")

    status_response = client.get(f"/api/instagram/publish/{job['id']}")
    assert status_response.status_code == 200
    final = status_response.json()
    assert final["status"] == "completed"
    assert final["isSimulated"] is True
    assert final["instagramMediaId"] is not None
    assert "simulated" in final["permalink"]

    updated_campaign = client.get(f"/api/campaigns/{campaign['id']}").json()
    assert updated_campaign["status"] == "published"


def test_publish_requires_completed_asset(client, product_image_bytes):
    """TestClient drains BackgroundTasks synchronously before returning, so a
    freshly-added asset is already 'completed' by the time a second request
    could observe it — there's no way to catch it mid-flight through the API
    alone. Set an asset's status directly in the DB to test the validation
    deterministically instead."""
    from app.database import SessionLocal
    from app.models.asset import Asset

    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset_id = campaign["assets"][0]["id"]

    db = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        asset.status = "processing"
        db.commit()
    finally:
        db.close()

    publish_response = client.post(
        "/api/instagram/publish",
        json={"campaignId": campaign["id"], "assetId": asset_id},
    )
    assert publish_response.status_code == 409


def test_publish_requires_ownership(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset = campaign["assets"][0]

    response = client.post(
        "/api/instagram/publish",
        json={"campaignId": "not-a-real-campaign", "assetId": asset["id"]},
    )
    assert response.status_code == 404
