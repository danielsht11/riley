from sqlalchemy.orm import Session
from crud import crud_owner


class OwnerService:
    @staticmethod
    def get_owner(db: Session, owner_id: int):
        return crud_owner.get_owner(db, owner_id)