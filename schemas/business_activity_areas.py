from pydantic import BaseModel

class BusinessActivityAreas(BaseModel):
    id: int
    activity_area: str