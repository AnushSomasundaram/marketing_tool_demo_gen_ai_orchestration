from functools import lru_cache

from app.config import get_settings
from app.services.providers.image.base import ImageGenerationProvider
from app.services.providers.social.base import SocialPublisher
from app.services.providers.text.base import TextGenerationProvider
from app.services.providers.video.base import VideoGenerationProvider


@lru_cache
def get_text_provider() -> TextGenerationProvider:
    settings = get_settings()
    if settings.use_mock_providers:
        from app.services.providers.text.mock_text import MockTextProvider

        return MockTextProvider()

    from app.services.providers.text.openai_text import OpenAITextProvider

    return OpenAITextProvider()


@lru_cache
def get_image_provider() -> ImageGenerationProvider:
    settings = get_settings()
    if settings.use_mock_providers:
        from app.services.providers.image.mock_image import MockImageProvider

        return MockImageProvider()

    from app.services.providers.image.openai_image import OpenAIImageProvider

    return OpenAIImageProvider()


@lru_cache
def get_video_provider() -> VideoGenerationProvider:
    settings = get_settings()
    if settings.use_mock_providers:
        from app.services.providers.video.mock_video import MockVideoProvider

        return MockVideoProvider()

    from app.services.providers.video.runway_video import RunwayVideoProvider

    return RunwayVideoProvider()


@lru_cache
def get_social_publisher() -> SocialPublisher:
    settings = get_settings()
    if settings.instagram_demo_mode:
        from app.services.providers.social.instagram_demo import DemoInstagramPublisher

        return DemoInstagramPublisher()

    from app.services.providers.social.instagram_graph import InstagramGraphPublisher

    return InstagramGraphPublisher()
