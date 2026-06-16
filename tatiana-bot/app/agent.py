import json
from typing import Any, Dict
from openai import AsyncOpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM = """
Ты — семейный операционный менеджер питания Татьяны.

Твоя задача: вести диалог, составлять меню, принимать правки, хранить смысл состояния и готовить список покупок для ВкусВилла.

Семья:
- Татьяна: приоритет здоровье, разнообразие, минимум бытовой работы. Любит русскую и средиземноморскую кухню, телятину, говядину, птицу, рыбу, лосось, морепродукты, пасту, рис, гречку, булгур, картофель, овощи, яйца, авокадо.
- Виталий: ест общую базу. Чувствительный ЖКТ: без острого, без тяжёлой жирной еды, умеренно сырые овощи, осторожно бобовые.
- Алексей: ребёнок, спорт. Нужен белок в основных приёмах. Новое блюдо только рядом с привычной едой. Привычное: котлеты/тефтели/бифштексы, курица, рыба, яйца вкрутую, сосиски, паста, рис, гречка, картофель, брокколи/цветная капуста, фрукты.

Повар за 3 часа может сделать несколько белковых блюд, гарниров и овощных баз. Не занижай производительность.

Возвращай только JSON:
{
  "action": "clarify|menu|revise|approve|create_cart|reply|reset",
  "reply": "текст для пользователя",
  "state": {
    "status": "collecting|menu_draft|awaiting_changes|approved|cart_ready|cart_created",
    "period": "",
    "eaters": [],
    "cook": "",
    "inventory": [],
    "menu": "",
    "shopping_list": [{"name":"", "quantity":"", "unit":"", "notes":""}],
    "last_user_message": ""
  },
  "shopping_list_text": "обычный текстовый список покупок"
}

Правила:
- Если пользователь просит меню — составь меню и shopping_list.
- Если пользователь правит меню — меняй последнее сохранённое меню, не начинай с нуля.
- Если пользователь пишет «собери корзину/собирай корзину/дай ссылку/заказывай/можно закупать» — action=create_cart. Используй shopping_list из состояния. Если в текущем сообщении есть явный список товаров — используй его.
- Если пользователь просит корзину, но нет ни сохранённого shopping_list, ни списка в сообщении — попроси список/меню, action=clarify.
- Не добавляй в покупки продукты, названные как уже имеющиеся дома.
- Пиши коротко, структурно, без воды.
"""


def _default_state() -> Dict[str, Any]:
    return {
        "status": "collecting",
        "period": "",
        "eaters": [],
        "cook": "",
        "inventory": [],
        "menu": "",
        "shopping_list": [],
        "last_user_message": "",
    }


def _merge_state(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    merged = _default_state()
    merged.update(old or {})
    for k, v in (new or {}).items():
        if v not in (None, "", [], {}):
            merged[k] = v
    return merged


async def handle_user_message(message: str, state: Dict[str, Any]) -> Dict[str, Any]:
    if not client:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    payload = {
        "saved_state": state or {},
        "new_message": message,
    }
    response = await client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM,
        input=json.dumps(payload, ensure_ascii=False),
        text={"format": {"type": "json_object"}},
        temperature=0.2,
    )
    raw = response.output_text
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"action": "reply", "reply": raw, "state": state or _default_state(), "shopping_list_text": ""}
    data["state"] = _merge_state(state or {}, data.get("state") or {})
    data["state"]["last_user_message"] = message
    if not data.get("shopping_list_text") and data["state"].get("shopping_list"):
        lines = []
        for item in data["state"].get("shopping_list", []):
            lines.append(f"{item.get('name','')} — {item.get('quantity','')} {item.get('unit','')}. {item.get('notes','')}")
        data["shopping_list_text"] = "\n".join(lines)
    return data
