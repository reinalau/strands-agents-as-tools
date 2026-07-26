import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:e2b-it-qat")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
