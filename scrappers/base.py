from abc import ABC, abstractmethod
from camoufox.sync_api import Camoufox
from models.result import ReturnResult


class BaseScraper(ABC):
    """
    Абстрактный базовый класс для всех источников данных (веб-парсеры, API-клиенты).
    Определяет общий интерфейс для поиска.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, query: str) -> list[ReturnResult]:
        """
        Запускает сбор данных. Должен быть переопределен во всех дочерних классах.
        """
        pass


class BaseBrowserScraper(BaseScraper, ABC):
    """
    Специализированный базовый класс для парсеров, требующих браузер Camoufox.
    Инкапсулирует запуск браузера, проставление источника, логирование и обработку ошибок.
    """

    def run(self, query: str) -> list[ReturnResult]:
        print(f"[{self.name}] запуск браузерного скраппинга для запроса: '{query}'")
        try:
            with Camoufox(headless=True) as browser:
                raw_results = self.scrape(query, browser)

            # Проставляем источник для каждого товара
            tagged_results = []
            for item in raw_results:
                item.source = self.name
                tagged_results.append(item)

            print(f"[{self.name}] скраппинг успешно завершен. Собрано: {len(tagged_results)} позиций.")
            return tagged_results
        except Exception as exc:
            print(f"[{self.name}] критическая ошибка при скраппинге: {exc}")
            return []

    @abstractmethod
    def scrape(self, query: str, browser) -> list[ReturnResult]:
        """
        Непосредственная логика парсинга конкретной площадки через браузер.
        """
        pass
