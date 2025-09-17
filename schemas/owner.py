from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
class OwnerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
class OwnerCreate(OwnerBase):
    pass
class Owner(OwnerBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True