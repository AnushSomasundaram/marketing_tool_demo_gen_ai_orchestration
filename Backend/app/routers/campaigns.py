from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_db, get_owned_campaign
from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.schemas.campaign import CampaignOut, CampaignSummaryOut, GenerationJobOut
from app.schemas.chat import ChatRequest, ChatTurnResponse
from app.services import campaign_service, chat_service, generation_service, job_service
from app.services.serializers import serialize_campaign, serialize_job
from app.utils.files import validate_and_read_image

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

VALID_SCOPES = {"campaign", "selected_asset", "caption_only", "visual_only"}


@router.post("", response_model=CampaignOut, status_code=201)
async def create_campaign(
    productImage: UploadFile,  # noqa: N803 - matches the frontend's multipart field name
    productName: str = Form(...),  # noqa: N803
    productDescription: str = Form(...),  # noqa: N803
    targetAudience: str | None = Form(None),  # noqa: N803
    tone: str = Form("professional"),
    price: str | None = Form(None),
    websiteUrl: str | None = Form(None),  # noqa: N803
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CampaignOut:
    image_bytes = await validate_and_read_image(productImage, max_bytes=settings.max_upload_bytes)
    campaign = await campaign_service.create_campaign(
        db,
        product_name=productName,
        product_description=productDescription,
        target_audience=targetAudience,
        tone=tone,
        price=price,
        website_url=websiteUrl,
        image_bytes=image_bytes,
        image_content_type=productImage.content_type or "image/png",
    )
    return serialize_campaign(db, campaign)


@router.get("", response_model=list[CampaignSummaryOut])
def list_campaigns(db: Session = Depends(get_db)) -> list[CampaignSummaryOut]:
    campaigns = campaign_service.list_campaigns(db)
    return [CampaignSummaryOut.model_validate(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign: Campaign = Depends(get_owned_campaign), db: Session = Depends(get_db)
) -> CampaignOut:
    return serialize_campaign(db, campaign)


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign: Campaign = Depends(get_owned_campaign), db: Session = Depends(get_db)) -> None:
    campaign_service.delete_campaign(db, campaign)


@router.post("/{campaign_id}/generate", response_model=CampaignOut, status_code=202)
def generate_campaign(
    background_tasks: BackgroundTasks,
    campaign: Campaign = Depends(get_owned_campaign),
    db: Session = Depends(get_db),
) -> CampaignOut:
    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.FAILED):
        raise HTTPException(status_code=409, detail=f"Campaign is already {campaign.status}.")
    background_tasks.add_task(generation_service.run_campaign_generation, campaign.id)
    return serialize_campaign(db, campaign)


@router.post("/{campaign_id}/regenerate", response_model=CampaignOut, status_code=202)
def regenerate_campaign(
    background_tasks: BackgroundTasks,
    campaign: Campaign = Depends(get_owned_campaign),
    db: Session = Depends(get_db),
) -> CampaignOut:
    background_tasks.add_task(generation_service.regenerate_all_images, campaign.id)
    background_tasks.add_task(generation_service.regenerate_video, campaign.id)
    campaign.status = CampaignStatus.GENERATING
    db.commit()
    return serialize_campaign(db, campaign)


@router.get("/{campaign_id}/jobs", response_model=list[GenerationJobOut])
def list_jobs(
    campaign: Campaign = Depends(get_owned_campaign), db: Session = Depends(get_db)
) -> list[GenerationJobOut]:
    jobs = job_service.list_jobs(db, campaign.id)
    return [serialize_job(j) for j in jobs]


@router.post("/{campaign_id}/chat", response_model=ChatTurnResponse)
async def campaign_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    campaign: Campaign = Depends(get_owned_campaign),
    db: Session = Depends(get_db),
) -> ChatTurnResponse:
    if request.scope not in VALID_SCOPES:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {request.scope}")

    assistant_message, actions = await chat_service.handle_chat_turn(
        db,
        campaign,
        message=request.message,
        scope=request.scope,
        selected_asset_id=request.selected_asset_id,
        background_tasks=background_tasks,
    )
    campaign_out = serialize_campaign(db, campaign)
    return ChatTurnResponse(
        id=assistant_message.id,
        role=assistant_message.role,
        content=assistant_message.content,
        created_at=assistant_message.created_at,
        assistant_message=assistant_message.content,
        actions=actions,
        campaign=campaign_out,
    )
