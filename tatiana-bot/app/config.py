import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VKUSVILL_MCP_URL = os.getenv("VKUSVILL_MCP_URL", "https://mcp001.vkusvill.ru/mcp").strip()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
