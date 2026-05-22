import re

from pydantic import BaseModel

_PRICE_DIGITS_RE = re.compile(r"\d+")


def parse_price_rub(value: str | int | float) -> int:
    """Цена в рублях: число или строка с ₽, пробелами, неразрывными пробелами."""
    if isinstance(value, bool):
        raise TypeError("price must be numeric")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).replace("\u00a0", " ").strip()
    digits = "".join(_PRICE_DIGITS_RE.findall(text))
    if not digits:
        raise ValueError(f"Не удалось распарсить цену: {value!r}")
    return int(digits)


_NO_PRICE_PHRASES = (
    "отсутствует",
    "договорн",
    "бесплатно",
    "цена не указана",
    "звоните",
    "по запросу",
)


def price_text_unavailable(text: str) -> bool:
    lower = text.strip().lower()
    return any(p in lower for p in _NO_PRICE_PHRASES)


def normalize_photo_url(value: str | None) -> str | None:
    if not value:
        return None
    url = value.strip()
    if url in ("Нет фото", "Нет ссылки") or "data:image" in url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    if not url.startswith(("http://", "https://")):
        return None
    if "," in url:
        url = url.split(",")[0].strip().split(" ")[0]
    return url


class ReturnResult(BaseModel):
    title: str
    link: str
    price: int  # в рублях, без символов и пробелов
    description: str | None = None
    photo_url: str | None = None
    source: str = ""  # avito | ozon | autopiter | rusmarket