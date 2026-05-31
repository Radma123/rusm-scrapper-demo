from .prompt import PROMPT
from config import settings, ai_client
from models.result import ReturnResult
from tools.ai_filter.filter import BaseFilter


class OpenAIFilter(BaseFilter):
    """Фильтр товаров, использующий внешнюю языковую модель (OpenAI API)."""

    def __init__(self):
        super().__init__(name="openai")

    def filter(self, items: list[ReturnResult]) -> list[ReturnResult]:
        if not items:
            return []

        try:
            # Преобразуем список в текст (JSON строки) для передачи модели
            input_text = "\n".join(f"{i.model_dump()}" for i in items)

            # Формируем запрос к AI
            response = ai_client.chat.completions.create(
                model=settings.MODEL,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": input_text},
                ],
                max_tokens=2048,
                temperature=0.0,
            )

            # Получаем отфильтрованный текст
            filtered_text = response.choices[0].message.content.strip()

            # Преобразуем обратно в список ReturnResult
            filtered_items = []
            for line in filtered_text.splitlines():
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    item = ReturnResult.model_validate_json(line_str)
                    filtered_items.append(item)
                except Exception as exc:
                    print(f"[OpenAI Filter] Ошибка парсинга строки от AI: {exc}. Строка: {line_str}")

            if not filtered_items:
                print("[OpenAI Filter] Внимание: пустой ответ от AI, возвращаем оригинальные элементы.")
                return items

            print(f"[OpenAI Filter] Отфильтровал {len(items)} позиций до {len(filtered_items)} релевантных.")
            return filtered_items

        except Exception as exc:
            print(f"[OpenAI Filter] Критическая ошибка при вызове OpenAI API: {exc}. Возвращаем все элементы.")
            return items
