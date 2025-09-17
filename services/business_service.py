from sqlalchemy.orm import Session
from crud import crud_business


class BusinessService:
    @staticmethod
    def get_business(db: Session, callout_phone: str):
        return crud_business.get_business(db, callout_phone)