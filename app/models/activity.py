"""
Activity models
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ActivityType(str, enum.Enum):
    """Activity type enumeration"""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"


class Activity(Base):
    """Activity model"""
    __tablename__ = "activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    
    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Duration
    duration_minutes = Column(Integer, nullable=True)
    
    # Outcome
    outcome = Column(String(255), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    activity_date = Column(DateTime, nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    
    def __repr__(self):
        return f"<Activity {self.activity_type} - {self.subject}>"
