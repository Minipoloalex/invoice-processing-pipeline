import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ERP_API_KEY = os.getenv("ERP_API_KEY")
ERP_BASE_URL = os.getenv("ERP_BASE_URL", "http://localhost:8000/api/erp")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
DATABASE_PATH = os.getenv("DATABASE_PATH", "invoices.db")
