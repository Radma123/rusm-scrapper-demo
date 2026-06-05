// Конфигурация иконок для площадок
const ICONS = {
  avito: "/static/icons/avito.png",
  ozon: "/static/icons/ozon.png",
  rusmarket: "/static/icons/rusmarket.svg",
  autopiter: null,
};

// Текстовые названия площадок
const SOURCE_LABELS = {
  avito: "Avito",
  ozon: "Ozon",
  rusmarket: "Rusmarket",
  autopiter: "Автопитер",
};

// Список доступных платформ
const PLATFORMS = ["rusmarket", "avito", "ozon", "autopiter"];

// DOM Элементы
const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const viewRadios = document.querySelectorAll('input[name="view"]');
const sortEl = document.getElementById("sort");

// Кэш для результатов поиска
let cachedItems = [];

/**
 * Форматирует цену в рубли с разделением тысяч
 * @param {number} n - Цена
 * @returns {string}
 */
function formatPrice(n) {
  return new Intl.NumberFormat("ru-RU").format(n) + " ₽";
}

/**
 * Проверяет валидность URL картинки
 * @param {string} url - URL картинки
 * @returns {boolean}
 */
function isValidPhotoUrl(url) {
  if (!url) return false;
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

/**
 * Экранирует HTML для защиты от XSS
 * @param {string} s - Текст
 * @returns {string}
 */
function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

/**
 * Генерирует HTML блок источника (платформы)
 * @param {string} source - Код источника
 * @returns {string}
 */
function sourceBlock(source) {
  const label = SOURCE_LABELS[source] || source;
  const src = ICONS[source];
  let icon = src
    ? `<img class="source-icon" src="${src}" alt="${label}" />`
    : `<span class="source-badge">${label.slice(0, 2).toUpperCase()}</span>`;

  const isOurPlatform = source === "rusmarket" ? " source--rusmarket" : "";

  if (isOurPlatform && !src) {
    icon = `<img class="source-icon" src="/static/icons/rusmarket-none.webp" alt="Rusmarket" />`;
  }

  return `<div class="source${isOurPlatform}">${icon}<span class="source-label">${escapeHtml(label)}</span></div>`;
}

/**
 * Генерирует HTML разметку карточки товара
 * @param {object} item - Объект товара
 * @param {object} options - Дополнительные параметры
 * @returns {string}
 */
function cardHtml(item, { showSource = true } = {}) {
  const photo = isValidPhotoUrl(item.photo_url)
    ? `<img class="card__img" src="${escapeHtml(item.photo_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" />`
    : `<div class="card__img card__img--placeholder">Нет фото</div>`;

  const desc = item.description
    ? `<p class="card__desc">${escapeHtml(item.description)}</p>`
    : "";

  const top = showSource
    ? `<div class="card__top">${sourceBlock(item.source)}<a class="card__title" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a></div>`
    : `<a class="card__title card__title--solo" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>`;

  return `
    <article class="card${showSource ? "" : " card--compact"}">
      ${top}
      ${photo}
      <p class="card__price">${formatPrice(item.price)}</p>
      ${desc}
    </article>
  `;
}

/**
 * Сортирует товары
 * @param {Array} items - Список товаров
 * @param {string} sortKey - Тип сортировки
 * @returns {Array}
 */
function sortItems(items, sortKey) {
  const copy = [...items];
  switch (sortKey) {
    case "price_desc":
      return copy.sort((a, b) => b.price - a.price);
    case "title_asc":
      return copy.sort((a, b) => a.title.localeCompare(b.title, "ru"));
    case "title_desc":
      return copy.sort((a, b) => b.title.localeCompare(a.title, "ru"));
    default:
      return copy.sort((a, b) => a.price - b.price);
  }
}

/**
 * Возвращает активный вид отображения (сетка/список/платформы)
 * @returns {string}
 */
function getViewMode() {
  return document.querySelector('input[name="view"]:checked')?.value || "platforms";
}

/**
 * Рендерит товары сгруппированные по платформам
 * @param {Array} items - Список товаров
 * @returns {string}
 */
function renderPlatforms(items) {
  return PLATFORMS.map((source) => {
    const platformItems = items.filter((i) => i.source === source);
    const listHtml = platformItems.length
      ? platformItems.map((i) => cardHtml(i, { showSource: false })).join("")
      : '<p class="platform-empty">Нет товаров</p>';
    return `
      <section class="platform-column" data-platform="${source}">
        <header class="platform-column__head">
          ${sourceBlock(source)}
          <span class="platform-column__count">${platformItems.length}</span>
        </header>
        <div class="platform-column__list">${listHtml}</div>
      </section>
    `;
  }).join("");
}

/**
 * Основная функция рендеринга результатов
 */
function renderResults() {
  if (!cachedItems.length) {
    resultsEl.innerHTML = "";
    resultsEl.className = "results results--platforms";
    return;
  }

  const sorted = sortItems(cachedItems, sortEl.value);
  const view = getViewMode();

  if (view === "platforms") {
    resultsEl.className = "results results--platforms";
    resultsEl.innerHTML = renderPlatforms(sorted);
    return;
  }

  resultsEl.className = `results results--${view}`;
  resultsEl.innerHTML = sorted.map((i) => cardHtml(i)).join("");
}

// Слушатели событий
viewRadios.forEach((r) => {
  r.addEventListener("change", renderResults);
});

sortEl.addEventListener("change", renderResults);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = queryInput.value.trim();
  if (!q) return;

  submitBtn.disabled = true;
  statusEl.hidden = false;
  statusEl.textContent = "Ищем на всех площадках…";
  resultsEl.innerHTML = "";
  cachedItems = [];

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    cachedItems = await res.json();
    statusEl.textContent = cachedItems.length
      ? `Найдено: ${cachedItems.length}`
      : "Ничего не найдено";
    renderResults();
  } catch (err) {
    statusEl.textContent = "Ошибка: " + err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

// Первоначальный поиск при наличии параметра ?q в URL
const params = new URLSearchParams(location.search);
if (params.get("q")) {
  queryInput.value = params.get("q");
  form.requestSubmit();
}
