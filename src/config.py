import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")


def require_api_key():
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not found. Set it in your .env file or environment variables."
        )
