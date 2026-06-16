import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
VKUSVILL_MCP_URL = os.getenv("VKUSVILL_MCP_URL", "https://mcp001.vkusvill.ru/mcp").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tati_home.db").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
ALLOWED_TELEGRAM_CHAT_ID = os.getenv("ALLOWED_TELEGRAM_CHAT_ID", "").strip()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
