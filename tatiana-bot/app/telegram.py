import httpx
from .config import TELEGRAM_BOT_TOKEN

API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_message(chat_id: str | int, text: str) -> None:
    if not text:
        text = "Пустой ответ. Это ошибка сценария: не сформирован текст для Telegram."
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or [text]
    async with httpx.AsyncClient(timeout=30) as client:
        for chunk in chunks:
            await client.post(
                f"{API}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": False},
            )


async def set_webhook(public_base_url: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API}/setWebhook", json={"url": f"{public_base_url}/telegram/webhook"})
        r.raise_for_status()
        return r.json()
