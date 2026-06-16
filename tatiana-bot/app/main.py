from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from . import state as state_store
from .agent import handle_user_message
from .config import ALLOWED_TELEGRAM_CHAT_ID, PUBLIC_BASE_URL, TELEGRAM_BOT_TOKEN, OPENAI_API_KEY
from .telegram import send_message, set_webhook
from .vkusvill import create_cart_from_text

app = FastAPI(title="Tatiana Bot")


@app.on_event("startup")
async def startup() -> None:
    state_store.init_db()


@app.get("/health")
async def health() -> dict:
    return {
        "ok": bool(TELEGRAM_BOT_TOKEN and OPENAI_API_KEY),
        "telegram_token": bool(TELEGRAM_BOT_TOKEN),
        "openai_key": bool(OPENAI_API_KEY),
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    update = await request.json()
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id") or "")
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return JSONResponse({"ok": True, "ignored": True})
    if ALLOWED_TELEGRAM_CHAT_ID and chat_id != ALLOWED_TELEGRAM_CHAT_ID:
        await send_message(chat_id, "Этот бот закрыт для личного использования.")
        return JSONResponse({"ok": True, "blocked": True})

    if text.lower() in {"/reset", "reset", "сброс"}:
        state_store.clear_state(chat_id)
        await send_message(chat_id, "Состояние сброшено. Можно начать заново.")
        return JSONResponse({"ok": True})

    saved = state_store.get_state(chat_id)
    try:
        agent_result = await handle_user_message(text, saved)
        new_state = agent_result.get("state") or saved
        action = agent_result.get("action")
        if action == "create_cart":
            shopping_list_text = agent_result.get("shopping_list_text") or ""
            if not shopping_list_text:
                reply = agent_result.get("reply") or "Нет списка покупок. Пришли меню или список продуктов."
            else:
                await send_message(chat_id, "Собираю корзину ВкусВилла…")
                cart = await create_cart_from_text(shopping_list_text)
                reply = cart.get("text") or "Корзина обработана, но текст ответа не сформирован."
                new_state["status"] = "cart_created" if cart.get("ok") else new_state.get("status", "cart_ready")
        else:
            reply = agent_result.get("reply") or "Не смогла сформировать ответ."
        state_store.save_state(chat_id, new_state)
        await send_message(chat_id, reply)
        return JSONResponse({"ok": True, "action": action})
    except Exception as e:
        await send_message(chat_id, f"Ошибка: {type(e).__name__}: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/setup-webhook")
async def setup_webhook() -> dict:
    if not PUBLIC_BASE_URL:
        raise HTTPException(status_code=400, detail="PUBLIC_BASE_URL is not configured")
    return await set_webhook(PUBLIC_BASE_URL)
