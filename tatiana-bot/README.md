# Tatiana Bot

Личный Telegram-бот для семейного питания.

## Что умеет

- ведёт диалог про меню;
- помнит последнее меню и список покупок;
- принимает правки;
- по команде «собирай корзину» создаёт корзину ВкусВилла;
- возвращает ссылку в Telegram.

## Архитектура

```text
Telegram → FastAPI backend → OpenAI agent → SQLite state
                               ↓
                         VkusVill MCP → cart link
```

## Быстрый запуск локально

```bash
cd tatiana-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Заполни `.env`:

```env
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
VKUSVILL_MCP_URL=https://mcp001.vkusvill.ru/mcp
PUBLIC_BASE_URL=https://your-public-url
ALLOWED_TELEGRAM_CHAT_ID=
```

`ALLOWED_TELEGRAM_CHAT_ID` можно оставить пустым на тесте. Потом лучше поставить свой chat_id.

## Webhook Telegram

После деплоя вызови:

```bash
curl -X POST https://your-service.example.com/setup-webhook
```

## Команды в боте

Сброс памяти:

```text
/reset
```

Обычный сценарий:

```text
Составь меню на 3 дня. Повар завтра 3 часа. Дома рис, яйца, лосось.
```

Правка:

```text
Убери печень, добавь суп, рис уже есть.
```

Корзина:

```text
Собирай корзину
```

Или прямой список:

```text
Собери корзину: яйца — 1 упаковка, картофель — 1 кг, борщ — 2 упаковки
```

## Деплой на Render

1. Создай Web Service.
2. Подключи GitHub repository.
3. Root Directory: `tatiana-bot`.
4. Environment: Docker.
5. Add Environment Variables из `.env.example`.
6. Deploy.
7. После deploy выполни POST `/setup-webhook`.

## Важное про ВкусВилл

ВкусВилл пересчитывает наличие после выбора адреса доставки. Если товар исчез после выбора адреса, это не ошибка backend: нужно подобрать замену под конкретный адрес.
