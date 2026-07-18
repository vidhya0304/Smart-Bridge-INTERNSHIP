import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Server Config
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# AI Models Configuration
is_on_render = os.getenv("RENDER", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DISABLE_LOCAL_T5 = os.getenv("DISABLE_LOCAL_T5", "true" if is_on_render else "false").lower() == "true"
LOCAL_T5_MODEL = os.getenv("LOCAL_T5_MODEL", "MBZUAI/LaMini-Flan-T5-248M")


# Directory Config
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure templates and static directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "css").mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(exist_ok=True)
(STATIC_DIR / "images").mkdir(exist_ok=True)
