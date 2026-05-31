import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models.result import ReturnResult
from tools.ai_filter.filter import BaseFilter

# Маленькая multilingual модель
model = SentenceTransformer("intfloat/multilingual-e5-small")

# Эталон "что такое запчасть"
REFERENCE_TEXT = """
запчасти фильтр подшипник гидравлика
ремень case cnh new holland case
артикул oem двигатель сельхозтехника
"""

reference_embedding = model.encode([REFERENCE_TEXT])


def is_relevant(text: str, threshold: float = 0.8) -> bool:
    """Проверяет релевантность текста запчастям по косинусному сходству векторов."""
    emb = model.encode([text])
    similarity = cosine_similarity(emb, reference_embedding)[0][0]
    return similarity >= threshold


def regex_filter(item: ReturnResult) -> bool:
    """Фильтр на содержание каталожного номера в названии или описании."""
    pattern = r"\b[A-Z0-9\-]{5,}\b"
    text = f"{item.title} {item.description or ''}"
    return bool(re.search(pattern, text))


class TransformerFilter(BaseFilter):
    """Фильтр товаров на основе семантического сходства (SentenceTransformer) и артикулов."""

    def __init__(self):
        super().__init__(name="transformer")

    def filter(self, items: list[ReturnResult]) -> list[ReturnResult]:
        filtered = []

        for item in items:
            combined_text = f"{item.title} {item.description or ''}"
            # Оставляем, если это наш Rusmarket, подходит по регулярке артикула или семантически релевантно
            if item.source == "rusmarket" or regex_filter(item) or is_relevant(combined_text):
                filtered.append(item)
            else:
                print(f"[Transformer Filter] Исключил позицию: {item.title} (ссылка: {item.link})")

        print(f"[Transformer Filter] Отобрал {len(filtered)} из {len(items)} позиций.")
        return filtered
