"""
Gemini Service Module
Google Gemini Vision API integration for plant disease diagnosis
"""

import asyncio
import base64
import json
import logging
import re
from typing import Any

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from app.config import DIAGNOSIS_JSON_SCHEMA, GEMINI_SYSTEM_INSTRUCTION, get_settings
from app.models import DiagnosisResult, ERROR_MESSAGES, PlantType, Region

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiAPIError(Exception):
    """Exception raised when Gemini API fails."""

    def __init__(self, message: str, user_message: str, retryable: bool = True):
        super().__init__(message)
        self.user_message = user_message
        self.retryable = retryable


class GeminiService:
    """
    Service for interacting with Google Gemini Vision API.

    Handles:
    - Plant disease diagnosis from images
    - Retry mechanism with exponential backoff
    - Response parsing and validation
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None
    ):
        """
        Initialize Gemini service.

        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.max_retries = settings.api_max_retries
        self.retry_delay = settings.api_retry_delay

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Safety settings - allow agricultural/medical content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Model configuration
        self.generation_config = {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4096,
            "response_mime_type": "application/json",
        }

        # Initialize model
        self._model = None

    @property
    def model(self):
        """Get or create Gemini model instance."""
        if self._model is None:
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction=self._build_system_instruction()
            )
        return self._model

    def _build_system_instruction(self) -> str:
        """Build the system instruction with JSON schema."""
        schema_str = json.dumps(DIAGNOSIS_JSON_SCHEMA, ensure_ascii=False, indent=2)
        return GEMINI_SYSTEM_INSTRUCTION.replace("{JSON_SCHEMA}", schema_str)

    def _build_prompt(
        self,
        plant_type: PlantType,
        region: Region | None = None,
        additional_info: str | None = None
    ) -> str:
        """
        Build diagnosis prompt.

        Args:
            plant_type: Type of plant
            region: Thai region
            additional_info: Additional information from user

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"วิเคราะห์โรคพืชจากภาพนี้",
            f"ชนิดพืช: {plant_type.value}",
        ]

        if region:
            prompt_parts.append(f"ภูมิภาค: {region.value}")

        if additional_info:
            prompt_parts.append(f"ข้อมูลเพิ่มเติมจากผู้ใช้: {additional_info}")

        prompt_parts.extend([
            "",
            "กรุณาวิเคราะห์และตอบเป็น JSON ตามรูปแบบที่กำหนด",
            "หากไม่พบโรคหรือพืชในภาพ ให้ระบุในผลลัพธ์"
        ])

        return "\n".join(prompt_parts)

    def _prepare_image_content(
        self,
        image_data: bytes,
        content_type: str = "image/jpeg"
    ) -> dict:
        """
        Prepare image content for API.

        Args:
            image_data: Image binary data
            content_type: MIME type

        Returns:
            Image content dictionary
        """
        base64_image = base64.b64encode(image_data).decode("utf-8")
        return {
            "mime_type": content_type,
            "data": base64_image
        }

    def _parse_response(self, response_text: str) -> DiagnosisResult:
        """
        Parse and validate Gemini response.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            DiagnosisResult object

        Raises:
            GeminiAPIError: If parsing fails
        """
        # Clean up response text
        text = response_text.strip()

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            text = json_match.group(1).strip()

        try:
            data = json.loads(text)
            return DiagnosisResult.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}\nResponse: {text[:500]}")
            raise GeminiAPIError(
                f"Invalid JSON response: {e}",
                ERROR_MESSAGES["api_error"],
                retryable=True
            )
        except Exception as e:
            logger.error(f"Validation error: {e}\nData: {text[:500]}")
            raise GeminiAPIError(
                f"Response validation failed: {e}",
                ERROR_MESSAGES["api_error"],
                retryable=False
            )

    async def diagnose(
        self,
        image_data: bytes,
        plant_type: PlantType,
        content_type: str = "image/jpeg",
        region: Region | None = None,
        additional_info: str | None = None
    ) -> DiagnosisResult:
        """
        Diagnose plant disease from image.

        Args:
            image_data: Image binary data
            plant_type: Type of plant
            content_type: Image MIME type
            region: Thai region
            additional_info: Additional information

        Returns:
            DiagnosisResult object

        Raises:
            GeminiAPIError: If diagnosis fails after retries
        """
        prompt = self._build_prompt(plant_type, region, additional_info)
        image_content = self._prepare_image_content(image_data, content_type)

        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Diagnosis attempt {attempt + 1}/{self.max_retries}")

                # Call Gemini API
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    [prompt, image_content]
                )

                if not response.text:
                    raise GeminiAPIError(
                        "Empty response from Gemini",
                        ERROR_MESSAGES["api_error"],
                        retryable=True
                    )

                # Parse response
                result = self._parse_response(response.text)

                logger.info(
                    f"Diagnosis successful: {result.disease_name_th} "
                    f"({result.confidence_level}%)"
                )

                return result

            except GeminiAPIError as e:
                last_error = e
                if not e.retryable:
                    raise

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retrying in {delay}s due to: {e}"
                    )
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_error = GeminiAPIError(
                    str(e),
                    ERROR_MESSAGES["api_error"],
                    retryable=True
                )

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        raise last_error or GeminiAPIError(
            "Max retries exceeded",
            ERROR_MESSAGES["api_error"],
            retryable=False
        )

    async def analyze_image_quality(
        self,
        image_data: bytes,
        content_type: str = "image/jpeg"
    ) -> dict[str, Any]:
        """
        Analyze image quality for diagnosis.

        Args:
            image_data: Image binary data
            content_type: Image MIME type

        Returns:
            Quality analysis dictionary
        """
        prompt = """
        วิเคราะห์คุณภาพของภาพนี้สำหรับการวินิจฉัยโรคพืช
        ตอบเป็น JSON ดังนี้:
        {
            "is_plant_visible": true/false,
            "is_disease_visible": true/false,
            "image_quality": "good/fair/poor",
            "suggestions": ["คำแนะนำ..."]
        }
        """

        image_content = self._prepare_image_content(image_data, content_type)

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image_content]
            )

            if response.text:
                text = response.text.strip()
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
                if json_match:
                    text = json_match.group(1).strip()
                return json.loads(text)

        except Exception as e:
            logger.warning(f"Image quality analysis failed: {e}")

        return {
            "is_plant_visible": True,
            "is_disease_visible": True,
            "image_quality": "unknown",
            "suggestions": []
        }

    async def health_check(self) -> bool:
        """
        Check Gemini API health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # List available models as a health check
            models = await asyncio.to_thread(genai.list_models)
            model_names = [m.name for m in models]
            return f"models/{self.model_name}" in model_names or any(
                self.model_name in name for name in model_names
            )
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False


# Global gemini service instance
gemini_service = GeminiService()
