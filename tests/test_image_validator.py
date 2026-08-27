from io import BytesIO
import pytest
from PIL import Image
from app.services.image_validator import InvalidImageError, validate_image_bytes

def image_bytes(mode: str, color) -> bytes:
    output = BytesIO()
    Image.new(mode, (64, 64), color).save(output, format="PNG")
    return output.getvalue()

def test_corrupt_image_is_rejected() -> None:
    with pytest.raises(InvalidImageError, match="corrupt"):
        validate_image_bytes(b"not-an-image")

def test_fully_transparent_image_is_rejected_as_foreground() -> None:
    with pytest.raises(InvalidImageError, match="foreground"):
        validate_image_bytes(image_bytes("RGBA", (0, 0, 0, 0)), require_foreground=True)

def test_meaningful_image_is_accepted() -> None:
    image = Image.new("RGB", (64, 64), "white")
    for x in range(20, 44):
        for y in range(20, 44):
            image.putpixel((x, y), (30, 80, 180))
    output = BytesIO()
    image.save(output, format="PNG")
    assert validate_image_bytes(output.getvalue())["width"] == 64
