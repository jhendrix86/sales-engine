"""
Pipeline models
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class PipelineStage(Base):
    """Pipeline stage model"""
    __tablename__ = "pipeline_stages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Stage details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    order = Column(Integer, nullable=False)
    
    # Probability
    win_probability = Column(Integer, default=0)  # percentage
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PipelineStage {self.name} - {self.win_probability}%>"


class Deal(Base):
    """Deal model"""
    __tablename__ = "deals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    
    # Deal details
    name = Column(String(500), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Pipeline
    stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=True)
    expected_close_date = Column(DateTime, nullable=True)
    
    # Status
    is_won = Column(Boolean, default=False)
    is_lost = Column(Boolean, default=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    lead = relationship("Lead")
    stage = relationship("PipelineStage")
    
    def __repr__(self):
        return f"<Deal {self.name} - {self.amount} {self.currency}>"
