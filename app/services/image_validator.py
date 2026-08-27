from io import BytesIO
from PIL import Image, ImageStat, UnidentifiedImageError

class InvalidImageError(ValueError): pass

def validate_image_bytes(
    data: bytes, *, min_width: int = 32, min_height: int = 32,
    max_pixels: int = 40_000_000, require_foreground: bool = False,
) -> dict[str, int | str]:
    if not data:
        raise InvalidImageError("Image is empty")
    try:
        with Image.open(BytesIO(data)) as probe:
            probe.verify()
        with Image.open(BytesIO(data)) as source:
            source.load()
            width, height = source.size
            image_format = source.format or "unknown"
            if width < min_width or height < min_height:
                raise InvalidImageError(f"Image is smaller than {min_width}x{min_height}")
            if width * height > max_pixels:
                raise InvalidImageError("Image dimensions exceed the safe pixel limit")
            rgba = source.convert("RGBA")
            alpha = rgba.getchannel("A")
            if require_foreground and alpha.getbbox() is None:
                raise InvalidImageError("Image has no visible foreground pixels")
            rgb = rgba.convert("RGB").resize((64, 64))
            if sum(ImageStat.Stat(rgb).var) < 1.0:
                raise InvalidImageError("Image contains no meaningful visual content")
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("Image is corrupt or unsupported") from exc
    return {"width": width, "height": height, "format": image_format}
