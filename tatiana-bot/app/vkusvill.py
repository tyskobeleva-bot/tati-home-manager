import json
import re
from typing import Any, Dict, List, Optional

from .config import VKUSVILL_MCP_URL


def _extract_jsonish(value: Any) -> Any:
    """Best-effort conversion of MCP tool content to Python objects.

    MCP returns content as a list of TextContent-like objects. The first version
    returned lists unchanged, so product search results were never parsed.
    """
    if isinstance(value, list):
        parsed = [_extract_jsonish(x) for x in value]
        if len(parsed) == 1:
            return parsed[0]
        return parsed
    if hasattr(value, "text"):
        value = value.text
    if isinstance(value, dict):
        return {k: _extract_jsonish(v) for k, v in value.items()}
    if not isinstance(value, str):
        return value
    text = value.strip()
    try:
        return json.loads(text)
    except Exception:
        return text


def _find_items(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        result = []
        for x in obj:
            if isinstance(x, dict) and ("xml_id" in x or "xmlId" in x or "id" in x):
                result.append(x)
            else:
                result.extend(_find_items(x))
        return result
    if isinstance(obj, dict):
        for key in ("items", "products", "result", "data", "goods", "records", "list"):
            if key in obj:
                found = _find_items(obj[key])
                if found:
                    return found
        if "xml_id" in obj or "xmlId" in obj or "id" in obj:
            return [obj]
    return []


def _clean_search_name(line: str) -> str:
    name = re.split(r"\s[—-]\s|:\s", line, maxsplit=1)[0].strip()
    name = re.sub(r"\b(куриные|куриное|свежие|свежий|упаковка|штуки|штук|кг|грамм|г)\b", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    return name or line.strip()


async def _call_tool(session, name: str, arguments: Dict[str, Any]) -> Any:
    result = await session.call_tool(name, arguments)
    content = getattr(result, "content", result)
    return _extract_jsonish(content)


async def create_cart_from_text(shopping_list_text: str) -> Dict[str, Any]:
    """Search VkusVill products one by one and create a basket link."""
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except Exception as e:
        raise RuntimeError("MCP SDK is not installed or changed its API") from e

    lines = [x.strip(" -•\t") for x in shopping_list_text.splitlines() if x.strip()]
    lines = [x for x in lines if len(x) > 2 and not x.lower().startswith(("что", "корзина", "список"))]

    products: List[Dict[str, Any]] = []
    added_items: List[str] = []
    not_found: List[str] = []
    used_xml: set[int] = set()

    async with streamablehttp_client(VKUSVILL_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for line in lines[:20]:
                name = _clean_search_name(line)
                if not name:
                    continue
                qty = _quantity_from_line(line)
                search = await _call_tool(
                    session,
                    "vkusvill_products_search",
                    {"q": name, "page": 1, "sort": "popularity", "vvonly": 0},
                )
                items = _find_items(search)
                chosen = None
                for item in items:
                    xml = item.get("xml_id") or item.get("xmlId")
                    if isinstance(xml, str) and xml.isdigit():
                        xml = int(xml)
                    if isinstance(xml, int) and xml > 0 and xml not in used_xml:
                        chosen = item
                        break
                if not chosen:
                    not_found.append(line)
                    continue

                xml_id = int(chosen.get("xml_id") or chosen.get("xmlId"))
                used_xml.add(xml_id)
                products.append({"xml_id": xml_id, "q": qty})
                added_items.append(f"{chosen.get('name') or chosen.get('title') or name} — {qty}")

            if not products:
                return {
                    "ok": False,
                    "text": "Не смогла найти товары для корзины. Пришли список короче и конкретнее.",
                    "cart_link": None,
                    "added_items": [],
                    "not_found": not_found,
                }
            cart = await _call_tool(session, "vkusvill_cart_link_create", {"products": products})

    link = _extract_link(cart)
    text = "Ссылка на корзину:\n" + (link or "ссылка не найдена в ответе ВкусВилла")
    text += "\n\nДобавленные товары:\n" + "\n".join(f"- {x}" for x in added_items)
    if not_found:
        text += "\n\nНе найдено:\n" + "\n".join(f"- {x}" for x in not_found)
    else:
        text += "\n\nВсе позиции найдены."
    text += "\n\nВажно: после выбора адреса доставки ВкусВилл может удалить недоступные позиции из корзины."
    return {
        "ok": True,
        "text": text,
        "cart_link": link,
        "added_items": added_items,
        "not_found": not_found,
        "raw": cart,
        "products": products,
    }


def _quantity_from_line(line: str) -> float:
    low = line.lower()
    m = re.search(r"(\d+[,.]?\d*)", low)
    if not m:
        return 1.0
    number = float(m.group(1).replace(",", "."))
    return max(0.01, min(40.0, number))


def _extract_link(obj: Any) -> Optional[str]:
    if isinstance(obj, str):
        m = re.search(r"https?://\S+", obj)
        return m.group(0) if m else None
    if isinstance(obj, list):
        for x in obj:
            link = _extract_link(x)
            if link:
                return link
    if isinstance(obj, dict):
        for key in ("url", "link", "cart_link", "share_url", "basket_url"):
            val = obj.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
        for val in obj.values():
            link = _extract_link(val)
            if link:
                return link
    return None
