from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Campaign Studio API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./campaign_studio.db"
    frontend_origins: str = "http://localhost:5173"
    max_upload_mb: int = 10

    # When set, every /api request (except /api/health) must carry a matching
    # X-Access-Code header. Empty disables the gate — used for local dev.
    access_code: str = ""

    # Base URL this API is reachable at, used to build absolute URLs for
    # locally-stored files (e.g. http://localhost:8000/storage/...).
    public_base_url: str = "http://localhost:8000"

    # OpenAI
    openai_api_key: str = ""
    openai_text_model: str = "gpt-4o-mini"
    openai_image_model: str = "gpt-image-2"

    # Runway
    runwayml_api_secret: str = ""
    runway_video_model: str = "gen4_turbo"
    runway_video_duration_seconds: int = 5
    runway_video_ratio: str = "720:1280"

    # Cloudinary / storage
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    use_local_storage: bool = True

    # Instagram / Meta
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = "http://localhost:8000/api/instagram/callback"
    instagram_api_version: str = "v21.0"
    instagram_demo_mode: bool = True

    # Providers
    use_mock_providers: bool = True

    # FFmpeg
    ffmpeg_binary: str = "ffmpeg"

    @property
    def frontend_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def runway_configured(self) -> bool:
        return bool(self.runwayml_api_secret)

    @property
    def storage_configured(self) -> bool:
        if self.use_local_storage:
            return True
        return bool(self.cloudinary_cloud_name and self.cloudinary_api_key and self.cloudinary_api_secret)

    @property
    def instagram_configured(self) -> bool:
        if self.instagram_demo_mode:
            return False
        return bool(self.meta_app_id and self.meta_app_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
