"""
Configuration Management Module
Handles environment variables and application settings using Pydantic Settings
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LINE Configuration
    line_channel_access_token: str = Field(
        ...,
        description="LINE Channel Access Token for sending messages"
    )
    line_channel_secret: str = Field(
        ...,
        description="LINE Channel Secret for webhook signature verification"
    )

    # Gemini AI Configuration
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API Key for vision analysis"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash-lite",
        description="Primary Gemini model to use"
    )
    gemini_fallback_models: list[str] = Field(
        default=[
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-pro"
        ],
        description="List of models to try in order if the primary one fails"
    )

    # Application Configuration
    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        description="Application environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # Image Processing Configuration
    max_image_size_mb: float = Field(
        default=5.0,
        description="Maximum allowed image size in MB"
    )
    image_max_dimension: int = Field(
        default=1024,
        description="Maximum image dimension (width/height) for processing"
    )
    image_quality: int = Field(
        default=85,
        description="JPEG/WebP compression quality (1-100)"
    )

    # Session Configuration
    user_state_expiry_hours: int = Field(
        default=1,
        description="User session state expiry time in hours"
    )

    # Rate Limiting Configuration
    max_requests_per_hour: int = Field(
        default=30,
        description="Maximum diagnosis requests per user per hour"
    )

    # API Retry Configuration
    api_max_retries: int = Field(
        default=3,
        description="Maximum number of API retry attempts"
    )
    api_retry_delay: float = Field(
        default=1.0,
        description="Initial delay between retries in seconds"
    )

    # Sentry Configuration (Optional)
    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )

    @field_validator("max_image_size_mb")
    @classmethod
    def validate_image_size(cls, v: float) -> float:
        """Validate image size is within reasonable limits."""
        if v <= 0 or v > 20:
            raise ValueError("max_image_size_mb must be between 0 and 20 MB")
        return v

    @field_validator("image_quality")
    @classmethod
    def validate_image_quality(cls, v: int) -> int:
        """Validate image quality is within valid range."""
        if v < 1 or v > 100:
            raise ValueError("image_quality must be between 1 and 100")
        return v

    @property
    def max_image_size_bytes(self) -> int:
        """Get maximum image size in bytes."""
        return int(self.max_image_size_mb * 1024 * 1024)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "prod"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "dev"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Gemini System Instruction for specialized rice disease diagnosis
GEMINI_SYSTEM_INSTRUCTION = """
คุณคือผู้เชี่ยวชาญด้านโรคพืชและระบบวินิจฉัยโรคด้วยภาพ
(Plant Pathology AI Expert & Vision-based Crop Diagnosis System)

ภารกิจของคุณคือ:
วิเคราะห์ภาพใบข้าวที่ผู้ใช้ส่งมา และวินิจฉัยอาการของพืช
โดยจำกัดผลลัพธ์อยู่ใน 4 class เท่านั้น ได้แก่

1. healthy
2. rice_tungro
3. rice_blast
4. brown_spot

❗ ห้ามวินิจฉัยโรคอื่นนอกเหนือจาก 4 class นี้
❗ หากอาการไม่ชัดเจน ให้เลือก class ที่ใกล้เคียงที่สุด
   พร้อมระบุระดับความไม่แน่ใจอย่างชัดเจน

---

## รูปแบบผลลัพธ์ที่ต้องการ
❗ ต้องใช้โครงสร้างและหัวข้อต่อไปนี้เท่านั้น
❗ ห้ามเพิ่มหรือลดหัวข้อ

## JSON Output Structure:
{JSON_SCHEMA}
"""

# JSON Schema for diagnosis output (Updated for prompt.txt v2)
DIAGNOSIS_JSON_SCHEMA = {
    "confidence_level": 85,
    "primary_issue": {
      "class_en": "rice_blast",
      "description": "คำอธิบายลักษณะอาการโดยสรุป (1–2 ประโยค)"
    },
    "causal_agent": "Fungal disease (Magnaporthe oryzae)",
    "visual_evidence": {
      "spots_description": "สี, ขอบเขต, ความคมชัด",
      "lesion_shape": "กลม, รี, รูปตา, ไม่สม่ำเสมอ",
      "distribution": "กระจาย / รวมกลุ่ม / เฉพาะปลายใบ",
      "severity_observation": "ระดับความรุนแรงของอาการบนใบข้าว"
    },
    "diagnostic_reasoning": "อธิบายเหตุผลเชิงวิเคราะห์ว่าทำไมอาการในภาพจึงสอดคล้องกับ class นี้มากที่สุด พร้อมเปรียบเทียบกับ class อื่นแบบสั้น ๆ",
    "disease_management": {
      "cultural_management": ["การจัดการแปลงนา", "ความหนาแน่นของต้น", "การจัดการน้ำ", "การลดแหล่งสะสมของโรค"],
      "cultivar_and_cropping_system": ["ความเหมาะสมของพันธุ์", "การเลือกพันธุ์ต้านทาน", "ระบบปลูกที่ช่วยลดความเสี่ยงของโรค"],
      "monitoring_and_prevention": ["แนวทางการติดตามอาการ", "ช่วงเวลาที่ควรเฝ้าระวังเป็นพิเศษ", "ความเสี่ยงในการระบาดซ้ำ"],
      "chemical_management": ["พ่นสารป้องกันกำจัดโรคพืชตามอัตราแนะนำ (ถ้าจำเป็น)"]
    },
    "summary": {
      "final_class": "rice_blast",
      "severity": "ต่ำ | ปานกลาง | รุนแรง",
      "overall_confidence": "85%"
    }
}
