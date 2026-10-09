import os
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")
IBM_STT_API_KEY = os.getenv("IBM_STT_API_KEY", "")
IBM_STT_URL = os.getenv("IBM_STT_URL", "")
IBM_STT_MODEL = os.getenv("IBM_STT_MODEL", "en-US_Multimedia")

DB_PATH = os.getenv("DB_PATH", "interview_trainer.db")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

RAG_CHUNK_SIZE = 300        # tokens (approx words)
RAG_TOP_K = 3               # chunks to retrieve
MAX_PREVIOUS_QUESTIONS = 5  # avoid repetition
FOCUS_MAX_FRAME_BYTES = int(os.getenv("FOCUS_MAX_FRAME_BYTES", "2000000"))
FOCUS_SMOOTHING = float(os.getenv("FOCUS_SMOOTHING", "0.25"))
