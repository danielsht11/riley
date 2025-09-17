from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

class BusinessActivityAreas(Base):
    __tablename__ = "business_activity_areas"
    id = Column(Integer, primary_key=True, index=True)
    activity_area = Column(String, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    business = relationship("Business", back_populates="activity_areas")