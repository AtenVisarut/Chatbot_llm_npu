"""
Pytest Configuration and Fixtures
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment
os.environ["ENVIRONMENT"] = "dev"
os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test_token"
os.environ["LINE_CHANNEL_SECRET"] = "test_secret"
os.environ["GEMINI_API_KEY"] = "test_api_key"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Create test client for FastAPI app."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    """Create async test client."""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_image_data() -> bytes:
    """Generate sample image data for testing."""
    from PIL import Image
    import io

    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_diagnosis_result() -> dict:
    """Sample diagnosis result for testing."""
    return {
        "disease_name_th": "โรคไหม้",
        "disease_name_en": "Rice Blast",
        "pathogen_type": "เชื้อรา",
        "confidence_level": 85,
        "symptoms_observed": ["จุดสีน้ำตาลรูปตา", "ขอบแผลสีเหลือง"],
        "disease_characteristics": {
            "appearance": "จุดรูปตาสีน้ำตาล",
            "occurrence": "อากาศชื้น",
            "spread_pattern": "ทางลม",
            "severity": "ปานกลาง"
        },
        "recommendations": ["ตัดใบที่เป็นโรค"],
        "prevention_methods": ["ใช้พันธุ์ต้านทาน"],
        "treatment": {
            "immediate_action": ["ตัดใบที่เป็นโรค"],
            "chemical_control": [],
            "organic_control": ["ใช้เชื้อ Trichoderma"],
            "cultural_practices": ["ปรับระยะปลูก"]
        },
        "additional_notes": "หากรุนแรงควรปรึกษาผู้เชี่ยวชาญ",
        "followup_needed": True,
        "expert_consultation": "ติดต่อศูนย์วิจัยข้าว"
    }


@pytest.fixture
def mock_line_webhook_body() -> str:
    """Sample LINE webhook body for testing."""
    import json
    return json.dumps({
        "destination": "test_destination",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "สวัสดี"
                },
                "timestamp": 1234567890000,
                "source": {
                    "type": "user",
                    "userId": "test_user_id"
                },
                "replyToken": "test_reply_token"
            }
        ]
    })
