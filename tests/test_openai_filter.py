import unittest
from unittest.mock import MagicMock, patch

from models.result import ReturnResult
from tools.ai_filter.openai_filter import OpenAIFilter


class TestOpenAIFilter(unittest.TestCase):
    def setUp(self):
        self.items = [
            ReturnResult(
                title="Фильтр John Deere RE504836",
                link="http://example.com/1",
                price=5000,
                description="Оригинальный фильтр",
            ),
            ReturnResult(
                title="Случайный чехол для телефона",
                link="http://example.com/2",
                price=300,
                description="Красивый силиконовый чехол",
            ),
        ]
        self.filter = OpenAIFilter()

    @patch("tools.ai_filter.openai_filter.ai_client")
    def test_openai_filter_success(self, mock_client):
        # Мокаем успешный ответ модели
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"title": "Фильтр John Deere RE504836", "link": "http://example.com/1", "price": 5000, "description": "Оригинальный фильтр", "photo_url": null, "source": ""}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        filtered = self.filter.filter(self.items)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Фильтр John Deere RE504836")

    @patch("tools.ai_filter.openai_filter.ai_client")
    def test_openai_filter_empty_or_malformed_response_fallback(self, mock_client):
        # Мокаем пустой или некорректный ответ от API
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=""))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Должен сработать fallback и вернуть исходный список
        filtered = self.filter.filter(self.items)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered, self.items)

    @patch("tools.ai_filter.openai_filter.ai_client")
    def test_openai_filter_api_error_fallback(self, mock_client):
        # Мокаем падение API с исключением
        mock_client.chat.completions.create.side_effect = Exception("API Connection Timeout")

        # При ошибке API также должен сработать fallback и вернуть исходные элементы
        filtered = self.filter.filter(self.items)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered, self.items)


if __name__ == "__main__":
    unittest.main()
