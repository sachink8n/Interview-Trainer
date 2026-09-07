import os
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")

DB_PATH = os.getenv("DB_PATH", "interview_trainer.db")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

RAG_CHUNK_SIZE = 300        # tokens (approx words)
RAG_TOP_K = 3               # chunks to retrieve
MAX_PREVIOUS_QUESTIONS = 5  # avoid repetition
