from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

class BusinessServices(Base):
    __tablename__ = "business_services"
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    business = relationship("Business", back_populates="services")