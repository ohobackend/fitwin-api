from io import BytesIO
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import StreamingResponse
from app.core.config import get_settings
from app.schemas.commerce import CartAddRequest, CartAddResponse, ProductLinkResponse
from app.services.commerce import build_product_url, create_product_qr

router = APIRouter(tags=["commerce"])
ProductId = Annotated[str, Path(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")]

def authenticated_user_id(request: Request) -> UUID:
    try:
        return UUID(str(request.state.user["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token subject must be a user UUID") from exc

@router.get("/products/{product_id}/link", response_model=ProductLinkResponse)
async def get_product_link(product_id: ProductId) -> ProductLinkResponse:
    return ProductLinkResponse(product_id=product_id, url=build_product_url(product_id))

@router.get(
    "/products/{product_id}/qr",
    response_class=StreamingResponse,
    responses={200: {"content": {"image/png": {}}, "description": "Product link QR code"}},
)
async def get_product_qr(product_id: ProductId) -> StreamingResponse:
    png = create_product_qr(product_id)
    return StreamingResponse(
        BytesIO(png), media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="product-{product_id}-qr.png"',
            "Cache-Control": "public, max-age=3600",
        },
    )

@router.post("/cart/add", response_model=CartAddResponse, status_code=201)
async def add_to_cart(payload: CartAddRequest, request: Request) -> CartAddResponse:
    user_id = authenticated_user_id(request)
    checkout_base = get_settings().product_store_base_url.rsplit("/products", 1)[0]
    return CartAddResponse(
        cart_item_id=uuid4(), user_id=user_id, product_id=payload.product_id,
        quantity=payload.quantity, garment_id=payload.garment_id,
        checkout_url=f"{checkout_base}/cart", mock=True,
    )
