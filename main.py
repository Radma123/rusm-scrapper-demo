from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from models.result import ReturnResult
from services.search import SearchService
from tools.ai_filter import active_filter

# Импортируем все стратегии поиска
from scrappers.rusmarket import RusmarketScraper
from scrappers.avito import AvitoScraper
from scrappers.ozon import OzonScraper
from scrappers.autopiter import AutopiterScraper

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="RusM Scrapper")


def compile_scss():
    """Компилирует static/scss/app.scss в static/css/app.css при запуске."""
    scss_file = ROOT / "static" / "scss" / "app.scss"
    css_file = ROOT / "static" / "css" / "app.css"
    
    try:
        import sass
        print(f"[SCSS] Обнаружен препроцессор. Компиляция: {scss_file.name} -> {css_file.name}...")
        css_file.parent.mkdir(parents=True, exist_ok=True)
        compiled_css = sass.compile(filename=str(scss_file), output_style="expanded")
        with open(css_file, "w", encoding="utf-8") as f:
            f.write(compiled_css)
        print("[SCSS] Компиляция стилей успешно завершена.")
    except ImportError:
        print("[SCSS] Предупреждение: библиотека 'libsass' не установлена.")
        print("[SCSS] Стили не могут быть скомпилированы динамически.")
    except Exception as exc:
        print(f"[SCSS] Критическая ошибка при компиляции SCSS: {exc}")


# Компилируем стили перед монтированием статики
compile_scss()

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

# Регистрируем стратегии поиска
scrapers = [
    RusmarketScraper(),
    AvitoScraper(),
    OzonScraper(),
    AutopiterScraper()
]

# Инициализируем поисковый сервис с внедренными зависимостями (Strategy & AI Filter)
search_service = SearchService(scrapers=scrapers, ai_filter=active_filter)


@app.get("/")
def index_page() -> FileResponse:
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1)) -> list[ReturnResult]:
    try:
        results = search_service.search_all(q)
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def main(query: str):
    """CLI: параллельный поиск и вывод в консоль."""
    results = search_service.search_all(query)
    print(f"\nВсего: {len(results)}")
    for item in results:
        print(f"[{item.source}] {item.title} — {item.price} ₽ — {item.link}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        cli_query = sys.argv[2] if len(sys.argv) > 2 else "86989733"
        main(cli_query)
    else:
        print(f"http://127.0.0.1:{settings.API_PORT}")
        uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
