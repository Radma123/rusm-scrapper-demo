import random
import re
import time
from urllib.parse import quote

from models.result import ReturnResult, normalize_photo_url, parse_price_rub

_PRODUCT_ID_RE = re.compile(r"-(\d+)(?:\?|/|$)")


def _product_id_from_href(href: str) -> str | None:
    match = _PRODUCT_ID_RE.search(href)
    return match.group(1) if match else None


def _normalize_product_url(href: str) -> str:
    base = href.split("?")[0]
    if base.startswith("http"):
        return base
    return f"https://www.ozon.ru{base}"


def _price_from_text(text: str) -> str | None:
    for line in text.split("\n"):
        line = line.strip()
        if "₽" not in line:
            continue
        match = re.search(r"(\d[\d\s\u00a0]*)₽", line)
        if match:
            amount = match.group(1).replace("\u00a0", " ").strip()
            if amount:
                return f"{amount} ₽"
    return None


_PROMO_TITLE_RE = re.compile(
    r"^(?:"
    r"распродажа|вау-цены|цена что надо|стало дешевле|express|оригинал|"
    r"\d+\s*баллов\s*за\s*отзыв|"
    r"(?:\d+\s*шт\s*)?остал(?:ось|ась)|"
    r"apple\s*оригинал"
    r")$",
    re.I,
)


def _is_promo_title(line: str) -> bool:
    line = line.strip()
    if _PROMO_TITLE_RE.match(line):
        return True
    return bool(re.search(r"\d+[\.,]?\d*\s*отзыв", line, re.I))


def _title_from_container(container) -> str | None:
    title_span = container.query_selector("span.tsBody500Medium")
    if title_span:
        text = title_span.inner_text().strip()
        if len(text) >= 10 and not _is_promo_title(text):
            return text

    for tile_link in container.query_selector_all(
        'a[class*="tile-clickable-element"]'
    ):
        span = tile_link.query_selector("span.tsBody500Medium")
        if span:
            text = span.inner_text().strip()
            if len(text) >= 10 and not _is_promo_title(text):
                return text

        text = tile_link.inner_text().strip()
        if len(text) >= 10 and not _is_promo_title(text) and "₽" not in text:
            return text

    for line in (container.inner_text() or "").split("\n"):
        line = line.strip()
        if not line or "₽" in line or _is_promo_title(line):
            continue
        if re.match(r"^-?\d+%$", line) or re.match(r"^−\d+%$", line):
            continue
        if re.match(r"^\d+\s*(отзыв|товар)", line, re.I):
            continue
        if re.match(r"^\d+(\.\d+)?$", line):
            continue
        if re.match(r"^\d+[\.,]?\d*\s*отзыв", line, re.I):
            continue
        if re.match(r"^(доставка|завтра|послезавтра|в корзину|купить|\d+\s+\w+)", line, re.I):
            continue
        if len(line) < 10 or len(line) > 300:
            continue
        return line

    return None


def _title_from_href(href: str) -> str | None:
    slug_match = re.search(r"/product/([^/?]+)", href)
    if not slug_match:
        return None
    slug = slug_match.group(1)
    slug = re.sub(r"-\d+$", "", slug)
    title = slug.replace("-", " ").strip()
    return title[:1].upper() + title[1:] if len(title) >= 10 else None


def ozon_scrape(query: str, browser):
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 900})

    page.on("pageerror", lambda exc: None)  # Silently ignore JS errors

    clean_query = query.strip()
    search_url = (
        f"https://www.ozon.ru/search/?text={quote(clean_query)}&from_global=true"
    )

    try:
        try:
            page.goto("https://www.ozon.ru/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(1.5, 2.5))

            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            print("Страница Ozon загружена. Ожидаем рендеринга товаров...")

            time.sleep(random.uniform(2.0, 3.0))
        except Exception as e:
            print(f"Ошибка загрузки страницы Ozon: {e}")
            return []

        title = page.title()
        if "Antibot" in title or "ограничен" in title.lower():
            print("Ozon показал антибот-страницу, результаты недоступны.")
            page.screenshot(path="ozon_antibot_screenshot.png")
            return []

        for i in range(1, 4):
            try:
                page.evaluate(
                    f"window.scrollTo({{top: (document.body.scrollHeight / 3) * {i}, behavior: 'smooth'}});"
                )
                time.sleep(random.uniform(1.0, 1.8))
            except:
                break

        results_root = (
            page.query_selector('div[data-widget="searchResultsV2"]')
            or page.query_selector('div[data-widget="tileGridDesktop"]')
        )
        scope = results_root or page

        # Try to wait for selector, but catch connection errors
        try:
            scope.wait_for_selector('a[href*="/product/"]', timeout=8000, state="attached")
        except Exception as e:
            print(f"Timeout ожидания селектора Ozon: {e}")
            links = scope.query_selector_all('a[href*="/product/"]')
            if not links:
                return []
        else:
            links = scope.query_selector_all('a[href*="/product/"]')

        print(f"Найдено ссылок на товары: {len(links)}")

        results = []
        seen_ids: set[str] = set()

        for index, link in enumerate(links):
            try:
                href = link.get_attribute("href")
                if not href or "/product/" not in href:
                    continue

                product_id = _product_id_from_href(href)
                if not product_id or product_id in seen_ids:
                    continue
                seen_ids.add(product_id)

                container = link.evaluate_handle(
                    """el => {
                        return el.closest('[data-index]')
                            || el.closest('[class*="tile"]')
                            || el.closest('[class*="product"]')
                            || (() => {
                                let node = el.parentElement;
                                for (let i = 0; i < 6 && node; i++) {
                                    if ((node.innerText || '').includes('₽')) return node;
                                    node = node.parentElement;
                                }
                                return null;
                            })();
                    }"""
                ).as_element()

                if not container:
                    continue

                title_text = _title_from_container(container)
                if not title_text:
                    title_text = _title_from_href(href)
                if not title_text:
                    product_id = _product_id_from_href(href)
                    title_text = f"Товар {product_id}" if product_id else "Нет названия"

                product_url = _normalize_product_url(href)

                card_text = container.inner_text() or ""
                price = _price_from_text(card_text)
                if not price:
                    continue

                parsed_price = parse_price_rub(price)
                if parsed_price <= 0:
                    continue

                img_url: str | None = None
                img_element = container.query_selector("img")
                if img_element:
                    for attr in ("src", "data-src", "srcset"):
                        raw = img_element.get_attribute(attr)
                        if attr == "srcset" and raw:
                            raw = raw.split(",")[0].strip().split(" ")[0]
                        img_url = normalize_photo_url(raw)
                        if img_url:
                            break

                results.append(
                    ReturnResult(
                        title=title_text,
                        link=product_url,
                        price=parsed_price,
                        description=None,
                        photo_url=img_url,
                    )
                )

            except Exception as e:
                print(f"Ошибка парсинга карточки №{index + 1}: {e}")
                continue

        print(f"Собрано уникальных товаров: {len(results)}")
        return results

    except Exception as e:
        print(f"Произошла ошибка при парсинге Ozon: {e}")
        try:
            page.screenshot(path="ozon_error_screenshot.png")
        except:
            pass
        return []
    finally:
        try:
            page.close()
        except:
            pass
