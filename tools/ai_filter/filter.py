from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models.result import ReturnResult

# маленькая multilingual модель
model = SentenceTransformer(
    "intfloat/multilingual-e5-small"
)

# эталон "что такое запчасть"
REFERENCE_TEXT = """
запчасти фильтр подшипник гидравлика
ремень case cnh new holland case
артикул oem двигатель сельхозтехника
"""

reference_embedding = model.encode([REFERENCE_TEXT])


def is_relevant(text: str, threshold: float = 0.8) -> bool:
    emb = model.encode([text])

    similarity = cosine_similarity(
        emb,
        reference_embedding
    )[0][0]

    return similarity >= threshold

def regex_filter(item: ReturnResult) -> bool:
    """Фильтр на содерждение каталожного номера в названии или описании."""
    import re

    # простой паттерн для поиска артикулов (можно улучшить)
    pattern = r"\b[A-Z0-9\-]{5,}\b"

    text = f"{item.title} {item.description or ''}"
    return bool(re.search(pattern, text))


def ai_filter(items: list[ReturnResult]) -> list[ReturnResult]:
    filtered = []

    for item in items:
        combined_text = f"{item.title} {item.description or ''}"
        if item.source == "rusmarket" or is_relevant(combined_text):
            filtered.append(item)
        else:
            print(f"AI фильтр исключил позицию: {item.title} (ссылка: {item.link})")

    print(f"AI фильтр отобрал {len(filtered)} из {len(items)} позиций.")

    return filtered