from tests.conftest import create_and_generate_campaign


def test_mock_job_progress_is_recorded(client, product_image_bytes):
    campaign = create_and_generate_campaign(client, product_image_bytes)

    response = client.get(f"/api/campaigns/{campaign['id']}/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) > 0

    job_types = {j["jobType"] for j in jobs}
    assert "campaign_plan" in job_types
    assert "caption" in job_types
    assert "image" in job_types
    assert "video" in job_types

    for job in jobs:
        assert job["status"] in ("completed", "failed")
        if job["status"] == "completed":
            assert job["progress"] == 100
        else:
            assert job["errorMessage"]


def test_failed_provider_call_marks_asset_failed(client, product_image_bytes, monkeypatch):
    """Forces the image provider to fail deterministically and verifies the
    asset/job/campaign all reflect the failure without crashing anything."""
    from app.services.exceptions import ProviderSafetyError
    from app.services.providers.image import mock_image

    async def _always_fail(self, *, prompt, reference_image_bytes, aspect_ratio):
        raise ProviderSafetyError("Simulated failure for testing.", provider="mock")

    monkeypatch.setattr(mock_image.MockImageProvider, "generate", _always_fail)

    campaign = create_and_generate_campaign(client, product_image_bytes)
    image_assets = [a for a in campaign["assets"] if a["type"] == "image"]

    assert all(a["status"] == "failed" for a in image_assets)
    assert all(a["errorMessage"] for a in image_assets)
    assert campaign["status"] in ("partially_failed", "failed")

    jobs = client.get(f"/api/campaigns/{campaign['id']}/jobs").json()
    image_jobs = [j for j in jobs if j["jobType"] == "image"]
    assert all(j["status"] == "failed" for j in image_jobs)
