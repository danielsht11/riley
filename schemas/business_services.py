from pydantic import BaseModel

class BusinessServices(BaseModel):
    id: int
    service: str