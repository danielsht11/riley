from sqlalchemy.orm import Session
from models.business import Business
from schemas.business import BusinessCreate
def create_business(db: Session, business: BusinessCreate):
    db_business = Business(name=business.name, scope=business.scope, hours=business.hours, callout_phone=business.callout_phone, webpage_url=business.webpage_url)
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business
def get_business(db: Session, callout_phone: str):
    return db.query(Business).filter(Business.callout_phone == callout_phone).first()
def get_all_businesses(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Business).offset(skip).limit(limit).all()
def get_businesses_by_owner_id(db: Session, owner_id: int):
    return db.query(Business).filter(Business.owner_id == owner_id).all()