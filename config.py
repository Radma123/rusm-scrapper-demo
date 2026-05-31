from pathlib import Path
from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """
    Класс настроек приложения с использованием Pydantic Settings.
    Автоматически загружает переменные из .env файла и валидирует типы.
    """

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Rusmarket ---
    RUSMARKET_API_URL: str
    RUSMARKET_TIMEOUT: float

    # --- FastAPI Server ---
    API_HOST: str
    API_PORT: int

    # --- AI Filter settings ---
    HERMES_API_KEY: str
    HERMES_BASE_URL: str
    MODEL: str
    
    # "transformer" (ML sentence_transformers) или "openai" (OpenAI LLM)
    AI_FILTER_TYPE: str


# Инициализируем настройки
settings = Settings()



# Глобальный клиент OpenAI
ai_client = OpenAI(
    base_url=settings.HERMES_BASE_URL,
    api_key=settings.HERMES_API_KEY
)
