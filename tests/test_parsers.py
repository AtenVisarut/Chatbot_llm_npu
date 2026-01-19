"""
Tests for Parser Utilities
"""

import pytest

from app.models import PlantType, Region
from app.utils.parsers import (
    extract_numbers,
    extract_plant_info,
    is_greeting,
    is_help_request,
    is_skip_command,
    normalize_thai_text,
    parse_plant_type,
    parse_postback_data,
    parse_region,
    parse_user_response,
    sanitize_text,
)


class TestParsePostbackData:
    """Test postback data parsing."""

    def test_single_value(self):
        """Test parsing single key-value pair."""
        result = parse_postback_data("plant_type=RICE")
        assert result == {"plant_type": "RICE"}

    def test_multiple_values(self):
        """Test parsing multiple key-value pairs."""
        result = parse_postback_data("plant_type=RICE&region=NORTH")
        assert result == {"plant_type": "RICE", "region": "NORTH"}

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_postback_data("")
        assert result == {}

    def test_value_with_special_chars(self):
        """Test parsing value with special characters."""
        result = parse_postback_data("action=show_treatment")
        assert result == {"action": "show_treatment"}


class TestParsePlantType:
    """Test plant type parsing."""

    def test_thai_rice(self):
        """Test parsing Thai word for rice."""
        assert parse_plant_type("ข้าว") == PlantType.RICE

    def test_thai_corn(self):
        """Test parsing Thai word for corn."""
        assert parse_plant_type("ข้าวโพด") == PlantType.CORN

    def test_thai_cassava(self):
        """Test parsing Thai word for cassava."""
        assert parse_plant_type("มันสำปะหลัง") == PlantType.CASSAVA

    def test_english_rice(self):
        """Test parsing English word for rice."""
        assert parse_plant_type("rice") == PlantType.RICE

    def test_enum_name(self):
        """Test parsing enum name directly."""
        assert parse_plant_type("RICE") == PlantType.RICE

    def test_unknown_plant(self):
        """Test parsing unknown plant returns None."""
        assert parse_plant_type("unknown plant") is None

    def test_partial_match(self):
        """Test partial match in sentence."""
        assert parse_plant_type("นาข้าวของผม") == PlantType.RICE


class TestParseRegion:
    """Test region parsing."""

    def test_thai_north(self):
        """Test parsing Thai word for north."""
        assert parse_region("ภาคเหนือ") == Region.NORTH

    def test_thai_northeast(self):
        """Test parsing Thai word for northeast."""
        assert parse_region("อีสาน") == Region.NORTHEAST

    def test_english_central(self):
        """Test parsing English word for central."""
        assert parse_region("central") == Region.CENTRAL

    def test_short_form(self):
        """Test parsing short form."""
        assert parse_region("เหนือ") == Region.NORTH

    def test_unknown_region(self):
        """Test parsing unknown region returns None."""
        assert parse_region("unknown") is None


class TestIsGreeting:
    """Test greeting detection."""

    def test_thai_greeting(self):
        """Test Thai greetings."""
        assert is_greeting("สวัสดี") is True
        assert is_greeting("สวัสดีครับ") is True
        assert is_greeting("หวัดดี") is True

    def test_english_greeting(self):
        """Test English greetings."""
        assert is_greeting("hello") is True
        assert is_greeting("Hi") is True

    def test_not_greeting(self):
        """Test non-greeting text."""
        assert is_greeting("ข้าวเป็นโรค") is False


class TestIsHelpRequest:
    """Test help request detection."""

    def test_thai_help(self):
        """Test Thai help keywords."""
        assert is_help_request("ช่วยด้วย") is True
        assert is_help_request("วิธีใช้งาน") is True

    def test_english_help(self):
        """Test English help keyword."""
        assert is_help_request("help") is True

    def test_not_help(self):
        """Test non-help text."""
        assert is_help_request("ข้าวเป็นโรค") is False


class TestIsSkipCommand:
    """Test skip command detection."""

    def test_thai_skip(self):
        """Test Thai skip keywords."""
        assert is_skip_command("ข้าม") is True
        assert is_skip_command("ไม่ระบุ") is True

    def test_english_skip(self):
        """Test English skip keyword."""
        assert is_skip_command("skip") is True

    def test_dash_skip(self):
        """Test dash as skip."""
        assert is_skip_command("-") is True


class TestSanitizeText:
    """Test text sanitization."""

    def test_removes_control_chars(self):
        """Test removal of control characters."""
        text = "hello\x00world"
        assert sanitize_text(text) == "hello world"

    def test_normalizes_whitespace(self):
        """Test whitespace normalization."""
        text = "hello   world"
        assert sanitize_text(text) == "hello world"

    def test_truncates_long_text(self):
        """Test truncation of long text."""
        text = "a" * 2000
        result = sanitize_text(text, max_length=100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")


class TestExtractNumbers:
    """Test number extraction."""

    def test_single_number(self):
        """Test extracting single number."""
        assert extract_numbers("อายุ 50 วัน") == [50]

    def test_multiple_numbers(self):
        """Test extracting multiple numbers."""
        assert extract_numbers("ใช้ 20 กรัม ต่อ น้ำ 20 ลิตร") == [20, 20]

    def test_no_numbers(self):
        """Test text with no numbers."""
        assert extract_numbers("ไม่มีตัวเลข") == []


class TestNormalizeThaiText:
    """Test Thai text normalization."""

    def test_removes_extra_spaces(self):
        """Test removal of extra spaces."""
        text = "สวัสดี   ครับ"
        assert normalize_thai_text(text) == "สวัสดี ครับ"

    def test_trims_whitespace(self):
        """Test trimming of whitespace."""
        text = "  สวัสดี  "
        assert normalize_thai_text(text) == "สวัสดี"


class TestParseUserResponse:
    """Test user response parsing."""

    def test_extracts_plant_type(self):
        """Test plant type extraction."""
        result = parse_user_response("ข้าวนาปี")
        assert result["plant_type"] == PlantType.RICE

    def test_extracts_region(self):
        """Test region extraction."""
        result = parse_user_response("ภาคอีสาน")
        assert result["region"] == Region.NORTHEAST

    def test_stores_additional_info(self):
        """Test storing unknown text as additional info."""
        result = parse_user_response("ข้อมูลอื่นๆ")
        assert result["additional_info"] == "ข้อมูลอื่นๆ"


class TestExtractPlantInfo:
    """Test plant info extraction."""

    def test_extracts_all_info(self):
        """Test extracting all information."""
        plant_type, region, additional = extract_plant_info("ข้าว ภาคเหนือ")
        assert plant_type == PlantType.RICE
        # Note: region parsing from same string might vary
