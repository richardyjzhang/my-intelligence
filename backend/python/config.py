import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

MINERU_TOKEN = os.getenv("MINERU_TOKEN", "")
MINERU_MODEL_VERSION = os.getenv("MINERU_MODEL_VERSION", "vlm")

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "D:/Code/AI-Projects/my-intelligence/data/chroma")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

FILE_ROOT_PATH = os.getenv("FILE_ROOT_PATH", "D:/Code/AI-Projects/my-intelligence/data")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3:8b")

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
