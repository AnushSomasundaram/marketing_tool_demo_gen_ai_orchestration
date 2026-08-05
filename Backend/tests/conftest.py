"""Test configuration. Forces mock providers, demo Instagram mode, and local
storage regardless of the developer's real .env — tests must never spend API
credits or make real network calls to OpenAI/Runway/Cloudinary/Meta.

Environment variables are set BEFORE any `app.*` module is imported, so
pydantic-settings picks them up on first read (env vars win over .env).
"""

import os
import shutil
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_campaign_studio.db"
TEST_STORAGE_ROOT = Path(__file__).resolve().parent / "test_storage"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["USE_MOCK_PROVIDERS"] = "true"
os.environ["INSTAGRAM_DEMO_MODE"] = "true"
os.environ["USE_LOCAL_STORAGE"] = "true"
os.environ["OPENAI_API_KEY"] = ""
os.environ["RUNWAYML_API_SECRET"] = ""
os.environ["CLOUDINARY_CLOUD_NAME"] = ""
os.environ["DEBUG"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

MOCK_ASSETS_DIR = Path(__file__).resolve().parent.parent / "app" / "mock_assets"


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    TEST_DB_PATH.unlink(missing_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    TEST_DB_PATH.unlink(missing_ok=True)
    shutil.rmtree(TEST_STORAGE_ROOT, ignore_errors=True)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def product_image_bytes() -> bytes:
    return (MOCK_ASSETS_DIR / "placeholder_image.png").read_bytes()


def create_and_generate_campaign(client: TestClient, product_image_bytes: bytes, **overrides) -> dict:
    """Test helper: creates a campaign and runs generation to completion
    (mock providers + synchronous BackgroundTasks make this a single call)."""
    fields = {
        "productName": "Aurora Bottle",
        "productDescription": "A sleek insulated water bottle for athletes",
        "targetAudience": "Runners and gym-goers",
        "tone": "energetic",
        "price": "$29",
        "websiteUrl": "https://aurora.example.com",
    }
    fields.update(overrides)

    response = client.post(
        "/api/campaigns",
        files={"productImage": ("product.png", product_image_bytes, "image/png")},
        data=fields,
    )
    assert response.status_code == 201, response.text
    campaign = response.json()

    response = client.post(f"/api/campaigns/{campaign['id']}/generate")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/campaigns/{campaign['id']}")
    assert response.status_code == 200
    return response.json()
