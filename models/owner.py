from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from db.database import Base
class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), index=True, nullable=False)
    email = Column(String, index=True)
    phone = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    # When an Owner is deleted, delete related Business rows as well
    businesses = relationship(
        "Business",
        back_populates="owner",
        cascade="all, delete",
        passive_deletes=True,
    )