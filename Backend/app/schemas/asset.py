from app.schemas.common import CamelModel


class OverlayUpdateRequest(CamelModel):
    headline: str | None = None
    product_name: str | None = None
    price: str | None = None
    website: str | None = None
    call_to_action: str | None = None
    fade_in: bool = True
    fade_out: bool = True


class DownloadResponse(CamelModel):
    url: str
    file_name: str
