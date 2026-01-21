"""
Text Message Templates Module
Plain text templates for LINE messaging
"""

from app.models import DiagnosisResult, Severity

class TextMessageBuilder:
    """
    Builder for plain text messages.
    """

    @staticmethod
    def format_diagnosis_result(result: DiagnosisResult) -> str:
        """
        Format diagnosis result into a specialized 4-class rice disease text block (v2).
        """
        lines = [
            "### 🌾 ผลการวินิจฉัยจากระบบ AI",
            "**(Rice Leaf Disease Diagnosis – 4 Classes)**",
            "",
            "---",
            "",
            "### 📊 ระดับความมั่นใจ (Confidence Level):",
            f"- {result.confidence_level} %",
            "",
            "---",
            "",
            "### 🔬 อาการหลัก (Primary Issue):",
            f"- {result.primary_issue.class_en}",
            f"- {result.primary_issue.description}",
            "",
            "---",
            "",
            "### 🧬 กลุ่มสาเหตุของโรค (Causal Agent):",
            f"- {result.causal_agent}",
            "",
            "---",
            "",
            "### 🔍 หลักฐานทางอาการจากภาพ (Visual Evidence):",
            "จากการวิเคราะห์ภาพ พบลักษณะสำคัญดังนี้:",
            f"- {result.visual_evidence.spots_description}",
            f"- {result.visual_evidence.lesion_shape}",
            f"- {result.visual_evidence.distribution}",
            f"- {result.visual_evidence.severity_observation}",
            "",
            "---",
            "",
            "### 🧠 เหตุผลในการจัดอยู่ใน Class นี้ (Diagnostic Reasoning):",
            f"{result.diagnostic_reasoning}",
            "",
            "---",
            "",
            "### 🛠️ แนวทางการจัดการโรค (Disease Management – Non-Chemical)",
            "",
            "#### 1️⃣ การจัดการเชิงเกษตร (Cultural Management):"
        ]

        for item in result.disease_management.cultural_management:
            lines.append(f"- {item}")

        lines.extend([
            "",
            "#### 2️⃣ การจัดการด้านพันธุ์และระบบปลูก:"
        ])
        for item in result.disease_management.cultivar_and_cropping_system:
            lines.append(f"- {item}")

        lines.extend([
            "",
            "#### 3️⃣ การเฝ้าระวังและป้องกัน:"
        ])
        for item in result.disease_management.monitoring_and_prevention:
            lines.append(f"- {item}")

        lines.extend([
            "",
            "#### 4️⃣ การจัดการด้วยสารเคมี (Chemical Management):"
        ])
        for item in result.disease_management.chemical_management:
            lines.append(f"- {item}")

        lines.extend([
            "",
            "> ❗ เน้นการจัดการเชิงระบบและเชิงป้องกันเป็นหลัก",
            "",
            "---",
            "",
            "### 📝 สรุปผลการวินิจฉัย:",
            f"- Class สุดท้าย: {result.summary.final_class}",
            f"- ระดับความรุนแรงของอาการ: {result.summary.severity}",
            f"- ความมั่นใจโดยรวมของระบบ: {result.summary.overall_confidence}",
            "",
            "---"
        ])
        
        return "\n".join(lines).strip()

    @staticmethod
    def format_error(message: str) -> str:
        """Format error message."""
        return f"⚠️ เกิดข้อผิดพลาด:\n{message}"

    @staticmethod
    def format_welcome() -> str:
        """Format welcome message."""
        return (
            "🌿 ยินดีต้อนรับสู่ระบบวินิจฉัยโรคพืช AI\n\n"
            "ส่งรูปภาพใบหรือส่วนที่เป็นโรคมาให้เราได้เลยครับ 📷\n"
            "ระบบจะทำการวิเคราะห์และให้คำแนะนำทันที!"
        )

    @staticmethod
    def format_processing() -> str:
        """Format processing message."""
        return "⏳ กำลังวิเคราะห์รูปภาพของคุณ กรุณารอสักครู่..."
