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

# Embedding（OpenAI 兼容协议）
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL",
                               os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# AI 对话（OpenAI 兼容协议）
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "4096"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))

# CHAT_MODEL: 兼容旧配置，未设置时取 AI_MODEL
CHAT_MODEL = os.getenv("CHAT_MODEL", "") or AI_MODEL or "qwen3:8b"

FILE_ROOT_PATH = os.getenv("FILE_ROOT_PATH", "D:/Code/AI-Projects/my-intelligence/data")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
