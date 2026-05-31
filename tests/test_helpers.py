import unittest

from models.helpers import (
    normalize_photo_url,
    parse_price_rub,
    price_text_unavailable,
)


class TestHelpers(unittest.TestCase):
    def test_parse_price_rub_integers_and_floats(self):
        self.assertEqual(parse_price_rub(123), 123)
        self.assertEqual(parse_price_rub(456.78), 456)

    def test_parse_price_rub_strings(self):
        self.assertEqual(parse_price_rub("1 250 ₽"), 1250)
        self.assertEqual(parse_price_rub("12\u00a0500 руб"), 12500)
        self.assertEqual(parse_price_rub("  999  "), 999)

    def test_parse_price_rub_invalid(self):
        with self.assertRaises(TypeError):
            parse_price_rub(True)
        with self.assertRaises(ValueError):
            parse_price_rub("цена договорная")

    def test_price_text_unavailable(self):
        self.assertTrue(price_text_unavailable("отсутствует"))
        self.assertTrue(price_text_unavailable("Цена по запросу"))
        self.assertTrue(price_text_unavailable("бесплатно"))
        self.assertFalse(price_text_unavailable("1500 руб"))

    def test_normalize_photo_url(self):
        self.assertEqual(
            normalize_photo_url("http://example.com/image.jpg"),
            "http://example.com/image.jpg",
        )
        self.assertEqual(
            normalize_photo_url("//cdn.example.com/pic.png"),
            "https://cdn.example.com/pic.png",
        )
        self.assertEqual(
            normalize_photo_url("http://img.com/1.jpg, http://img.com/2.jpg 2x"),
            "http://img.com/1.jpg",
        )
        self.assertIsNone(normalize_photo_url("Нет фото"))
        self.assertIsNone(normalize_photo_url("data:image/png;base64,..."))
        self.assertIsNone(normalize_photo_url(""))


if __name__ == "__main__":
    unittest.main()
