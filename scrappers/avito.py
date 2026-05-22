import random
import time

from models.result import ReturnResult, normalize_photo_url, parse_price_rub, price_text_unavailable

_PHOTO_SELECTORS = (
    '[data-marker="item-photo"] img',
    '[data-marker="slider-image"] img',
    'li[data-marker="slider-image/img"] img',
    'img[itemprop="image"]',
    'a[data-marker="item-photo"] img',
)


def _img_url_from_element(img_element) -> str | None:
    for attr in ("src", "data-src", "data-url", "data-lazy-src"):
        raw = img_element.get_attribute(attr)
        url = normalize_photo_url(raw)
        if url:
            return url
    srcset = img_element.get_attribute("srcset")
    if srcset:
        first = srcset.split(",")[0].strip().split(" ")[0]
        return normalize_photo_url(first)
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
                for x in ("/avatar", "/icon", "/logo", "sprite", "1x1", "avatars.avito")
            ):
                continue
            if "img.avito.st" in lower or "avito.st/image" in lower:
                return url
            if fallback is None:
                fallback = url
    return fallback


def avito_scrape(query: str, browser):
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 900})

    clean_query = query.strip().replace(" ", "+")
    url = f"https://www.avito.ru/bashkortostan?q={clean_query}"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("Страница AVITO загружена. Ожидаем рендеринга товаров...")

        time.sleep(random.uniform(2.0, 3.0))

        for i in range(1, 4):
            page.evaluate(
                f"window.scrollTo({{top: (document.body.scrollHeight / 3) * {i}, behavior: 'smooth'}});"
            )
            time.sleep(random.uniform(1.0, 1.8))

        page.wait_for_selector('div[data-marker="item"]', timeout=15000)
        items = page.query_selector_all('div[data-marker="item"]')
        print(f"Найдено объявлений на странице: {len(items)}")

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
                print(f"Ошибка парсинга карточки №{index + 1}: {e}")
                continue

        page.close()
        return results

    except Exception as e:
        print(f"Произошла ошибка при парсинге: {e}")
        page.screenshot(path="error_screenshot.png")
        page.close()
        return []
