from typing import Optional
from datetime import datetime
from pydantic import BaseModel
class BusinessBase(BaseModel):
    name: str
    scope: Optional[str] = None
    hours: Optional[str] = None
    callout_phone: Optional[str] = None
    webpage_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    activiry_area: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
class BusinessCreate(BusinessBase):
    pass
class Business(BusinessBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True