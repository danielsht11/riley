from sqlalchemy.orm import Session
from models.owner import Owner
from schemas.owner import OwnerCreate
def create_owner(db: Session, owner: OwnerCreate):
    db_owner = Owner(name=owner.name, email=owner.email, phone=owner.phone, status=owner.status)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner
def get_owner(db: Session, owner_id: int):
    return db.query(Owner).filter(Owner.id == owner_id).first()
def get_all_owners(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Owner).offset(skip).limit(limit).all()
def get_owner_by_phone(db: Session, phone: str):
    return db.query(Owner).filter(Owner.phone == phone).first()
