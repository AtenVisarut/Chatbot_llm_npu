"""
LINE Flex Message Templates Module
Templates for rich LINE messaging
"""

from typing import Any

from linebot.v3.messaging import (
    FlexBox,
    FlexBubble,
    FlexButton,
    FlexIcon,
    FlexImage,
    FlexMessage,
    FlexSeparator,
    FlexText,
    MessageAction,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
    URIAction,
)

from app.models import DiagnosisResult, PlantPart, PlantType, Severity


class FlexMessageBuilder:
    """
    Builder for LINE Flex Messages.

    Creates rich, interactive messages for:
    - Information request
    - Diagnosis results
    - Processing status
    - Error messages
    """

    # Color scheme
    COLORS = {
        "primary": "#1DB446",
        "secondary": "#555555",
        "accent": "#FF6B6B",
        "warning": "#FFA500",
        "success": "#28A745",
        "danger": "#DC3545",
        "info": "#17A2B8",
        "light": "#AAAAAA",
        "dark": "#111111",
        "white": "#FFFFFF",
        "background": "#F5F5F5",
    }

    # Severity colors
    SEVERITY_COLORS = {
        Severity.MILD: "#28A745",
        Severity.MODERATE: "#FFA500",
        Severity.SEVERE: "#DC3545",
    }

    @classmethod
    def create_info_request_message(cls) -> FlexMessage:
        """
        Create information request message after receiving image.

        Returns:
            FlexMessage asking for plant type and location
        """
        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                background_color=cls.COLORS["primary"],
                padding_all="15px",
                contents=[
                    FlexText(
                        text="กรุณาให้ข้อมูลเพิ่มเติม",
                        weight="bold",
                        color=cls.COLORS["white"],
                        size="lg",
                    )
                ],
            ),
            body=FlexBox(
                layout="vertical",
                spacing="md",
                contents=[
                    FlexText(
                        text="เพื่อการวินิจฉัยที่แม่นยำ กรุณาเลือกข้อมูลด้านล่าง",
                        wrap=True,
                        color=cls.COLORS["secondary"],
                        size="sm",
                    ),
                    FlexSeparator(margin="lg"),
                    FlexText(
                        text="ชนิดพืช",
                        weight="bold",
                        size="md",
                        margin="lg",
                    ),
                    FlexBox(
                        layout="horizontal",
                        spacing="sm",
                        margin="md",
                        contents=[
                            cls._create_plant_button(PlantType.RICE),
                            cls._create_plant_button(PlantType.CORN),
                        ],
                    ),
                    FlexBox(
                        layout="horizontal",
                        spacing="sm",
                        margin="sm",
                        contents=[
                            cls._create_plant_button(PlantType.CASSAVA),
                            cls._create_plant_button(PlantType.SUGARCANE),
                        ],
                    ),
                    FlexBox(
                        layout="horizontal",
                        spacing="sm",
                        margin="sm",
                        contents=[
                            cls._create_plant_button(PlantType.VEGETABLE),
                            cls._create_plant_button(PlantType.FRUIT),
                        ],
                    ),
                ],
            ),
            footer=FlexBox(
                layout="vertical",
                spacing="sm",
                contents=[
                    FlexButton(
                        action=PostbackAction(
                            label="อื่นๆ (พิมพ์ระบุ)",
                            data="plant_type=other"
                        ),
                        style="secondary",
                        height="sm",
                    ),
                ],
            ),
        )

        return FlexMessage(alt_text="กรุณาให้ข้อมูลเพิ่มเติม", contents=bubble)

    @classmethod
    def _create_plant_button(cls, plant_type: PlantType) -> FlexButton:
        """Create a plant type selection button."""
        return FlexButton(
            action=PostbackAction(
                label=plant_type.value,
                data=f"plant_type={plant_type.name}"
            ),
            style="primary",
            height="sm",
            flex=1,
        )

    @classmethod
    def create_plant_part_request_message(cls) -> FlexMessage:
        """
        Create plant part selection message.

        Returns:
            FlexMessage asking for affected plant part
        """
        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                background_color=cls.COLORS["info"],
                padding_all="15px",
                contents=[
                    FlexText(
                        text="จุดที่พบอาการ",
                        weight="bold",
                        color=cls.COLORS["white"],
                        size="lg",
                    )
                ],
            ),
            body=FlexBox(
                layout="vertical",
                spacing="md",
                contents=[
                    FlexText(
                        text="การระบุจุดที่พบอาการช่วยให้วินิจฉัยโรคได้แม่นยำขึ้น",
                        wrap=True,
                        color=cls.COLORS["secondary"],
                        size="sm",
                    ),
                    FlexSeparator(margin="lg"),
                    FlexBox(
                        layout="vertical",
                        spacing="sm",
                        margin="md",
                        contents=[
                            cls._create_plant_part_button(PlantPart.LEAF),
                            cls._create_plant_part_button(PlantPart.STEM),
                            cls._create_plant_part_button(PlantPart.ROOT),
                            cls._create_plant_part_button(PlantPart.SHEATH),
                        ],
                    ),
                ],
            ),
            footer=FlexBox(
                layout="vertical",
                spacing="sm",
                contents=[
                    FlexButton(
                        action=PostbackAction(
                            label="ข้ามขั้นตอนนี้",
                            data="plant_part=skip"
                        ),
                        style="secondary",
                        height="sm",
                    ),
                ],
            ),
        )

        return FlexMessage(alt_text="จุดที่พบอาการ", contents=bubble)

    @classmethod
    def _create_plant_part_button(cls, plant_part: PlantPart) -> FlexButton:
        """Create a plant part selection button."""
        return FlexButton(
            action=PostbackAction(
                label=plant_part.value,
                data=f"plant_part={plant_part.name}"
            ),
            style="primary",
            height="sm",
        )

    @classmethod
    def create_processing_message(cls) -> FlexMessage:
        """
        Create processing status message.

        Returns:
            FlexMessage showing processing status
        """
        bubble = FlexBubble(
            body=FlexBox(
                layout="vertical",
                spacing="md",
                padding_all="20px",
                contents=[
                    FlexText(
                        text="กำลังวิเคราะห์...",
                        weight="bold",
                        size="lg",
                        align="center",
                    ),
                    FlexText(
                        text="กรุณารอสักครู่ ระบบกำลังวิเคราะห์รูปภาพของคุณ",
                        wrap=True,
                        color=cls.COLORS["secondary"],
                        size="sm",
                        align="center",
                        margin="md",
                    ),
                    FlexBox(
                        layout="horizontal",
                        justify_content="center",
                        margin="lg",
                        contents=[
                            FlexText(text="⏳", size="xxl"),
                        ],
                    ),
                ],
            ),
        )

        return FlexMessage(alt_text="กำลังวิเคราะห์...", contents=bubble)

    @classmethod
    def create_diagnosis_result_message(
        cls,
        result: DiagnosisResult
    ) -> FlexMessage:
        """
        Create diagnosis result message.

        Args:
            result: Diagnosis result from Gemini

        Returns:
            FlexMessage with diagnosis details
        """
        severity = result.disease_characteristics.severity
        severity_color = cls.SEVERITY_COLORS.get(
            Severity(severity) if isinstance(severity, str) else severity,
            cls.COLORS["info"]
        )

        # Build symptoms text
        symptoms_text = "• " + "\n• ".join(result.symptoms_observed[:3])

        # Build recommendations text
        recommendations_text = "• " + "\n• ".join(result.recommendations[:3])

        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                background_color=cls.COLORS["primary"],
                padding_all="15px",
                contents=[
                    FlexText(
                        text="ผลการวินิจฉัย",
                        weight="bold",
                        color=cls.COLORS["white"],
                        size="md",
                    ),
                    FlexText(
                        text=result.disease_name_th,
                        weight="bold",
                        color=cls.COLORS["white"],
                        size="xl",
                        margin="sm",
                    ),
                    FlexText(
                        text=result.disease_name_en,
                        color=cls.COLORS["white"],
                        size="sm",
                    ),
                ],
            ),
            body=FlexBox(
                layout="vertical",
                spacing="md",
                contents=[
                    # Confidence and severity row
                    FlexBox(
                        layout="horizontal",
                        spacing="md",
                        contents=[
                            FlexBox(
                                layout="vertical",
                                flex=1,
                                contents=[
                                    FlexText(
                                        text="ความมั่นใจ",
                                        size="xs",
                                        color=cls.COLORS["light"],
                                    ),
                                    FlexText(
                                        text=f"{result.confidence_level}%",
                                        weight="bold",
                                        size="lg",
                                        color=cls.COLORS["primary"],
                                    ),
                                ],
                            ),
                            FlexBox(
                                layout="vertical",
                                flex=1,
                                contents=[
                                    FlexText(
                                        text="ความรุนแรง",
                                        size="xs",
                                        color=cls.COLORS["light"],
                                    ),
                                    FlexText(
                                        text=severity if isinstance(severity, str) else severity.value,
                                        weight="bold",
                                        size="lg",
                                        color=severity_color,
                                    ),
                                ],
                            ),
                            FlexBox(
                                layout="vertical",
                                flex=1,
                                contents=[
                                    FlexText(
                                        text="สาเหตุ",
                                        size="xs",
                                        color=cls.COLORS["light"],
                                    ),
                                    FlexText(
                                        text=result.pathogen_type,
                                        weight="bold",
                                        size="md",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    FlexSeparator(),
                    # Symptoms
                    FlexText(
                        text="อาการที่พบ",
                        weight="bold",
                        size="md",
                    ),
                    FlexText(
                        text=symptoms_text,
                        wrap=True,
                        size="sm",
                        color=cls.COLORS["secondary"],
                    ),
                    FlexSeparator(),
                    # Recommendations
                    FlexText(
                        text="คำแนะนำเบื้องต้น",
                        weight="bold",
                        size="md",
                    ),
                    FlexText(
                        text=recommendations_text,
                        wrap=True,
                        size="sm",
                        color=cls.COLORS["secondary"],
                    ),
                ],
            ),
            footer=FlexBox(
                layout="vertical",
                spacing="sm",
                contents=[
                    FlexButton(
                        action=PostbackAction(
                            label="ดูวิธีการรักษา",
                            data=f"show_treatment"
                        ),
                        style="primary",
                        height="sm",
                    ),
                    FlexButton(
                        action=PostbackAction(
                            label="วินิจฉัยใหม่",
                            data="new_diagnosis"
                        ),
                        style="secondary",
                        height="sm",
                    ),
                ],
            ),
        )

        return FlexMessage(
            alt_text=f"ผลวินิจฉัย: {result.disease_name_th}",
            contents=bubble
        )

    @classmethod
    def create_treatment_message(cls, result: DiagnosisResult) -> FlexMessage:
        """
        Create detailed treatment message.

        Args:
            result: Diagnosis result

        Returns:
            FlexMessage with treatment details
        """
        contents = []

        # Immediate actions
        if result.treatment.immediate_action:
            contents.extend([
                FlexText(
                    text="การดำเนินการเร่งด่วน",
                    weight="bold",
                    size="md",
                    color=cls.COLORS["danger"],
                ),
                FlexText(
                    text="• " + "\n• ".join(result.treatment.immediate_action),
                    wrap=True,
                    size="sm",
                    margin="sm",
                ),
                FlexSeparator(margin="md"),
            ])

        # Chemical control
        if result.treatment.chemical_control:
            contents.append(
                FlexText(
                    text="การควบคุมด้วยสารเคมี",
                    weight="bold",
                    size="md",
                    margin="md",
                )
            )
            for chem in result.treatment.chemical_control[:2]:
                contents.extend([
                    FlexText(
                        text=f"💊 {chem.product_name}",
                        weight="bold",
                        size="sm",
                        margin="sm",
                    ),
                    FlexText(
                        text=f"สารออกฤทธิ์: {chem.active_ingredient}",
                        wrap=True,
                        size="xs",
                        color=cls.COLORS["secondary"],
                    ),
                    FlexText(
                        text=f"อัตรา: {chem.dosage}",
                        size="xs",
                        color=cls.COLORS["secondary"],
                    ),
                    FlexText(
                        text=f"⚠️ {chem.precautions}",
                        wrap=True,
                        size="xs",
                        color=cls.COLORS["warning"],
                    ),
                ])
            contents.append(FlexSeparator(margin="md"))

        # Organic control
        if result.treatment.organic_control:
            contents.extend([
                FlexText(
                    text="วิธีอินทรีย์",
                    weight="bold",
                    size="md",
                    color=cls.COLORS["success"],
                    margin="md",
                ),
                FlexText(
                    text="• " + "\n• ".join(result.treatment.organic_control),
                    wrap=True,
                    size="sm",
                    margin="sm",
                ),
                FlexSeparator(margin="md"),
            ])

        # Prevention methods
        if result.prevention_methods:
            contents.extend([
                FlexText(
                    text="วิธีป้องกัน",
                    weight="bold",
                    size="md",
                    margin="md",
                ),
                FlexText(
                    text="• " + "\n• ".join(result.prevention_methods[:3]),
                    wrap=True,
                    size="sm",
                    margin="sm",
                ),
            ])

        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                background_color=cls.COLORS["info"],
                padding_all="15px",
                contents=[
                    FlexText(
                        text="วิธีการรักษา",
                        weight="bold",
                        color=cls.COLORS["white"],
                        size="lg",
                    ),
                    FlexText(
                        text=result.disease_name_th,
                        color=cls.COLORS["white"],
                        size="sm",
                    ),
                ],
            ),
            body=FlexBox(
                layout="vertical",
                spacing="sm",
                contents=contents,
            ),
            footer=FlexBox(
                layout="vertical",
                spacing="sm",
                contents=[
                    FlexButton(
                        action=PostbackAction(
                            label="กลับไปดูผลวินิจฉัย",
                            data="show_diagnosis"
                        ),
                        style="secondary",
                        height="sm",
                    ),
                ],
            ),
        )

        return FlexMessage(
            alt_text=f"วิธีรักษา: {result.disease_name_th}",
            contents=bubble
        )

    @classmethod
    def create_error_message(cls, message: str) -> FlexMessage:
        """
        Create error message.

        Args:
            message: Error message to display

        Returns:
            FlexMessage with error
        """
        bubble = FlexBubble(
            body=FlexBox(
                layout="vertical",
                spacing="md",
                padding_all="20px",
                contents=[
                    FlexBox(
                        layout="horizontal",
                        justify_content="center",
                        contents=[
                            FlexText(text="⚠️", size="xxl"),
                        ],
                    ),
                    FlexText(
                        text="เกิดข้อผิดพลาด",
                        weight="bold",
                        size="lg",
                        align="center",
                        color=cls.COLORS["danger"],
                    ),
                    FlexText(
                        text=message,
                        wrap=True,
                        size="sm",
                        align="center",
                        color=cls.COLORS["secondary"],
                    ),
                ],
            ),
            footer=FlexBox(
                layout="vertical",
                contents=[
                    FlexButton(
                        action=PostbackAction(
                            label="ลองใหม่อีกครั้ง",
                            data="retry"
                        ),
                        style="primary",
                        height="sm",
                    ),
                ],
            ),
        )

        return FlexMessage(alt_text="เกิดข้อผิดพลาด", contents=bubble)

    @classmethod
    def create_welcome_message(cls) -> FlexMessage:
        """
        Create welcome message for new users.

        Returns:
            FlexMessage with welcome and instructions
        """
        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                background_color=cls.COLORS["primary"],
                padding_all="20px",
                contents=[
                    FlexText(
                        text="ยินดีต้อนรับ",
                        weight="bold",
                        color=cls.COLORS["white"],
                        size="xl",
                        align="center",
                    ),
                    FlexText(
                        text="ระบบวินิจฉัยโรคพืชด้วย AI",
                        color=cls.COLORS["white"],
                        size="md",
                        align="center",
                        margin="sm",
                    ),
                ],
            ),
            body=FlexBox(
                layout="vertical",
                spacing="md",
                contents=[
                    FlexText(
                        text="วิธีใช้งาน",
                        weight="bold",
                        size="lg",
                    ),
                    FlexBox(
                        layout="horizontal",
                        spacing="md",
                        margin="md",
                        contents=[
                            FlexText(text="1️⃣", size="lg"),
                            FlexText(
                                text="ถ่ายรูปใบหรือส่วนที่เป็นโรค",
                                wrap=True,
                                size="sm",
                                flex=5,
                            ),
                        ],
                    ),
                    FlexBox(
                        layout="horizontal",
                        spacing="md",
                        contents=[
                            FlexText(text="2️⃣", size="lg"),
                            FlexText(
                                text="เลือกชนิดพืชและจุดที่พบอาการ",
                                wrap=True,
                                size="sm",
                                flex=5,
                            ),
                        ],
                    ),
                    FlexBox(
                        layout="horizontal",
                        spacing="md",
                        contents=[
                            FlexText(text="3️⃣", size="lg"),
                            FlexText(
                                text="รับผลวินิจฉัยและคำแนะนำ",
                                wrap=True,
                                size="sm",
                                flex=5,
                            ),
                        ],
                    ),
                    FlexSeparator(margin="lg"),
                    FlexText(
                        text="💡 เคล็ดลับ: ถ่ายรูปให้ชัดและเห็นอาการโรคชัดเจน",
                        wrap=True,
                        size="xs",
                        color=cls.COLORS["light"],
                        margin="md",
                    ),
                ],
            ),
            footer=FlexBox(
                layout="vertical",
                contents=[
                    FlexText(
                        text="ส่งรูปภาพมาเพื่อเริ่มต้นใช้งาน",
                        size="sm",
                        color=cls.COLORS["secondary"],
                        align="center",
                    ),
                ],
            ),
        )

        return FlexMessage(alt_text="ยินดีต้อนรับสู่ระบบวินิจฉัยโรคพืช", contents=bubble)

    @classmethod
    def create_quick_reply_plant_types(cls) -> QuickReply:
        """
        Create quick reply buttons for plant types.

        Returns:
            QuickReply with plant type options
        """
        items = [
            QuickReplyItem(
                action=PostbackAction(
                    label=plant_type.value,
                    data=f"plant_type={plant_type.name}"
                )
            )
            for plant_type in PlantType
            if plant_type != PlantType.OTHER
        ]

        return QuickReply(items=items)

    @classmethod
    def create_quick_reply_plant_parts(cls) -> QuickReply:
        """
        Create quick reply buttons for plant parts.

        Returns:
            QuickReply with plant part options
        """
        items = [
            QuickReplyItem(
                action=PostbackAction(
                    label=part.value,
                    data=f"plant_part={part.name}"
                )
            )
            for part in PlantPart
        ]

        items.append(
            QuickReplyItem(
                action=PostbackAction(
                    label="ข้าม",
                    data="plant_part=skip"
                )
            )
        )

        return QuickReply(items=items)


# Convenience instance
flex_builder = FlexMessageBuilder()
