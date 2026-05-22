from typing import Any, Dict, List, Optional

import requests

from config import RUSMARKET_API_URL, RUSMARKET_TIMEOUT

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def get_products_availability(
    products: List[Dict[str, Any]],
    sources: Optional[List[str]] = None,
    force_refresh: bool = False,
    *,
    api_url: str | None = None,
    timeout: float | None = None,
) -> List[Dict[str, Any]]:
    """
    Вход:
        products = [{"serial": "...", "count": 2}, ...]

    Выход:
        [
          {
            "serial": "02-103781",
            "name": "Название товара",
            "requested_count": 1,
            "local": {...} | None,
            "external": {
              "cnhi_parts": {...},
              "service2": {...}
            }
          }
        ]
    """
    if not products:
        raise ValueError("products must be a non-empty list")

    if sources is None:
        sources = ["local", "external"]

    url = api_url or RUSMARKET_API_URL
    request_timeout = timeout if timeout is not None else RUSMARKET_TIMEOUT

    payload: Dict[str, Any] = {
        "products": products,
        "sources": sources,
        "force_refresh": force_refresh,
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": _DEFAULT_USER_AGENT,
        },
        timeout=request_timeout,
    )

    if response.status_code == 403:
        raise PermissionError("Rusmarket API: доступ запрещён (bot User-Agent?)")
    if response.status_code == 400:
        detail = response.text[:500]
        raise ValueError(f"Rusmarket API: неверный запрос — {detail}")
    if not response.ok:
        detail = response.text[:500]
        raise RuntimeError(
            f"Rusmarket API: HTTP {response.status_code} — {detail}"
        )

    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("Rusmarket API: ответ не является JSON-объектом")

    data = body.get("data")
    if not isinstance(data, list):
        raise RuntimeError(
            f"Rusmarket API: поле data отсутствует или не список: {body!r}"
        )

    return data
