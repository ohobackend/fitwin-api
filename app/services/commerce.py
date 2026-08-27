from functools import lru_cache
from io import BytesIO
from urllib.parse import quote
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from app.core.config import get_settings

def build_product_url(product_id: str) -> str:
    base_url = get_settings().product_store_base_url.rstrip("/")
    return f"{base_url}/{quote(product_id, safe='')}"

@lru_cache(maxsize=256)
def create_product_qr(product_id: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(build_product_url(product_id))
    qr.make(fit=True)
    image = qr.make_image(fill_color="#111111", back_color="#ffffff")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
