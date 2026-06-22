from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .config import VKUSVILL_MCP_URL
from .vkusvill import create_cart_from_text

app = FastAPI(
    title="Tatiana VkusVill Cart Action",
    description="ChatGPT Action API: creates a VkusVill cart link from an approved shopping list.",
    version="1.0.0",
)


class ShoppingItem(BaseModel):
    name: str = Field(..., description="Product name in Russian, for example: яйца, кабачки, брокколи")
    quantity: Optional[str] = Field(None, description="Human quantity, for example: 1 упаковка, 1 кг, 2 штуки")
    notes: Optional[str] = Field(None, description="Optional constraints or replacement notes")


class CreateCartRequest(BaseModel):
    shopping_list_text: Optional[str] = Field(
        None,
        description="Approved shopping list as plain Russian text. Use this when ChatGPT already has a formatted list.",
    )
    items: Optional[List[ShoppingItem]] = Field(
        None,
        description="Structured shopping list. Use this when items are available as objects.",
    )


class CreateCartResponse(BaseModel):
    ok: bool
    text: str
    cart_link: Optional[str] = None
    added_items: List[str] = []
    not_found: List[str] = []


def _items_to_text(items: Optional[List[ShoppingItem]]) -> str:
    if not items:
        return ""
    lines = []
    for item in items:
        line = item.name
        if item.quantity:
            line += f" — {item.quantity}"
        if item.notes:
            line += f" ({item.notes})"
        lines.append(line)
    return "\n".join(lines)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "tatiana-vkusvill-cart-action", "mcp_url": VKUSVILL_MCP_URL}


@app.post("/create-vkusvill-cart", response_model=CreateCartResponse)
async def create_vkusvill_cart(payload: CreateCartRequest) -> CreateCartResponse:
    shopping_text = (payload.shopping_list_text or "").strip() or _items_to_text(payload.items)
    if not shopping_text:
        return CreateCartResponse(
            ok=False,
            text="Нет списка покупок. Сначала утверди меню и список продуктов, потом вызывай создание корзины.",
        )

    result = await create_cart_from_text(shopping_text)
    return CreateCartResponse(
        ok=bool(result.get("ok")),
        text=result.get("text") or "Корзина обработана, но текст ответа не сформирован.",
        cart_link=result.get("cart_link"),
        added_items=result.get("added_items") or [],
        not_found=result.get("not_found") or [],
    )
