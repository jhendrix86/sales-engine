"""
CRM integration models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class CRMType(str, enum.Enum):
    """CRM provider enumeration - matches the real clients in app/services/crm_client.py"""
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    PIPEDRIVE = "pipedrive"


class CRMSyncStatus(str, enum.Enum):
    """CRM integration sync status enumeration"""
    ACTIVE = "active"
    ERROR = "error"
    PAUSED = "paused"


class CRMContactSyncStatus(str, enum.Enum):
    """Individual contact sync status enumeration"""
    SYNCED = "synced"
    PENDING = "pending"
    ERROR = "error"


class CRMIntegration(TenantBase, Base):
    """CRM integration model"""
    __tablename__ = "crm_integrations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # CRM details
    crm_type = Column(Enum(CRMType), nullable=False)
    crm_name = Column(String(100), nullable=False)

    # Configuration
    api_key = Column(String(255), nullable=True)
    api_url = Column(String(255), nullable=True)

    # Sync status
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(Enum(CRMSyncStatus), default=CRMSyncStatus.ACTIVE)
    last_error = Column(String(500), nullable=True)

    # Metadata
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CRMIntegration {self.crm_type} - {self.sync_status}>"


class CRMContact(TenantBase, Base):
    """CRM contact sync model"""
    __tablename__ = "crm_contacts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(Uuid(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    crm_integration_id = Column(Uuid(as_uuid=True), ForeignKey("crm_integrations.id"), nullable=False)

    # CRM details
    crm_contact_id = Column(String(255), nullable=False)
    crm_contact_url = Column(String(500), nullable=True)

    # Sync status
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(Enum(CRMContactSyncStatus), default=CRMContactSyncStatus.SYNCED)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead")
    crm_integration = relationship("CRMIntegration")

    def __repr__(self):
        return f"<CRMContact {self.crm_contact_id}>"
