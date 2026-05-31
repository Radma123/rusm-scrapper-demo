import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from models.result import ReturnResult


class FilterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._orig_sentence_transformers = sys.modules.get('sentence_transformers')
        fake_sentence_transformers = types.ModuleType('sentence_transformers')
        cls.mock_model = MagicMock()
        cls.mock_model.encode.return_value = np.array([[0.0, 0.0]])
        fake_sentence_transformers.SentenceTransformer = MagicMock(return_value=cls.mock_model)
        sys.modules['sentence_transformers'] = fake_sentence_transformers

        cls.transformer_mod = importlib.import_module('tools.ai_filter.transformer_filter')

    @classmethod
    def tearDownClass(cls):
        if cls._orig_sentence_transformers is not None:
            sys.modules['sentence_transformers'] = cls._orig_sentence_transformers
        else:
            sys.modules.pop('sentence_transformers', None)

    def test_regex_filter_accepts_catalog_number_in_title(self):
        item = ReturnResult(
            title='Фильтр 12345-ABC',
            description='Нужная запчасть',
            link='http://example.com',
            price=100,
        )

        self.assertTrue(self.transformer_mod.regex_filter(item))

    def test_regex_filter_accepts_catalog_number_in_description(self):
        item = ReturnResult(
            title='Неинформативный заголовок',
            description='Артикул: 12AB-34567',
            link='http://example.com',
            price=100,
        )

        self.assertTrue(self.transformer_mod.regex_filter(item))

    def test_regex_filter_rejects_non_catalog_text(self):
        item = ReturnResult(
            title='Обычная деталь',
            description='Нет артикулов и каталожных номеров',
            link='http://example.com',
            price=100,
        )

        self.assertFalse(self.transformer_mod.regex_filter(item))

    def test_ai_filter_keeps_relevant_or_regex_matched_items(self):
        item_relevant = ReturnResult(
            title='Фильтр масла для сельхозтехники',
            description='Качественная запчасть для трактора',
            link='http://example.com/relevant',
            price=150,
        )
        item_with_article = ReturnResult(
            title='Запчасть 54321-XYZ',
            description='Не совсем релевантное описание',
            link='http://example.com/article',
            price=200,
        )
        item_irrelevant = ReturnResult(
            title='Несвязанный товар',
            description='Описание без номера и ключевых слов',
            link='http://example.com/irrelevant',
            price=50,
        )

        # Создаем инстанс фильтра
        tf = self.transformer_mod.TransformerFilter()

        with patch.object(self.transformer_mod, 'is_relevant', side_effect=[True, False, False]):
            filtered = tf.filter([
                item_relevant,
                item_with_article,
                item_irrelevant,
            ])

        self.assertEqual(filtered, [item_relevant, item_with_article])
        self.assertNotIn(item_irrelevant, filtered)


if __name__ == '__main__':
    unittest.main()
