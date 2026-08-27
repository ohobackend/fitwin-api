from uuid import UUID
from pydantic import BaseModel, Field

class ProductLinkResponse(BaseModel):
    product_id: str
    url: str

class CartAddRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    quantity: int = Field(default=1, ge=1, le=99)
    garment_id: UUID | None = None

class CartAddResponse(BaseModel):
    cart_item_id: UUID
    user_id: UUID
    product_id: str
    quantity: int
    garment_id: UUID | None
    checkout_url: str
    mock: bool = True
