"""
Proposal models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class ProposalStatus(str, enum.Enum):
    """Proposal status enumeration"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Proposal(TenantBase, Base):
    """Proposal model"""
    __tablename__ = "proposals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    
    # Proposal details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Amount
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Status
    status = Column(Enum(ProposalStatus), default=ProposalStatus.DRAFT)
    
    # Validity
    valid_until = Column(DateTime, nullable=True)
    
    # Content
    content = Column(Text, nullable=True)
    template_id = Column(String(100), nullable=True)
    
    # Delivery
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="proposals")
    
    def __repr__(self):
        return f"<Proposal {self.id} - {self.status}>"
