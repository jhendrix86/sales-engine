"""
Lead models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class LeadStatus(str, enum.Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(str, enum.Enum):
    """Lead source enumeration"""
    MARKETING = "marketing"
    WEBSITE = "website"
    REFERRAL = "referral"
    OUTREACH = "outreach"
    PARTNER = "partner"


class Lead(Base):
    """Lead model"""
    __tablename__ = "leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Contact information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    
    # Lead details
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    source = Column(Enum(LeadSource), nullable=True)
    
    # Value
    estimated_value = Column(Integer, nullable=True)
    actual_value = Column(Integer, nullable=True)
    
    # Pipeline
    pipeline_stage = Column(String(50), default="new")
    
    # CRM integration
    crm_contact_id = Column(String(255), nullable=True)
    crm_deal_id = Column(String(255), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    activities = relationship("Activity", back_populates="lead")
    proposals = relationship("Proposal", back_populates="lead")
    
    def __repr__(self):
        return f"<Lead {self.id} - {self.name} - {self.status}>"
