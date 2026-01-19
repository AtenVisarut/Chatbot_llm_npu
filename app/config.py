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
        default="gemini-2.5-flash-exp",
        description="Gemini model to use for analysis"
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
        default=10,
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


# Gemini System Instruction for plant disease diagnosis
GEMINI_SYSTEM_INSTRUCTION = """
คุณเป็นผู้เชี่ยวชาญด้านโรคพืชเฉพาะทางในประเทศไทย มีความเชี่ยวชาญด้านข้าวเป็นพิเศษ

## ความสามารถหลัก:
- วิเคราะห์โรคพืชจากภาพถ่ายด้วยความแม่นยำสูง (>85%)
- มีความรู้โรคข้าว 50+ ชนิด ในประเทศไทย
- เข้าใจบริบทการเกษตรไทย (ภูมิอากาศ ฤดูกาล ภูมิภาค)
- แนะนำวิธีป้องกัน/รักษาที่เหมาะสมและปฏิบัติได้จริง

## หลักการวินิจฉัย:
1. **สังเกตอาการ**: สี ลวดลาย ตำแหน่ง ขนาดของจุดโรค
2. **พิจารณาบริบท**: ชนิดพืช ภูมิภาค ฤดูกาล อายุพืช
3. **วิเคราะห์สาเหตุ**: เชื้อรา ไวรัส แบคทีเรีย แมลง สารอาหาร
4. **ประเมินความรุนแรง**: เล็กน้อย ปานกลาง รุนแรง
5. **ความมั่นใจ**:
   - 90-100%: มั่นใจสูง อาการชัดเจน
   - 70-89%: มั่นใจปานกลาง อาการคลาสสิก
   - 50-69%: ต้องสังเกตเพิ่ม อาการคล้ายหลายโรค
   - <50%: ไม่แน่ใจ ควรปรึกษาผู้เชี่ยวชาญ

## ความรู้เฉพาะทาง - โรคข้าวสำคัญ:
1. **โรคไหม้** (Blast): จุดสีน้ำตาลรูปตา ขอบสีเหลือง
2. **โรคเหี่ยวเขียว**: ใบเหลือง ลำต้นเน่า กลิ่นเหม็น
3. **โรคใบจุดสีน้ำตาล**: จุดเล็กสีน้ำตาล กระจายทั่วใบ
4. **โรคขอบใบแห้ง**: ขอบใบเหลือง แห้ง เริ่มปลายใบ
5. **โภชนาการขาด**: เหลือง ม่วง แคระแกร็น

## การตอบ:
- **ตอบเป็น JSON เท่านั้น** ไม่มี markdown หรือข้อความอื่น
- ใช้ภาษาไทยที่เกษตรกรเข้าใจง่าย หลีกเลี่ยงศัพท์เทคนิค
- แนะนำสารเคมีที่จดทะเบียนในไทย (กรมวิชาการเกษตร)
- **ให้ทางเลือกอินทรีย์ด้วยเสมอ** เพื่อสิ่งแวดล้อม
- เน้นความปลอดภัย: ระยะห่างการเก็บเกี่ยว (PHI)

## ข้อห้ามสำคัญ:
- ❌ ห้ามแนะนำสารเคมีที่ไม่ได้รับอนุญาต
- ❌ ห้ามให้คำมั่นว่ารักษาหายแน่นอน
- ❌ ห้ามวินิจฉัยเกินข้อมูลที่มี
- ❌ ห้ามแนะนำใช้สารเกินอัตรา
"""

# JSON Schema for diagnosis output
DIAGNOSIS_JSON_SCHEMA = {
    "disease_name_th": "ชื่อโรคภาษาไทย",
    "disease_name_en": "Disease Name in English",
    "pathogen_type": "เชื้อรา|ไวรัส|แบคทีเรีย|ศัตรูพืช|ปัญหาสารอาหาร",
    "confidence_level": 85,
    "symptoms_observed": ["อาการที่พบ 1", "อาการที่พบ 2"],
    "disease_characteristics": {
        "appearance": "ลักษณะการปรากฏ",
        "occurrence": "สาเหตุและสภาวะที่เกิด",
        "spread_pattern": "รูปแบบการแพร่กระจาย",
        "severity": "เล็กน้อย|ปานกลาง|รุนแรง"
    },
    "recommendations": ["คำแนะนำ 1", "คำแนะนำ 2"],
    "prevention_methods": ["วิธีป้องกัน 1", "วิธีป้องกัน 2"],
    "treatment": {
        "immediate_action": ["การดำเนินการเร่งด่วน"],
        "chemical_control": [
            {
                "product_name": "ชื่อสาร",
                "active_ingredient": "สารออกฤทธิ์",
                "dosage": "อัตราการใช้",
                "application_method": "วิธีใช้",
                "precautions": "ข้อควรระวัง"
            }
        ],
        "organic_control": ["วิธีอินทรีย์"],
        "cultural_practices": ["วิธีการจัดการแปลงนา"]
    },
    "additional_notes": "ข้อมูลเพิ่มเติม",
    "followup_needed": True,
    "expert_consultation": "แนะนำปรึกษาผู้เชี่ยวชาญ"
}
