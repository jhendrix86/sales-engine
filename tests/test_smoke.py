"""
Sales Engine smoke tests
"""
import pytest


@pytest.mark.asyncio
async def test_pipeline_import():
    """Verify pipeline models import without error"""
    from app.models.pipeline import Deal, PipelineStage
    assert Deal is not None
    assert PipelineStage is not None


@pytest.mark.asyncio
async def test_app_instantiation():
    """Verify FastAPI app instantiates without error"""
    from app.main import app
    assert app is not None
    assert app.title == "Sales Engine"
