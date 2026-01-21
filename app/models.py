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


class PrimaryIssue(BaseModel):
    """Primary issue model."""
    class_en: str = Field(..., description="Class ที่ตรวจพบ (ภาษาอังกฤษ)")
    description: str = Field(..., description="คำอธิบายลักษณะอาการโดยสรุป (1–2 ประโยค)")


class VisualEvidence(BaseModel):
    """Structured visual evidence from image."""
    spots_description: str = Field(..., description="ลักษณะของจุดหรือแผลบนใบ (สี, ขอบเขต, ความคมชัด)")
    lesion_shape: str = Field(..., description="รูปทรงของแผล (เช่น กลม, รี, รูปตา, ไม่สม่ำเสมอ)")
    distribution: str = Field(..., description="การกระจายตัวของอาการบนใบ (กระจาย / รวมกลุ่ม / เฉพาะปลายใบ)")
    severity_observation: str = Field(..., description="ระดับความรุนแรงของอาการบนใบข้าว")


class DiseaseManagement(BaseModel):
    """Disease management recommendations."""
    cultural_management: list[str] = Field(..., description="การจัดการเชิงเกษตร")
    cultivar_and_cropping_system: list[str] = Field(..., description="การจัดการด้านพันธุ์และระบบปลูก")
    monitoring_and_prevention: list[str] = Field(..., description="การเฝ้าระวังและป้องกัน")
    chemical_management: list[str] = Field(..., description="การจัดการด้วยสารเคมี (หากจำเป็น)")


class DiagnosisSummary(BaseModel):
    """Diagnosis summary model."""
    final_class: str = Field(..., description="Class สุดท้าย")
    severity: str = Field(..., description="ระดับความรุนแรง")
    overall_confidence: str = Field(..., description="ความมั่นใจโดยรวม")


class DiagnosisResult(BaseModel):
    """Complete diagnosis result from Gemini AI (Updated v2)."""
    confidence_level: int = Field(..., ge=0, le=100, description="ระดับความมั่นใจ (XX)")
    primary_issue: PrimaryIssue = Field(..., description="อาการหลัก")
    causal_agent: str = Field(..., description="กลุ่มสาเหตุของโรค (Causal Agent)")
    visual_evidence: VisualEvidence = Field(..., description="หลักฐานทางอาการจากภาพ")
    diagnostic_reasoning: str = Field(..., description="เหตุผลในการจัดอยู่ใน Class นี้")
    disease_management: DiseaseManagement = Field(..., description="แนวทางการจัดการโรค")
    summary: DiagnosisSummary = Field(..., description="สรุปผล")

    model_config = {
        "json_schema_extra": {
            "example": {
                "confidence_level": 85,
                "primary_issue": {
                    "class_en": "rice_blast",
                    "description": "พบแผลรูปตาสีน้ำตาลขอบเหลืองกระจายอยู่ทั่วไปบนใบข้าว"
                },
                "causal_agent": "Fungal disease (Magnaporthe oryzae)",
                "visual_evidence": {
                    "spots_description": "แผลแบบจุดหยดน้ำ สีเทากลาง มีขอบสีน้ำตาลเข้ม",
                    "lesion_shape": "รูปตา หรือรูปข้าวหลามตัด",
                    "distribution": "กระจายตัวสม่ำเสมอทั่วทั้งใบ",
                    "severity_observation": "พบแผลลามประมาณ 20-30% ของพื้นที่ใบ"
                },
                "diagnostic_reasoning": "เนื่องจากลักษณะแผลเป็นรูปตาที่ชัดเจนและมีสีเทากลาง ซึ่งเป็นเอกลักษณ์ของ Rice Blast ต่างจาก Brown Spot ที่ปกติแผลจะกลมกว่า",
                "disease_management": {
                    "cultural_management": ["ลดการใส่ปุ๋ยไนโตรเจนส่วนเกิน", "งดให้น้ำแบบสปริงเกอร์ในช่วงเย็น"],
                    "cultivar_and_cropping_system": ["ใช้พันธุ์ต้านทาน เช่น กข57", "เว้นระยะปลูกให้ระบายอากาศดี"],
                    "monitoring_and_prevention": ["สำรวจแปลงทุก 3 วัน", "เฝ้าระวังเป็นพิเศษในช่วงอากาศชื้น"],
                    "chemical_management": ["พ่นสารป้องกันกำจัดเชื้อรา เช่น ไซโปรโคนาโซล หรือ อะซอกซีสโตรบิน ตามอัตราแนะนำ"]
                },
                "summary": {
                    "final_class": "rice_blast",
                    "severity": "ปานกลาง",
                    "overall_confidence": "85%"
                }
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
