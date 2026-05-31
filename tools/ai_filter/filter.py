from abc import ABC, abstractmethod
from models.result import ReturnResult


class BaseFilter(ABC):
    """
    Базовый абстрактный класс для всех фильтров товаров.
    Все конкретные реализации фильтров должны наследоваться от него.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def filter(self, items: list[ReturnResult]) -> list[ReturnResult]:
        """
        Фильтрует список товаров.
        Метод должен быть переопределен в дочерних классах.
        """
        pass