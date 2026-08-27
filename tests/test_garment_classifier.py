from io import BytesIO
from PIL import Image
from app.services.garment_classifier import classify_category, classify_dominant_color

def make_image(color: tuple[int, int, int, int]) -> bytes:
    output = BytesIO()
    Image.new("RGBA", (10, 10), color).save(output, format="PNG")
    return output.getvalue()

def test_category_is_classified_from_filename() -> None:
    assert classify_category("summer-dress.png") == "dress"
    assert classify_category("unlabelled.png") == "other"

def test_transparent_pixels_are_ignored_for_color() -> None:
    assert classify_dominant_color(make_image((215, 40, 40, 255))) == "red"
