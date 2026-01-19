"""
Pydantic Models Module
Data validation and serialization models for the application
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PathogenType(str, Enum):
    """Types of pathogens that can cause plant diseases."""
    FUNGUS = "เชื้อรา"
    VIRUS = "ไวรัส"
    BACTERIA = "แบคทีเรีย"
    PEST = "ศัตรูพืช"
    NUTRIENT = "ปัญหาสารอาหาร"
    UNKNOWN = "ไม่ทราบสาเหตุ"


class Severity(str, Enum):
    """Severity levels for plant diseases."""
    MILD = "เล็กน้อย"
    MODERATE = "ปานกลาง"
    SEVERE = "รุนแรง"


class PlantType(str, Enum):
    """Supported plant types for diagnosis."""
    RICE = "ข้าว"
    CORN = "ข้าวโพด"
    CASSAVA = "มันสำปะหลัง"
    SUGARCANE = "อ้อย"
    VEGETABLE = "พืชผัก"
    FRUIT = "ไม้ผล"
    OTHER = "อื่นๆ"


class PlantPart(str, Enum):
    """Plant parts that can be affected by disease."""
    LEAF = "ใบ"
    STEM = "ลำต้น"
    ROOT = "ราก"
    SHEATH = "กาบใบ"
    OTHER = "อื่นๆ"


class UserState(str, Enum):
    """User conversation states."""
    IDLE = "idle"
    WAITING_FOR_IMAGE = "waiting_for_image"
    WAITING_FOR_PLANT_TYPE = "waiting_for_plant_type"
    WAITING_FOR_PLANT_PART = "waiting_for_plant_part"
    PROCESSING = "processing"
    COMPLETED = "completed"


class ChemicalControl(BaseModel):
    """Chemical control recommendation model."""
    product_name: str = Field(..., description="ชื่อสารเคมี")
    active_ingredient: str = Field(..., description="สารออกฤทธิ์")
    dosage: str = Field(..., description="อัตราการใช้")
    application_method: str = Field(..., description="วิธีใช้")
    precautions: str = Field(..., description="ข้อควรระวัง")


class DiseaseCharacteristics(BaseModel):
    """Disease characteristics model."""
    appearance: str = Field(..., description="ลักษณะการปรากฏ")
    occurrence: str = Field(..., description="สาเหตุและสภาวะที่เกิด")
    spread_pattern: str = Field(..., description="รูปแบบการแพร่กระจาย")
    severity: Severity = Field(..., description="ระดับความรุนแรง")


class Treatment(BaseModel):
    """Treatment recommendations model."""
    immediate_action: list[str] = Field(
        default_factory=list,
        description="การดำเนินการเร่งด่วน"
    )
    chemical_control: list[ChemicalControl] = Field(
        default_factory=list,
        description="วิธีควบคุมด้วยสารเคมี"
    )
    organic_control: list[str] = Field(
        default_factory=list,
        description="วิธีควบคุมแบบอินทรีย์"
    )
    cultural_practices: list[str] = Field(
        default_factory=list,
        description="วิธีการจัดการแปลง"
    )


class DiagnosisResult(BaseModel):
    """Complete diagnosis result from Gemini AI."""
    disease_name_th: str = Field(..., description="ชื่อโรคภาษาไทย")
    disease_name_en: str = Field(..., description="ชื่อโรคภาษาอังกฤษ")
    pathogen_type: str = Field(..., description="ประเภทของเชื้อก่อโรค")
    confidence_level: int = Field(
        ...,
        ge=0,
        le=100,
        description="ระดับความมั่นใจ (0-100%)"
    )
    symptoms_observed: list[str] = Field(
        default_factory=list,
        description="อาการที่พบ"
    )
    disease_characteristics: DiseaseCharacteristics = Field(
        ...,
        description="ลักษณะของโรค"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="คำแนะนำทั่วไป"
    )
    prevention_methods: list[str] = Field(
        default_factory=list,
        description="วิธีป้องกัน"
    )
    treatment: Treatment = Field(..., description="วิธีการรักษา")
    additional_notes: str | None = Field(
        default=None,
        description="ข้อมูลเพิ่มเติม"
    )
    followup_needed: bool = Field(
        default=False,
        description="ต้องติดตามผลหรือไม่"
    )
    expert_consultation: str | None = Field(
        default=None,
        description="คำแนะนำในการปรึกษาผู้เชี่ยวชาญ"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "disease_name_th": "โรคไหม้",
                "disease_name_en": "Rice Blast",
                "pathogen_type": "เชื้อรา",
                "confidence_level": 85,
                "symptoms_observed": [
                    "จุดสีน้ำตาลรูปตาบนใบ",
                    "ขอบแผลสีเหลือง"
                ],
                "disease_characteristics": {
                    "appearance": "จุดรูปตาสีน้ำตาล ขอบเหลือง",
                    "occurrence": "อากาศชื้นสูง อุณหภูมิ 25-28°C",
                    "spread_pattern": "แพร่ทางลม สปอร์",
                    "severity": "ปานกลาง"
                },
                "recommendations": [
                    "หยุดให้น้ำเพิ่มความชื้น",
                    "ตัดใบที่เป็นโรคทิ้ง"
                ],
                "prevention_methods": [
                    "ใช้พันธุ์ต้านทาน",
                    "ไม่ใส่ปุ๋ยไนโตรเจนเกิน"
                ],
                "treatment": {
                    "immediate_action": ["ตัดใบที่เป็นโรค"],
                    "chemical_control": [
                        {
                            "product_name": "ไตรไซคลาโซล",
                            "active_ingredient": "Tricyclazole 75% WP",
                            "dosage": "20 กรัม/น้ำ 20 ลิตร",
                            "application_method": "พ่นทางใบ",
                            "precautions": "ห้ามพ่นก่อนเก็บเกี่ยว 21 วัน"
                        }
                    ],
                    "organic_control": ["ใช้เชื้อ Trichoderma"],
                    "cultural_practices": ["ปรับระยะปลูกให้โปร่ง"]
                },
                "additional_notes": "หากอาการรุนแรงควรปรึกษาเกษตรอำเภอ",
                "followup_needed": True,
                "expert_consultation": "แนะนำติดต่อศูนย์วิจัยข้าว"
            }
        }
    }


class UserInfo(BaseModel):
    """User information collected for diagnosis."""
    plant_type: PlantType | None = Field(
        default=None,
        description="ชนิดพืช"
    )
    plant_part: PlantPart | None = Field(
        default=None,
        description="จุดที่พบอาการ/ส่วนของพืช"
    )
    additional_info: str | None = Field(
        default=None,
        description="ข้อมูลเพิ่มเติมจากผู้ใช้"
    )


class UserSession(BaseModel):
    """User session data stored in Redis."""
    user_id: str = Field(..., description="LINE user ID")
    state: UserState = Field(
        default=UserState.IDLE,
        description="Current conversation state"
    )
    image_data: bytes | None = Field(
        default=None,
        description="Stored image data"
    )
    image_content_type: str | None = Field(
        default=None,
        description="Image MIME type"
    )
    user_info: UserInfo = Field(
        default_factory=UserInfo,
        description="User provided information"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session last update time"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }


class DiagnosisRequest(BaseModel):
    """Request model for diagnosis API."""
    image_base64: str = Field(..., description="Base64 encoded image")
    plant_type: PlantType = Field(..., description="Type of plant")
    plant_part: PlantPart | None = Field(default=None, description="จุดที่พบอาการ")
    additional_info: str | None = Field(
        default=None,
        description="Additional information"
    )


class DiagnosisResponse(BaseModel):
    """Response model for diagnosis API."""
    success: bool = Field(..., description="Whether diagnosis was successful")
    diagnosis: DiagnosisResult | None = Field(
        default=None,
        description="Diagnosis result"
    )
    error: str | None = Field(default=None, description="Error message if any")
    processing_time_ms: int | None = Field(
        default=None,
        description="Processing time in milliseconds"
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current timestamp"
    )
    services: dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Any | None = Field(default=None, description="Additional details")


# Thai error messages for user-friendly responses
ERROR_MESSAGES = {
    "image_too_large": "รูปภาพใหญ่เกินไป กรุณาเลือกรูปที่เล็กกว่า {max_size} MB",
    "invalid_image_format": "รูปภาพไม่ถูกต้อง กรุณาส่งรูปนามสกุล .jpg, .jpeg, .png",
    "api_error": "ระบบขัดข้อง กรุณาลองใหม่อีกครั้งในอีกสักครู่",
    "low_confidence": "ระบบไม่สามารถวินิจฉัยได้แน่ชัด แนะนำให้ส่งรูปที่ชัดเจนกว่า หรือปรึกษาผู้เชี่ยวชาญ",
    "rate_limit_exceeded": "คุณใช้งานเกินจำนวนครั้งที่กำหนด กรุณาลองใหม่ในอีก {minutes} นาที",
    "no_plant_detected": "ไม่พบพืชในภาพ กรุณาถ่ายภาพให้เห็นส่วนที่มีอาการชัดเจน",
    "session_expired": "เซสชั่นหมดอายุ กรุณาส่งรูปภาพใหม่อีกครั้ง",
    "unknown_error": "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง",
}
