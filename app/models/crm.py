"""
CRM integration models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.models.tenant_base import TenantBase


class CRMIntegration(TenantBase, Base):
    """CRM integration model"""
    __tablename__ = "crm_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # CRM details
    crm_type = Column(String(50), nullable=False)  # hubspot, salesforce, pipedrive
    crm_name = Column(String(100), nullable=False)
    
    # Configuration
    api_key = Column(String(255), nullable=True)
    api_url = Column(String(255), nullable=True)
    
    # Sync status
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="active")  # active, error, paused
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CRMIntegration {self.crm_type} - {self.sync_status}>"


class CRMContact(Base):
    """CRM contact sync model"""
    __tablename__ = "crm_contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    crm_integration_id = Column(UUID(as_uuid=True), ForeignKey("crm_integrations.id"), nullable=False)
    
    # CRM details
    crm_contact_id = Column(String(255), nullable=False)
    crm_contact_url = Column(String(500), nullable=True)
    
    # Sync status
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="synced")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead")
    crm_integration = relationship("CRMIntegration")
    
    def __repr__(self):
        return f"<CRMContact {self.crm_contact_id}>"
