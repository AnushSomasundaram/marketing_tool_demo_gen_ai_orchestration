from enum import StrEnum


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    PLANNING = "planning"
    GENERATING = "generating"
    READY = "ready"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"
    PUBLISHING = "publishing"
    PUBLISHED = "published"


class AssetType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class AssetStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class GenerationJobType(StrEnum):
    CAMPAIGN_PLAN = "campaign_plan"
    CAPTION = "caption"
    IMAGE = "image"
    VIDEO = "video"
    VIDEO_COMPOSITION = "video_composition"


class GenerationJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class PublishJobStatus(StrEnum):
    QUEUED = "queued"
    CONTAINER_CREATED = "container_created"
    PROCESSING = "processing"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatActionType(StrEnum):
    REVISE_CAMPAIGN_PLAN = "revise_campaign_plan"
    REGENERATE_ALL_IMAGES = "regenerate_all_images"
    REGENERATE_VIDEO = "regenerate_video"
    REVISE_IMAGE = "revise_image"
    REVISE_VIDEO = "revise_video"
    REVISE_CAPTION = "revise_caption"
    GENERATE_CAPTION_ALTERNATIVE = "generate_caption_alternative"
    UPDATE_VIDEO_OVERLAYS = "update_video_overlays"
    NO_ACTION = "no_action"
    REQUEST_CLARIFICATION = "request_clarification"
