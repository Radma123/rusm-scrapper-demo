from abc import ABC, abstractmethod
from models.result import ReturnResult
from models.helpers import normalize_photo_url
from tools.ai_filter.filter import BaseFilter


class ResultProcessor(ABC):
    """
    Абстрактный базовый класс для шага обработки результатов скраппинга.
    Реализует паттерн 'Конвейер' (Pipeline).
    """

    @abstractmethod
    def process(self, items: list[ReturnResult]) -> list[ReturnResult]:
        """Обрабатывает и модифицирует список товаров."""
        pass


class PriceSanitizer(ResultProcessor):
    """Шаг конвейера: отбраковывает товары с некорректной ценой (<= 0)."""

    def process(self, items: list[ReturnResult]) -> list[ReturnResult]:
        cleaned = [item for item in items if item.price > 0]
        return cleaned


class PhotoNormalizer(ResultProcessor):
    """Шаг конвейера: нормализует URL картинок товаров."""

    def process(self, items: list[ReturnResult]) -> list[ReturnResult]:
        normalized = []
        for item in items:
            photo = normalize_photo_url(item.photo_url)
            normalized.append(item.model_copy(update={"photo_url": photo}))
        return normalized


class AIFiltrator(ResultProcessor):
    """Шаг конвейера: выполняет интеллектуальную фильтрацию через переданный AI-фильтр."""

    def __init__(self, ai_filter: BaseFilter):
        self.ai_filter = ai_filter

    def process(self, items: list[ReturnResult]) -> list[ReturnResult]:
        return self.ai_filter.filter(items)


class PriceSorter(ResultProcessor):
    """Шаг конвейера: сортирует товары по возрастанию цены."""

    def process(self, items: list[ReturnResult]) -> list[ReturnResult]:
        return sorted(items, key=lambda r: r.price)


class Pipeline:
    """
    Управляющий класс конвейера обработки результатов.
    Последовательно запускает все зарегистрированные обработчики.
    """

    def __init__(self, processors: list[ResultProcessor]):
        self.processors = processors

    def execute(self, items: list[ReturnResult]) -> list[ReturnResult]:
        """Выполняет последовательную обработку конвейером."""
        current_items = items
        for processor in self.processors:
            current_items = processor.process(current_items)
        return current_items
