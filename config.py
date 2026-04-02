import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ERP_API_KEY = os.getenv("ERP_API_KEY")
ERP_BASE_URL = os.getenv("ERP_BASE_URL")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY")
