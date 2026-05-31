from config import settings
from .filter import BaseFilter
from .transformer_filter import TransformerFilter
from .openai_filter import OpenAIFilter


def get_active_filter() -> BaseFilter:
    """
    Фабричный метод для инстанцирования активного фильтра.
    Выбирает класс фильтра на основе конфигурации AI_FILTER_TYPE.
    """
    if settings.AI_FILTER_TYPE == "openai":
        print("[AI System] Инициализация OpenAI LLM фильтра...")
        return OpenAIFilter()
    else:
        print("[AI System] Инициализация локального ML Transformer фильтра...")
        return TransformerFilter()


# Инициализируем активный инстанс фильтра заранее (при импорте)
active_filter = get_active_filter()
