# Tatiana VkusVill Cart Action

Это не Telegram-бот.

Это технический API-модуль для ChatGPT Project: ты обсуждаешь меню прямо в ChatGPT, а когда говоришь «собирай корзину», ChatGPT вызывает этот API и получает ссылку на корзину ВкусВилла.

## Целевой сценарий

```text
Татьяна в ChatGPT Project:
Составь меню на 3 дня. Дома рис, яйца, лосось.

ChatGPT:
Меню + список покупок.

Татьяна:
Собирай корзину.

ChatGPT → Action API:
POST /create-vkusvill-cart

Action API → VkusVill MCP:
создаёт корзину.

ChatGPT:
Ссылка на корзину: https://vkusvill.ru/?share_basket=...
```

## Что делает этот сервис

- принимает утверждённый список покупок;
- ищет товары во ВкусВилле;
- собирает уникальные `xml_id`;
- вызывает `vkusvill_cart_link_create`;
- возвращает ссылку, добавленные товары и ненайденные позиции.

## Что НЕ делает этот сервис

- не ведёт диалог;
- не составляет меню;
- не хранит семейную память;
- не работает через Telegram;
- не использует OpenAI API.

Всё мышление и обсуждение меню остаётся в ChatGPT Project.

## API

### Health

```http
GET /health
```

### Создать корзину

```http
POST /create-vkusvill-cart
Content-Type: application/json
```

Пример:

```json
{
  "shopping_list_text": "Яйца — 1 упаковка\nКабачки — 1 кг\nБрокколи — 1 упаковка"
}
```

Ответ:

```json
{
  "ok": true,
  "text": "Ссылка на корзину:\nhttps://vkusvill.ru/?share_basket=...",
  "cart_link": "https://vkusvill.ru/?share_basket=...",
  "added_items": ["Яйца — 1", "Кабачки — 1"],
  "not_found": []
}
```

## OpenAPI для ChatGPT Actions

Файл:

```text
openapi.yaml
```

В нём описан endpoint:

```text
/create-vkusvill-cart
```

## Локальный запуск для теста

```bash
cd tatiana-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

`.env`:

```env
VKUSVILL_MCP_URL=https://mcp001.vkusvill.ru/mcp
```

## Проверка

```bash
curl -X POST http://localhost:8000/create-vkusvill-cart \
  -H "Content-Type: application/json" \
  -d '{"shopping_list_text":"Яйца — 1 упаковка\nКабачки — 1 кг"}'
```
