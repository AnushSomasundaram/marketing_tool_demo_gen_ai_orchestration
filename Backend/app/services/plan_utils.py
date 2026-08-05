import json

from app.models.campaign import Campaign
from app.schemas.plan import CampaignPlan


def load_campaign_plan(campaign: Campaign) -> CampaignPlan | None:
    if not campaign.plan_json:
        return None
    return CampaignPlan.model_validate(json.loads(campaign.plan_json))
