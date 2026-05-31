import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from models.result import ReturnResult


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("RusM Scrapper", response.text)

    @patch("main.search_service.search_all")
    def test_search_endpoint_success(self, mock_search_all):
        # Настраиваем фейковый результат для search_all
        fake_result = [
            ReturnResult(
                title="Оригинальный фильтр CNH",
                link="http://example.com/cnh",
                price=3200,
                description="Подходит для New Holland",
                source="rusmarket",
            )
        ]
        mock_search_all.return_value = fake_result

        # Выполняем GET-запрос к API
        response = self.client.get("/api/search?q=CNH")
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON-ответ
        json_data = response.json()
        self.assertEqual(len(json_data), 1)
        self.assertEqual(json_data[0]["title"], "Оригинальный фильтр CNH")
        self.assertEqual(json_data[0]["price"], 3200)
        self.assertEqual(json_data[0]["source"], "rusmarket")

    @patch("main.search_service.search_all")
    def test_search_endpoint_error_handling(self, mock_search_all):
        # Настраиваем ошибку
        mock_search_all.side_effect = Exception("Scraping timeout")

        # Делаем запрос и проверяем, что FastAPI корректно возвращает 500 ошибку
        response = self.client.get("/api/search?q=error")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Scraping timeout")


if __name__ == "__main__":
    unittest.main()
