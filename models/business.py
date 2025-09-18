from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

"""
id = fields.Int(required=True)
owner_id = fields.Int(required=True)
name = fields.Str(required=True)
scope = fields.Str(required=True)
hours = fields.Str(required=True)
callout_phone = fields.Str(required=True)
"""
class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), index=True, nullable=False)
    email = Column(String)
    scope = Column(String, index=True)
    hours = Column(String)
    callout_phone = Column(String)
    webpage_url = Column(String)
    description = Column(String)
    tagline = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    owner_id = Column(Integer, ForeignKey("owners.id", ondelete="CASCADE"), index=True, nullable=False)
    owner = relationship("Owner", back_populates="businesses")
    services = relationship("BusinessServices", back_populates="business", cascade="all, delete-orphan")
    activity_areas = relationship("BusinessActivityAreas", back_populates="business", cascade="all, delete-orphan")
