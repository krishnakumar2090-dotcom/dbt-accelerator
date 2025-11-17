import os
from dotenv import load_dotenv

def load_env():
    """Load Azure OpenAI environment variables."""
    load_dotenv()
    INCUBATOR_KEY = os.getenv("INCUBATOR_KEY")
    INCUBATOR_ENDPOINT = os.getenv("INCUBATOR_ENDPOINT")
    API_VERSION = os.getenv("API_VERSION", "2024-10-01")

    if not INCUBATOR_KEY or not INCUBATOR_ENDPOINT:
        raise ValueError("❌ Missing Azure environment variables. Check your .env file.")

    return INCUBATOR_KEY, INCUBATOR_ENDPOINT, API_VERSION
