"""
Text Parsing Utilities Module
Utilities for parsing user input and postback data
"""

import re
from typing import Any
from urllib.parse import parse_qs

from app.models import PlantPart, PlantType


def parse_postback_data(data: str) -> dict[str, str]:
    """
    Parse postback data string into dictionary.

    Args:
        data: Postback data string (e.g., "plant_type=RICE&plant_part=LEAF")

    Returns:
        Dictionary of parsed key-value pairs
    """
    result = {}
    pairs = data.split("&")

    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[key.strip()] = value.strip()

    return result


def parse_plant_type(text: str) -> PlantType | None:
    """
    Parse plant type from user text input.

    Args:
        text: User input text

    Returns:
        PlantType enum or None if not recognized
    """
    text_lower = text.lower().strip()

    # Direct Thai matches
    thai_mappings = {
        "ข้าว": PlantType.RICE,
        "ข้าวโพด": PlantType.CORN,
        "ข้าวโพดเลี้ยงสัตว์": PlantType.CORN,
        "มันสำปะหลัง": PlantType.CASSAVA,
        "มัน": PlantType.CASSAVA,
        "อ้อย": PlantType.SUGARCANE,
        "พืชผัก": PlantType.VEGETABLE,
        "ผัก": PlantType.VEGETABLE,
        "ไม้ผล": PlantType.FRUIT,
        "ผลไม้": PlantType.FRUIT,
    }

    for key, plant_type in thai_mappings.items():
        if key in text_lower:
            return plant_type

    # English matches
    english_mappings = {
        "rice": PlantType.RICE,
        "corn": PlantType.CORN,
        "maize": PlantType.CORN,
        "cassava": PlantType.CASSAVA,
        "sugarcane": PlantType.SUGARCANE,
        "sugar cane": PlantType.SUGARCANE,
        "vegetable": PlantType.VEGETABLE,
        "fruit": PlantType.FRUIT,
    }

    for key, plant_type in english_mappings.items():
        if key in text_lower:
            return plant_type

    # Try matching enum names
    for plant_type in PlantType:
        if plant_type.name.lower() == text_lower:
            return plant_type

    return None


def parse_plant_part(text: str) -> PlantPart | None:
    """
    Parse plant part from user text input.

    Args:
        text: User input text

    Returns:
        PlantPart enum or None if not recognized
    """
    text_lower = text.lower().strip()

    # Thai mappings
    thai_mappings = {
        "ใบ": PlantPart.LEAF,
        "ลำต้น": PlantPart.STEM,
        "ราก": PlantPart.ROOT,
        "กาบใบ": PlantPart.SHEATH,
        "กาบ": PlantPart.SHEATH,
    }

    for key, part in thai_mappings.items():
        if key in text_lower:
            return part

    # English mappings
    english_mappings = {
        "leaf": PlantPart.LEAF,
        "stem": PlantPart.STEM,
        "root": PlantPart.ROOT,
        "sheath": PlantPart.SHEATH,
    }

    for key, part in english_mappings.items():
        if key in text_lower:
            return part

    # Try matching enum names
    for part in PlantPart:
        if part.name.lower() == text_lower:
            return part

    return None


def parse_user_response(text: str) -> dict[str, Any]:
    """
    Parse user text response to extract useful information.

    Args:
        text: User input text

    Returns:
        Dictionary with parsed information
    """
    result = {
        "plant_type": parse_plant_type(text),
        "plant_part": parse_plant_part(text),
        "additional_info": None,
    }

    # If no plant type or part found, treat as additional info
    if result["plant_type"] is None and result["plant_part"] is None:
        result["additional_info"] = text.strip()

    return result


def extract_plant_info(text: str) -> tuple[PlantType | None, PlantPart | None, str | None]:
    """
    Extract plant type, plant part, and additional info from text.

    Args:
        text: User input text

    Returns:
        Tuple of (plant_type, plant_part, additional_info)
    """
    parsed = parse_user_response(text)
    return (
        parsed["plant_type"],
        parsed["plant_part"],
        parsed["additional_info"]
    )


def is_greeting(text: str) -> bool:
    """
    Check if text is a greeting.

    Args:
        text: User input text

    Returns:
        True if text is a greeting
    """
    greetings = [
        "สวัสดี", "หวัดดี", "ดีครับ", "ดีค่ะ", "hello", "hi",
        "hey", "สวัสดีครับ", "สวัสดีค่ะ", "ดี"
    ]
    text_lower = text.lower().strip()
    return any(greeting in text_lower for greeting in greetings)


def is_help_request(text: str) -> bool:
    """
    Check if text is a help request.

    Args:
        text: User input text

    Returns:
        True if text is asking for help
    """
    help_keywords = [
        "ช่วย", "help", "วิธีใช้", "ใช้งาน", "ยังไง",
        "อย่างไร", "คำสั่ง", "เมนู", "menu"
    ]
    text_lower = text.lower().strip()
    return any(keyword in text_lower for keyword in help_keywords)


def is_skip_command(text: str) -> bool:
    """
    Check if text is a skip command.

    Args:
        text: User input text

    Returns:
        True if user wants to skip
    """
    skip_keywords = ["ข้าม", "skip", "ไม่ระบุ", "ไม่ทราบ", "-"]
    text_lower = text.lower().strip()
    return any(keyword in text_lower for keyword in skip_keywords)


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input text.

    Args:
        text: User input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    # Remove control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Trim
    text = text.strip()

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def extract_numbers(text: str) -> list[int]:
    """
    Extract all numbers from text.

    Args:
        text: Input text

    Returns:
        List of extracted integers
    """
    return [int(n) for n in re.findall(r"\d+", text)]


def normalize_thai_text(text: str) -> str:
    """
    Normalize Thai text by removing extra spaces and normalizing characters.

    Args:
        text: Thai text

    Returns:
        Normalized text
    """
    # Remove Thai tone marks that might cause matching issues
    # (optional - depends on your use case)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()
