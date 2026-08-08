"""
Configuration management for Sales Engine
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/sales")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # CRM Integrations
    hubspot_api_key: str = os.getenv("HUBSPOT_API_KEY", "")
    salesforce_api_key: str = os.getenv("SALESFORCE_API_KEY", "")
    pipedrive_api_key: str = os.getenv("PIPEDRIVE_API_KEY", "")
    
    # Application
    app_name: str = "Sales Engine"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    marketing_automation_url: str = os.getenv("MARKETING_AUTOMATION_URL", "http://localhost:8039")
    revenue_operations_url: str = os.getenv("REVENUE_OPERATIONS_URL", "http://localhost:8036")
    analytics_engine_url: str = os.getenv("ANALYTICS_ENGINE_URL", "http://localhost:8042")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # tolerate env vars owned by other libs (e.g. unkey-auth's UNKEY_*)


settings = Settings()
