"""
Tests for Pydantic Models
"""

import pytest
from pydantic import ValidationError

from app.models import (
    ChemicalControl,
    DiagnosisResult,
    DiseaseCharacteristics,
    PlantType,
    Region,
    Severity,
    Treatment,
    UserInfo,
    UserState,
)


class TestEnums:
    """Test enum models."""

    def test_plant_type_values(self):
        """Test PlantType enum values."""
        assert PlantType.RICE.value == "ข้าว"
        assert PlantType.CORN.value == "ข้าวโพด"
        assert PlantType.CASSAVA.value == "มันสำปะหลัง"

    def test_region_values(self):
        """Test Region enum values."""
        assert Region.NORTH.value == "ภาคเหนือ"
        assert Region.NORTHEAST.value == "ภาคอีสาน"
        assert Region.CENTRAL.value == "ภาคกลาง"

    def test_severity_values(self):
        """Test Severity enum values."""
        assert Severity.MILD.value == "เล็กน้อย"
        assert Severity.MODERATE.value == "ปานกลาง"
        assert Severity.SEVERE.value == "รุนแรง"

    def test_user_state_values(self):
        """Test UserState enum values."""
        assert UserState.IDLE.value == "idle"
        assert UserState.PROCESSING.value == "processing"
        assert UserState.COMPLETED.value == "completed"


class TestChemicalControl:
    """Test ChemicalControl model."""

    def test_valid_chemical_control(self):
        """Test valid chemical control creation."""
        chem = ChemicalControl(
            product_name="ไตรไซคลาโซล",
            active_ingredient="Tricyclazole 75% WP",
            dosage="20 กรัม/น้ำ 20 ลิตร",
            application_method="พ่นทางใบ",
            precautions="ห้ามพ่นก่อนเก็บเกี่ยว 21 วัน"
        )
        assert chem.product_name == "ไตรไซคลาโซล"
        assert chem.active_ingredient == "Tricyclazole 75% WP"

    def test_missing_required_field(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ValidationError):
            ChemicalControl(
                product_name="Test",
                # Missing other required fields
            )


class TestDiseaseCharacteristics:
    """Test DiseaseCharacteristics model."""

    def test_valid_characteristics(self):
        """Test valid disease characteristics."""
        chars = DiseaseCharacteristics(
            appearance="จุดสีน้ำตาล",
            occurrence="อากาศชื้น",
            spread_pattern="ทางลม",
            severity=Severity.MODERATE
        )
        assert chars.severity == Severity.MODERATE

    def test_severity_string_conversion(self):
        """Test severity can be created from string."""
        chars = DiseaseCharacteristics(
            appearance="test",
            occurrence="test",
            spread_pattern="test",
            severity="ปานกลาง"
        )
        assert chars.severity == Severity.MODERATE


class TestTreatment:
    """Test Treatment model."""

    def test_default_empty_lists(self):
        """Test default empty lists for treatment fields."""
        treatment = Treatment()
        assert treatment.immediate_action == []
        assert treatment.chemical_control == []
        assert treatment.organic_control == []
        assert treatment.cultural_practices == []

    def test_with_values(self):
        """Test treatment with values."""
        treatment = Treatment(
            immediate_action=["ตัดใบที่เป็นโรค"],
            organic_control=["ใช้เชื้อ Trichoderma"]
        )
        assert len(treatment.immediate_action) == 1
        assert len(treatment.organic_control) == 1


class TestDiagnosisResult:
    """Test DiagnosisResult model."""

    def test_valid_diagnosis_result(self, sample_diagnosis_result):
        """Test valid diagnosis result creation."""
        result = DiagnosisResult(**sample_diagnosis_result)
        assert result.disease_name_th == "โรคไหม้"
        assert result.confidence_level == 85
        assert result.followup_needed is True

    def test_confidence_level_bounds(self):
        """Test confidence level must be 0-100."""
        with pytest.raises(ValidationError):
            DiagnosisResult(
                disease_name_th="Test",
                disease_name_en="Test",
                pathogen_type="Test",
                confidence_level=150,  # Invalid
                disease_characteristics={
                    "appearance": "test",
                    "occurrence": "test",
                    "spread_pattern": "test",
                    "severity": "เล็กน้อย"
                },
                treatment={}
            )

    def test_model_dump_json(self, sample_diagnosis_result):
        """Test model can be serialized to JSON."""
        result = DiagnosisResult(**sample_diagnosis_result)
        json_str = result.model_dump_json()
        assert "โรคไหม้" in json_str


class TestUserInfo:
    """Test UserInfo model."""

    def test_default_values(self):
        """Test default values for UserInfo."""
        info = UserInfo()
        assert info.plant_type is None
        assert info.region is None
        assert info.additional_info is None

    def test_with_values(self):
        """Test UserInfo with values."""
        info = UserInfo(
            plant_type=PlantType.RICE,
            region=Region.NORTHEAST,
            additional_info="ข้าวอายุ 2 เดือน"
        )
        assert info.plant_type == PlantType.RICE
        assert info.region == Region.NORTHEAST
