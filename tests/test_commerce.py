from app.core.config import get_settings
from app.services.commerce import build_product_url, create_product_qr

def test_product_url_uses_configured_store_base() -> None:
    settings = get_settings()
    assert build_product_url("sku-100") == f"{settings.product_store_base_url}/sku-100"

def test_product_qr_is_png_and_cached() -> None:
    first = create_product_qr("sku-100")
    second = create_product_qr("sku-100")
    assert first.startswith(b"\x89PNG\r\n\x1a\n")
    assert first is second
