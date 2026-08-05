from app.schemas.common import CamelModel


class HealthResponse(CamelModel):
    status: str
    database: bool
    ffmpeg: bool
    openai_configured: bool
    runway_configured: bool
    storage_configured: bool
    instagram_configured: bool
