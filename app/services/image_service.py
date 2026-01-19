"""
Image Service Module
Image optimization and processing for plant disease detection
"""

import base64
import io
import logging
from typing import Literal

import httpx
from PIL import Image, ImageOps

from app.config import get_settings
from app.models import ERROR_MESSAGES

logger = logging.getLogger(__name__)
settings = get_settings()

# Supported image formats
SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
EXTENSION_MAP = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP"
}


class ImageValidationError(Exception):
    """Exception raised when image validation fails."""

    def __init__(self, message: str, user_message: str):
        super().__init__(message)
        self.user_message = user_message


class ImageService:
    """
    Service for image processing and optimization.

    Handles:
    - Downloading images from LINE Content API
    - Validating image format and size
    - Resizing and compressing images
    - Converting to optimal format for API
    """

    def __init__(
        self,
        max_dimension: int | None = None,
        quality: int | None = None,
        max_size_bytes: int | None = None
    ):
        """
        Initialize image service.

        Args:
            max_dimension: Maximum width/height in pixels
            quality: JPEG/WebP quality (1-100)
            max_size_bytes: Maximum file size in bytes
        """
        self.max_dimension = max_dimension or settings.image_max_dimension
        self.quality = quality or settings.image_quality
        self.max_size_bytes = max_size_bytes or settings.max_image_size_bytes

    async def download_from_line(
        self,
        message_id: str,
        channel_token: str
    ) -> tuple[bytes, str]:
        """
        Download image from LINE Content API.

        Args:
            message_id: LINE message ID
            channel_token: LINE channel access token

        Returns:
            Tuple of (image_data, content_type)

        Raises:
            ImageValidationError: If download fails
        """
        url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        headers = {"Authorization": f"Bearer {channel_token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "image/jpeg")
                image_data = response.content

                logger.info(
                    f"Downloaded image: {len(image_data)} bytes, type: {content_type}"
                )

                return image_data, content_type

            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to download image: {e}")
                raise ImageValidationError(
                    f"HTTP error: {e.response.status_code}",
                    ERROR_MESSAGES["api_error"]
                )
            except httpx.RequestError as e:
                logger.error(f"Request error downloading image: {e}")
                raise ImageValidationError(
                    str(e),
                    ERROR_MESSAGES["api_error"]
                )

    def validate_image(
        self,
        image_data: bytes,
        content_type: str
    ) -> None:
        """
        Validate image format and size.

        Args:
            image_data: Image binary data
            content_type: MIME type of the image

        Raises:
            ImageValidationError: If validation fails
        """
        # Check content type
        if content_type not in SUPPORTED_FORMATS:
            raise ImageValidationError(
                f"Unsupported format: {content_type}",
                ERROR_MESSAGES["invalid_image_format"]
            )

        # Check file size
        if len(image_data) > self.max_size_bytes:
            max_mb = settings.max_image_size_mb
            raise ImageValidationError(
                f"Image too large: {len(image_data)} bytes",
                ERROR_MESSAGES["image_too_large"].format(max_size=max_mb)
            )

        # Try to open the image to verify it's valid
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()
        except Exception as e:
            logger.error(f"Invalid image data: {e}")
            raise ImageValidationError(
                f"Invalid image: {e}",
                ERROR_MESSAGES["invalid_image_format"]
            )

    def optimize_image(
        self,
        image_data: bytes,
        output_format: Literal["JPEG", "WEBP"] = "JPEG"
    ) -> tuple[bytes, str]:
        """
        Optimize image for API processing.

        Operations:
        - Resize to max dimension while maintaining aspect ratio
        - Auto-orient based on EXIF data
        - Compress to specified quality
        - Convert to specified format

        Args:
            image_data: Input image binary data
            output_format: Output format (JPEG or WEBP)

        Returns:
            Tuple of (optimized_data, content_type)
        """
        # Open image
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (for JPEG compatibility)
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Auto-orient based on EXIF
        img = ImageOps.exif_transpose(img)

        # Resize if necessary
        original_size = img.size
        img = self._resize_image(img)
        if img.size != original_size:
            logger.info(f"Resized image from {original_size} to {img.size}")

        # Save to buffer with compression
        buffer = io.BytesIO()
        if output_format == "WEBP":
            img.save(buffer, format="WEBP", quality=self.quality, method=6)
            content_type = "image/webp"
        else:
            img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
            content_type = "image/jpeg"

        optimized_data = buffer.getvalue()
        logger.info(
            f"Optimized image: {len(image_data)} -> {len(optimized_data)} bytes "
            f"({100 * len(optimized_data) / len(image_data):.1f}%)"
        )

        return optimized_data, content_type

    def _resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image to fit within max dimension.

        Args:
            img: PIL Image object

        Returns:
            Resized PIL Image
        """
        width, height = img.size

        if width <= self.max_dimension and height <= self.max_dimension:
            return img

        # Calculate new dimensions
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def to_base64(self, image_data: bytes) -> str:
        """
        Convert image data to base64 string.

        Args:
            image_data: Image binary data

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_data).decode("utf-8")

    def from_base64(self, base64_string: str) -> bytes:
        """
        Convert base64 string to image data.

        Args:
            base64_string: Base64 encoded string

        Returns:
            Image binary data
        """
        return base64.b64decode(base64_string)

    def get_image_info(self, image_data: bytes) -> dict:
        """
        Get information about an image.

        Args:
            image_data: Image binary data

        Returns:
            Dictionary with image info
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            return {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "size_bytes": len(image_data),
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return {"error": str(e)}

    async def process_line_image(
        self,
        message_id: str,
        channel_token: str
    ) -> tuple[bytes, str]:
        """
        Download and process image from LINE.

        Complete pipeline:
        1. Download from LINE Content API
        2. Validate format and size
        3. Optimize for API processing

        Args:
            message_id: LINE message ID
            channel_token: LINE channel access token

        Returns:
            Tuple of (optimized_image_data, content_type)
        """
        # Download
        image_data, content_type = await self.download_from_line(
            message_id, channel_token
        )

        # Validate
        self.validate_image(image_data, content_type)

        # Optimize
        optimized_data, new_content_type = self.optimize_image(image_data)

        return optimized_data, new_content_type


# Global image service instance
image_service = ImageService()
