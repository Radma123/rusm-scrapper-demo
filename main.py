from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import uvicorn
from camoufox.sync_api import Camoufox
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.rusmarket import get_products_availability
from api.rusmarket_convert import availability_to_results
from config import API_HOST, API_PORT
from models.result import ReturnResult, normalize_photo_url
from scrappers.autopiter import autopiter_scrape
from scrappers.avito import avito_scrape
from scrappers.ozon import ozon_scrape
from tools.ai_filter.filter import ai_filter

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="RusM Scrapper")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


def _tag(items: list[ReturnResult], source: str) -> list[ReturnResult]:
    return [item.model_copy(update={"source": source}) for item in items]


def _fetch_rusmarket(query: str) -> list[ReturnResult]:
    serial = query.strip()
    products = [{"serial": serial, "count": 1}]
    print(f"[rusmarket] запрос availability: {serial}")
    data = get_products_availability(products=products)
    return availability_to_results(data)


def _run_scraper(scrape_fn, query: str, source: str) -> list[ReturnResult]:
    print(f"[{source}] парсинг: {query.strip()}")
    with Camoufox(headless=True) as browser:
        raw = scrape_fn(query, browser)
    return _tag(raw, source)


def search_all(query: str) -> list[ReturnResult]:
    """Параллельно опрашивает Rusmarket, Avito, Ozon и Автопитер."""
    q = query.strip()
    if not q:
        return []

    jobs = {
        "rusmarket": lambda: _fetch_rusmarket(q),
        "avito": lambda: _run_scraper(avito_scrape, q, "avito"),
        "ozon": lambda: _run_scraper(ozon_scrape, q, "ozon"),
        "autopiter": lambda: _run_scraper(autopiter_scrape, q, "autopiter"),
    }

    combined: list[ReturnResult] = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {pool.submit(fn): name for name, fn in jobs.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                chunk = future.result()
                combined.extend(chunk)
                print(f"[{name}] готово: {len(chunk)} позиций")
            except Exception as exc:
                print(f"[{name}] ошибка: {exc}")

    return _finalize_results(combined)


def _finalize_results(results: list[ReturnResult]) -> list[ReturnResult]:
    """Только с ценой > 0, фото без мусорных строк, сортировка по цене."""
    cleaned: list[ReturnResult] = []
    for item in results:
        if item.price <= 0:
            continue
        photo = normalize_photo_url(item.photo_url)
        cleaned.append(item.model_copy(update={"photo_url": photo}))
        ai_filtered = ai_filter(cleaned)

    return sorted(ai_filtered, key=lambda r: r.price)


@app.get("/")
def index_page() -> FileResponse:
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1)) -> list[ReturnResult]:
    try:
        results = search_all(q)
        # return [r.model_dump() for r in results] // использовать для производительности
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def main(query: str):
    """CLI: параллельный поиск и вывод в консоль."""
    results = search_all(query)
    print(f"\nВсего: {len(results)}")
    for item in results:
        print(f"[{item.source}] {item.title} — {item.price} ₽ — {item.link}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        cli_query = sys.argv[2] if len(sys.argv) > 2 else "86989733"
        main(cli_query)
    else:
        print(f"http://127.0.0.1:{API_PORT}")
        uvicorn.run(app, host=API_HOST, port=API_PORT)
