from api.rusmarket import get_products_availability
from api.rusmarket_convert import availability_to_results
from models import ReturnResult
from scrappers.base import BaseScraper


class RusmarketScraper(BaseScraper):
    """
    API-клиент для Rusmarket.
    Интегрирован как стратегия (Scraper) в общий полиморфный список.
    """

    def __init__(self):
        super().__init__(name="rusmarket")

    def run(self, query: str) -> list[ReturnResult]:
        serial = query.strip()
        products = [{"serial": serial, "count": 1}]
        print(f"[{self.name}] запуск API-запроса availability для артикула: '{serial}'")
        try:
            data = get_products_availability(products=products)
            results = availability_to_results(data)
            
            # Проставляем источник для Rusmarket на случай, если аналоги содержат другое имя
            tagged_results = []
            for item in results:
                item.source = self.name
                tagged_results.append(item)
                
            print(f"[{self.name}] API-запрос успешно завершен. Получено: {len(tagged_results)} позиций.")
            return tagged_results
        except Exception as exc:
            print(f"[{self.name}] ошибка при выполнении API-запроса: {exc}")
            return []
