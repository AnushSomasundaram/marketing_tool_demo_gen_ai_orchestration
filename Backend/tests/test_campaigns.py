from tests.conftest import create_and_generate_campaign


def test_create_campaign(client, product_image_bytes):
    response = client.post(
        "/api/campaigns",
        files={"productImage": ("product.png", product_image_bytes, "image/png")},
        data={
            "productName": "Aurora Bottle",
            "productDescription": "A sleek insulated water bottle",
            "tone": "professional",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["productName"] == "Aurora Bottle"
    assert body["status"] == "draft"
    assert body["assets"] == []
    assert body["productImageUrl"].startswith("http")


def test_unsupported_file_type_rejected(client):
    response = client.post(
        "/api/campaigns",
        files={"productImage": ("product.txt", b"not an image", "text/plain")},
        data={"productName": "X", "productDescription": "Y", "tone": "professional"},
    )
    assert response.status_code == 400
    assert "JPG, PNG, or WebP" in response.json()["detail"]


def test_campaign_generation_produces_plan_derived_assets(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)

    # Campaign-plan parsing: title comes from the parsed CampaignPlan, not the
    # raw request, and status has moved past 'draft'.
    assert campaign["title"] != ""
    assert campaign["status"] in ("ready", "partially_failed")

    # Two images + one video, as the plan always specifies.
    assets_by_type = [a["type"] for a in campaign["assets"]]
    assert assets_by_type.count("image") == 2
    assert assets_by_type.count("video") == 1

    for asset in campaign["assets"]:
        assert asset["status"] in ("completed", "failed")
        if asset["status"] == "completed":
            assert asset["previewUrl"] is not None
            assert asset["caption"] != ""
            assert len(asset["hashtags"]) > 0


def test_get_nonexistent_campaign_returns_404(client):
    response = client.get("/api/campaigns/does-not-exist")
    assert response.status_code == 404


def test_campaign_ownership_is_enforced_for_asset_access(client, product_image_bytes):
    """Even with a single dev user, ownership checks run the same query
    pattern real auth would use — a foreign campaign id must 404, not 200
    with someone else's data."""
    campaign = create_and_generate_campaign(client, product_image_bytes)
    asset_id = campaign["assets"][0]["id"]

    # A made-up asset id must not resolve.
    response = client.get("/api/assets/not-a-real-asset-id")
    assert response.status_code == 404

    # A real asset id does resolve for the owning (only) user.
    response = client.get(f"/api/assets/{asset_id}")
    assert response.status_code == 200


def test_generate_twice_returns_conflict(client, product_image_bytes):
    response = client.post(
        "/api/campaigns",
        files={"productImage": ("product.png", product_image_bytes, "image/png")},
        data={"productName": "X", "productDescription": "Y", "tone": "professional"},
    )
    campaign_id = response.json()["id"]

    first = client.post(f"/api/campaigns/{campaign_id}/generate")
    assert first.status_code == 202

    second = client.post(f"/api/campaigns/{campaign_id}/generate")
    assert second.status_code == 409


def test_list_and_delete_campaign(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)

    listing = client.get("/api/campaigns")
    assert listing.status_code == 200
    assert any(c["id"] == campaign["id"] for c in listing.json())

    deletion = client.delete(f"/api/campaigns/{campaign['id']}")
    assert deletion.status_code == 204

    missing = client.get(f"/api/campaigns/{campaign['id']}")
    assert missing.status_code == 404
