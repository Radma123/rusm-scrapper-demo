from concurrent.futures import ThreadPoolExecutor, as_completed
from models.result import ReturnResult
from scrappers.base import BaseScraper
from tools.ai_filter.filter import BaseFilter
from services.pipeline import (
    Pipeline,
    PriceSanitizer,
    PhotoNormalizer,
    AIFiltrator,
    PriceSorter,
)


class SearchService:
    """
    Сервис бизнес-логики для параллельного поиска запчастей на всех площадках.
    Спроектирован на основе паттернов 'Стратегия' (Strategy) и 'Конвейер' (Pipeline).
    Полностью независим от конкретных реализаций парсеров и фильтров (Dependency Injection).
    """

    def __init__(self, scrapers: list[BaseScraper], ai_filter: BaseFilter):
        self.scrapers = scrapers
        
        # Конфигурируем конвейер постобработки результатов
        self.pipeline = Pipeline([
            PriceSanitizer(),
            PhotoNormalizer(),
            AIFiltrator(ai_filter),
            PriceSorter()
        ])

    def search_all(self, query: str) -> list[ReturnResult]:
        """Параллельно опрашивает все зарегистрированные стратегии скраппинга."""
        q = query.strip()
        if not q:
            return []

        combined: list[ReturnResult] = []

        # Запускаем все стратегии параллельно в пуле потоков
        with ThreadPoolExecutor(max_workers=len(self.scrapers)) as pool:
            futures = {pool.submit(scraper.run, q): scraper.name for scraper in self.scrapers}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    chunk = future.result()
                    combined.extend(chunk)
                    print(f"[{name}] поток завершен. Получено: {len(chunk)} позиций.")
                except Exception as exc:
                    print(f"[{name}] критическая ошибка выполнения потока: {exc}")

        # Пропускаем сырые результаты через конвейер постобработки
        return self.pipeline.execute(combined)
