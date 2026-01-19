"""
Tests for Image Service
"""

import io

import pytest
from PIL import Image

from app.services.image_service import ImageService, ImageValidationError


class TestImageService:
    """Test ImageService class."""

    @pytest.fixture
    def image_service(self):
        """Create ImageService instance."""
        return ImageService(
            max_dimension=512,
            quality=85,
            max_size_bytes=5 * 1024 * 1024
        )

    @pytest.fixture
    def create_test_image(self):
        """Factory to create test images."""

        def _create(width: int, height: int, format: str = "JPEG") -> bytes:
            img = Image.new("RGB", (width, height), color="green")
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            return buffer.getvalue()

        return _create

    def test_validate_valid_jpeg(self, image_service, create_test_image):
        """Test validation of valid JPEG image."""
        image_data = create_test_image(100, 100, "JPEG")
        # Should not raise
        image_service.validate_image(image_data, "image/jpeg")

    def test_validate_valid_png(self, image_service, create_test_image):
        """Test validation of valid PNG image."""
        image_data = create_test_image(100, 100, "PNG")
        # Should not raise
        image_service.validate_image(image_data, "image/png")

    def test_validate_invalid_format(self, image_service, create_test_image):
        """Test validation rejects invalid format."""
        image_data = create_test_image(100, 100, "JPEG")
        with pytest.raises(ImageValidationError) as exc_info:
            image_service.validate_image(image_data, "image/gif")
        assert "รูปภาพไม่ถูกต้อง" in exc_info.value.user_message

    def test_validate_too_large(self, image_service):
        """Test validation rejects oversized image."""
        # Create a service with very small max size
        small_service = ImageService(max_size_bytes=100)
        image_data = b"x" * 200

        with pytest.raises(ImageValidationError) as exc_info:
            small_service.validate_image(image_data, "image/jpeg")
        assert "ใหญ่เกินไป" in exc_info.value.user_message

    def test_optimize_resize_large_image(self, image_service, create_test_image):
        """Test optimization resizes large images."""
        # Create image larger than max_dimension
        image_data = create_test_image(1000, 1000, "JPEG")

        optimized_data, content_type = image_service.optimize_image(image_data)

        # Check the optimized image dimensions
        optimized_img = Image.open(io.BytesIO(optimized_data))
        assert optimized_img.width <= 512
        assert optimized_img.height <= 512

    def test_optimize_maintains_aspect_ratio(self, image_service, create_test_image):
        """Test optimization maintains aspect ratio."""
        # Create rectangular image
        image_data = create_test_image(1000, 500, "JPEG")

        optimized_data, _ = image_service.optimize_image(image_data)

        optimized_img = Image.open(io.BytesIO(optimized_data))
        aspect_ratio = optimized_img.width / optimized_img.height
        assert 1.9 <= aspect_ratio <= 2.1  # ~2:1 ratio

    def test_optimize_converts_rgba_to_rgb(self, image_service):
        """Test optimization converts RGBA to RGB."""
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(0, 255, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        optimized_data, _ = image_service.optimize_image(image_data)

        optimized_img = Image.open(io.BytesIO(optimized_data))
        assert optimized_img.mode == "RGB"

    def test_optimize_reduces_size(self, image_service, create_test_image):
        """Test optimization reduces file size."""
        # Create large image
        image_data = create_test_image(1000, 1000, "JPEG")

        optimized_data, _ = image_service.optimize_image(image_data)

        assert len(optimized_data) < len(image_data)

    def test_to_base64(self, image_service, sample_image_data):
        """Test base64 encoding."""
        base64_str = image_service.to_base64(sample_image_data)
        assert isinstance(base64_str, str)
        assert len(base64_str) > 0

    def test_from_base64(self, image_service, sample_image_data):
        """Test base64 decoding."""
        base64_str = image_service.to_base64(sample_image_data)
        decoded = image_service.from_base64(base64_str)
        assert decoded == sample_image_data

    def test_get_image_info(self, image_service, create_test_image):
        """Test getting image info."""
        image_data = create_test_image(200, 150, "JPEG")

        info = image_service.get_image_info(image_data)

        assert info["width"] == 200
        assert info["height"] == 150
        assert info["format"] == "JPEG"
        assert info["mode"] == "RGB"
        assert info["size_bytes"] == len(image_data)

    def test_get_image_info_invalid(self, image_service):
        """Test getting image info for invalid data."""
        info = image_service.get_image_info(b"not an image")
        assert "error" in info

    def test_small_image_not_resized(self, image_service, create_test_image):
        """Test small images are not resized."""
        # Create image smaller than max_dimension
        image_data = create_test_image(256, 256, "JPEG")

        optimized_data, _ = image_service.optimize_image(image_data)

        optimized_img = Image.open(io.BytesIO(optimized_data))
        assert optimized_img.width == 256
        assert optimized_img.height == 256

    def test_webp_output(self, image_service, create_test_image):
        """Test WEBP output format."""
        image_data = create_test_image(100, 100, "JPEG")

        optimized_data, content_type = image_service.optimize_image(
            image_data, output_format="WEBP"
        )

        assert content_type == "image/webp"
