import random
from models import ReturnResult, normalize_photo_url, parse_price_rub, price_text_unavailable
from scrappers.base import BaseBrowserScraper

_PHOTO_SELECTORS = (
    '[data-marker="item-photo"] img',
    '[data-marker="slider-image"] img',
    'li[data-marker="slider-image/img"] img',
    'img[itemprop="image"]',
    'a[data-marker="item-photo"] img',
    '[class*="photo-slider"] img'
)


def _img_url_from_element(img_element) -> str | None:
    srcset = img_element.get_attribute("srcset")
    if srcset:
        first = srcset.split(",")[0].strip().split(" ")[0]
        url = normalize_photo_url(first)
        if url and "1x1" not in url.lower() and not url.startswith("data:"):
            return url

    for attr in ("data-src", "data-url", "data-lazy-src", "src"):
        raw = img_element.get_attribute(attr)
        if not raw:
            continue
        url = normalize_photo_url(raw)
        if url and "1x1" not in url.lower() and not url.startswith("data:"):
            return url
    return None


def _avito_photo_url(item) -> str | None:
    fallback: str | None = None
    for selector in _PHOTO_SELECTORS:
        for img in item.query_selector_all(selector):
            url = _img_url_from_element(img)
            if not url:
                continue
            lower = url.lower()
            if any(
                x in lower
                for x in ("/avatar", "/icon", "/logo", "sprite", "avatars.avito")
            ):
                continue
            if "img.avito.st" in lower or "avito.st/image" in lower:
                return url
            if fallback is None:
                fallback = url
    return fallback


class AvitoScraper(BaseBrowserScraper):
    """Парсер для торговой площадки Avito."""

    def __init__(self):
        super().__init__(name="avito")

    def scrape(self, query: str, browser) -> list[ReturnResult]:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        clean_query = query.replace(" ", "+")
        url = f"https://www.avito.ru/bashkortostan?q={clean_query}"

        try:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print("[avito] страница загружена. Ожидаем рендеринга товаров...")
                page.wait_for_timeout(random.uniform(2000, 3000))

                for _ in range(12):
                    try:
                        page.evaluate("window.scrollBy({top: 400, behavior: 'smooth'});")
                        page.wait_for_timeout(random.uniform(300, 600))
                    except:
                        break
            except Exception as e:
                print(f"[avito] ошибка загрузки страницы: {e}")
                return []

            try:
                page.wait_for_selector('div[data-marker="item"]', timeout=8000)
            except Exception as e:
                print(f"[avito] timeout ожидания селектора: {e}")
                items = page.query_selector_all('div[data-marker="item"]')
                if not items:
                    return []
            else:
                items = page.query_selector_all('div[data-marker="item"]')

            print(f"[avito] найдено объявлений на странице: {len(items)}")
            results = []

            for index, item in enumerate(items):
                try:
                    title_element = item.query_selector('a[data-marker="item-title"]')
                    if title_element:
                        title = title_element.get_attribute("title") or title_element.inner_text().strip()
                        raw_url = title_element.get_attribute("href")
                        product_url = f"https://www.avito.ru{raw_url}" if raw_url else None
                    else:
                        title = "Нет названия"
                        product_url = None

                    if not product_url:
                        continue

                    price_raw: str | None = None
                    price_element = item.query_selector('meta[itemprop="price"]')
                    if price_element:
                        content = price_element.get_attribute("content")
                        if content:
                            price_raw = f"{content} ₽"
                    else:
                        price_text_elem = item.query_selector('[data-marker="item-price"]')
                        if price_text_elem:
                            price_raw = price_text_elem.inner_text().strip()

                    if not price_raw or price_text_unavailable(price_raw):
                        continue

                    price = parse_price_rub(price_raw)
                    if price <= 0:
                        continue

                    desc_element = item.query_selector('meta[itemprop="description"]')
                    description = (
                        desc_element.get_attribute("content").strip()
                        if desc_element
                        else None
                    )

                    img_url = _avito_photo_url(item)

                    results.append(
                        ReturnResult(
                            title=title,
                            link=product_url,
                            price=price,
                            description=description,
                            photo_url=img_url,
                        )
                    )
                except Exception as e:
                    print(f"[avito] ошибка парсинга карточки №{index + 1}: {e}")
                    continue

            return results
        finally:
            try:
                page.close()
            except:
                pass