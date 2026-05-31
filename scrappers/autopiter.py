import random
import time
from urllib.parse import quote

from models import (
    ReturnResult,
    normalize_photo_url,
    parse_price_rub,
    price_text_unavailable,
)
from scrappers.base import BaseBrowserScraper


class AutopiterScraper(BaseBrowserScraper):
    """Парсер для торговой площадки Автопитер."""

    def __init__(self):
        super().__init__(name="autopiter")

    def scrape(self, query: str, browser) -> list[ReturnResult]:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})
        page.on("pageerror", lambda exc: None)

        url = f"https://autopiter.ru/goods/{quote(query)}"

        try:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print("[autopiter] страница загружена. Ожидаем рендеринга товаров...")
                time.sleep(random.uniform(2.0, 3.0))

                for i in range(1, 4):
                    try:
                        page.evaluate(
                            f"window.scrollTo({{top: (document.body.scrollHeight / 3) * {i}, behavior: 'smooth'}});"
                        )
                        time.sleep(random.uniform(1.0, 1.8))
                    except:
                        break
            except Exception as e:
                print(f"[autopiter] ошибка загрузки страницы: {e}")
                return []

            try:
                page.wait_for_selector(
                    'div[itemtype="http://schema.org/Product"]',
                    timeout=8000,
                    state="attached"
                )
            except Exception as e:
                print(f"[autopiter] timeout ожидания селектора: {e}")
                items = page.query_selector_all('div[itemtype="http://schema.org/Product"]')
                if not items:
                    return []
            else:
                items = page.query_selector_all('div[itemtype="http://schema.org/Product"]')

            print(f"[autopiter] найдено позиций на странице: {len(items)}")
            results = []

            for index, item in enumerate(items):
                try:
                    row = item.evaluate_handle(
                        'el => el.closest(\'div[class*="IndividualTableRow__row"]\')'
                    ).as_element()

                    title_element = item.query_selector('meta[itemprop="name"]')
                    title = (
                        title_element.get_attribute("content").strip()
                        if title_element
                        else "Нет названия"
                    )

                    link_element = (
                        row.query_selector('a[href*="/goods/"][href*="id"]')
                        if row
                        else None
                    )
                    raw_url = link_element.get_attribute("href") if link_element else None
                    product_url = (
                        f"https://autopiter.ru{raw_url}"
                        if raw_url
                        else "Нет ссылки"
                    )

                    price_element = item.query_selector('meta[itemprop="lowPrice"]')
                    low_price = (
                        price_element.get_attribute("content").strip()
                        if price_element
                        else None
                    )
                    price_raw: str | None = None
                    if low_price and low_price != "0":
                        price_raw = f"{low_price} ₽"
                    else:
                        price_text_elem = (
                            row.query_selector(
                                '[class*="price"], [class*="Price"], [class*="cost"]'
                            )
                            if row
                            else None
                        )
                        if price_text_elem:
                            price_raw = price_text_elem.inner_text().strip()

                    if not price_raw or price_text_unavailable(price_raw):
                        continue

                    parsed_price = parse_price_rub(price_raw)
                    if parsed_price <= 0:
                        continue

                    desc_element = item.query_selector('meta[itemprop="description"]')
                    description = (
                        desc_element.get_attribute("content").strip()
                        if desc_element
                        else None
                    )

                    img_url: str | None = None
                    if row:
                        img_element = row.query_selector("img")
                        if img_element:
                            for attr in ("src", "data-src", "srcset"):
                                raw = img_element.get_attribute(attr)
                                if attr == "srcset" and raw:
                                    raw = raw.split(",")[0].strip().split(" ")[0]
                                img_url = normalize_photo_url(raw)
                                if img_url:
                                    break

                    if product_url == "Нет ссылки":
                        continue

                    results.append(
                        ReturnResult(
                            title=title,
                            link=product_url,
                            price=parsed_price,
                            description=description,
                            photo_url=img_url,
                        )
                    )
                except Exception as e:
                    print(f"[autopiter] ошибка парсинга карточки №{index + 1}: {e}")
                    continue

            return results
        finally:
            try:
                page.close()
            except:
                pass
