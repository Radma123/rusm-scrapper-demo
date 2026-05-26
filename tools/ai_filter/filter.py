from .prompt import PROMPT

from config import MODEL, ai_client
from models.result import ReturnResult

def ai_filter(items: list[ReturnResult]) -> list[ReturnResult]:
    """Использует AI для определения релевантности позициий."""
    if not items:
        return []

    # Преобразуем список в текст для AI
    input_text = "\n".join(f"{i.model_dump()}" for i in items)

    # Формируем запрос к AI
    response = ai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": input_text},
        ],
        max_tokens=2048,
    )

    # Получаем отфильтрованный текст от AI
    filtered_text = response.choices[0].message.content.strip()

    # Преобразуем обратно в список ReturnResult
    filtered_items = []
    for line in filtered_text.splitlines():
        try:
            item = ReturnResult.model_validate_json(line)
            filtered_items.append(item)
        except Exception as exc:
            print(f"Ошибка при парсинге строки от AI: {exc}\nСтрока: {line}")

    print(f"AI отфильтровал {len(items)} позиций до {len(filtered_items)} релевантных.")

    return filtered_items