import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")