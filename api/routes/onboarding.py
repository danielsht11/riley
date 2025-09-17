from pydantic import BaseModel
from fastapi import APIRouter
from models import Business, owner
from services import open_ai_service

PREFIX = "/onboarding"
router = APIRouter(prefix=PREFIX, tags=["onboarding"])


class BusinessRequest(BaseModel):
    business_name: str
    business_scope: str
    business_hours: str
    business_callout_phone: str
    business_webpage_url: str
    owner_name: str
    owner_email: str


@router.post("/business")
async def create_business(payload: BusinessRequest):
    business = Business(
        name=payload.business_name,
        scope=payload.business_scope,
        hours=payload.business_hours,
        callout_phone=payload.business_callout_phone,
        webpage_url=payload.business_webpage_url
    )
    owner = owner(name=payload.owner_name, email=payload.owner_email)
    business.description = open_ai_service.generate_business_description(business, owner)
    return {"message": "Business created", "description": business.description}
