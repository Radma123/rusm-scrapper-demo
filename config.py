import os
from pathlib import Path
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# --- Rusmarket portal ---
RUSMARKET_API_URL = os.getenv(
    "RUSMARKET_API_URL",
    "https://rusmarket.top/api/v1/products/availability",
)
RUSMARKET_TIMEOUT = float(os.getenv("RUSMARKET_TIMEOUT", "30"))


# --- HTTP API ---
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "6767"))


# ai
ai_client = OpenAI(base_url="https://hermes.ai.unturf.com/v1", api_key="56e8b753164e17ab9f7df285fabd2f0eaacbcaa9b17afb20")
MODEL = "adamo1139/Hermes-3-Llama-3.1-8B-FP8-Dynamic"
