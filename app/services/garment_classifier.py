from io import BytesIO
from pathlib import Path
from PIL import Image

CATEGORY_KEYWORDS = {
    "top": ("top", "shirt", "tshirt", "tee", "blouse", "sweater", "hoodie", "상의", "셔츠"),
    "bottom": ("bottom", "pants", "trouser", "jeans", "shorts", "skirt", "바지", "치마"),
    "dress": ("dress", "gown", "원피스", "드레스"),
    "outerwear": ("outer", "jacket", "coat", "blazer", "cardigan", "재킷", "코트"),
}

NAMED_COLORS = {
    "black": (20, 20, 20), "white": (240, 240, 240), "gray": (128, 128, 128),
    "red": (210, 45, 45), "orange": (230, 125, 35), "yellow": (225, 205, 45),
    "green": (55, 145, 70), "blue": (50, 100, 200), "purple": (125, 70, 155),
    "pink": (225, 135, 165), "brown": (120, 75, 45), "beige": (210, 190, 150),
}

def classify_category(filename: str | None) -> str:
    stem = Path(filename or "").stem.lower().replace("-", "_")
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in stem for keyword in keywords):
            return category
    return "other"

def classify_dominant_color(image_bytes: bytes) -> str:
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.convert("RGBA")
        image.thumbnail((256, 256))
        opaque_rgb = [pixel[:3] for pixel in image.getdata() if pixel[3] >= 64]
    if not opaque_rgb:
        return "unknown"
    sample = Image.new("RGB", (len(opaque_rgb), 1))
    sample.putdata(opaque_rgb)
    colors = sample.quantize(colors=5).convert("RGB").getcolors(maxcolors=5) or []
    _, dominant = max(colors, key=lambda item: item[0])
    return min(NAMED_COLORS, key=lambda name: sum((dominant[i] - NAMED_COLORS[name][i]) ** 2 for i in range(3)))
