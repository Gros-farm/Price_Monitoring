const stores = [
  { id: "auchan", name: "Ашан", logo: "./assets/figma/logo-auchan.png", color: "#ffffff", logoClass: "store-logo--auchan" },
  { id: "metro", name: "Metro", short: "M", color: "#014171" },
];

const REFRESH_INTERVAL_MS = 2 * 60 * 60 * 1000;
const CHART_WIDTH = 1080;
const CHART_HEIGHT = 402;
const CHART_PADDING = { top: 16, right: 38, bottom: 42, left: 42 };
const CHART_DATES = ["24.03", "25.03", "26.03", "27.03", "28.03", "29.03", "30.03"];

const categories = [
  "Фрукты",
  "Овощи",
  "Ягоды",
  "Зелень",
  "Грибы",
];

const categoryColors = {
  Фрукты: "#4d9de0",
  Овощи: "#43aa3d",
  Ягоды: "#df3d8f",
  Зелень: "#138a36",
  Грибы: "#8f6f4d",
};

const productColors = [
  "#007aff",
  "#92bbe9",
  "#007aff",
  "#db9494",
  "#e61414",
  "#8b3d3d",
  "#40b34a",
  "#285fcc",
  "#8dad2d",
  "#e0caca",
  "#680b75",
];

const baseCatalog = [
  ["Томаты красные Скэрлетт 450 г", "Овощи", 300],
  ["Томаты черри красные на ветке, 500 г", "Овощи", 189],
  ["Огурцы сорт Святогор 600 г", "Овощи", 290],
  ["Среднеплодные огурцы для салатов и консервации", "Овощи", 150],
  ["Банан, шт", "Фрукты", 35],
  ["Лимоны, 500 г", "Фрукты", 130],
  ["Киви зеленые, 600 г", "Фрукты", 210],
  ["Авокадо Хасс, 600 г", "Фрукты", 300],
  ["Виноград белый без косточек, 500 г", "Фрукты", 320],
  ["Манго спелое, 1 шт", "Фрукты", 280],
  ["Лаймы свежие, 3 шт", "Фрукты", 145],
  ["Грейпфрут красный, 1 кг", "Фрукты", 190],
  ["Персики отборные, 500 г", "Фрукты", 260],
  ["Нектарины сладкие, 500 г", "Фрукты", 245],
  ["Абрикосы свежие, 500 г", "Фрукты", 230],
  ["Сливы синие, 500 г", "Фрукты", 170],
  ["Хурма королек, 1 кг", "Фрукты", 240],
  ["Гранат крупный, 1 шт", "Фрукты", 210],
  ["Ананас спелый, 1 шт", "Фрукты", 390],
  ["Кокос питьевой, 1 шт", "Фрукты", 280],
  ["Помело, 1 кг", "Фрукты", 185],
  ["Фейхоа, 500 г", "Фрукты", 330],
  ["Инжир свежий, 250 г", "Фрукты", 420],
  ["Финики королевские, 300 г", "Фрукты", 260],
  ["Огурцы сорт Святогор, 600 г", "Овощи", 350],
  ["Короткоплодные огурцы для салатов, 450 г", "Овощи", 200],
  ["Свежие среднеплодные огурцы, 600 г", "Овощи", 220],
  ["Томаты красные Скартлет, 450 г", "Овощи", 500],
  ["Томаты черри красные на ветке, 500 г", "Овощи", 197],
  ["Томаты сливка желтые, 350 г", "Овощи", 297],
  ["Розовые томаты Дагестан, 500 г", "Овощи", 370],
  ["Картофель молодой, 1 кг", "Овощи", 89],
  ["Морковь мытая, 1 кг", "Овощи", 76],
  ["Лук репчатый, 1 кг", "Овощи", 65],
  ["Свекла, 1 кг", "Овощи", 72],
  ["Капуста белокочанная, 1 кг", "Овощи", 55],
  ["Кабачки свежие, 1 кг", "Овощи", 145],
  ["Баклажаны грунтовые, 1 кг", "Овощи", 240],
  ["Перец сладкий красный, 500 г", "Овощи", 210],
  ["Перец острый красный, 100 г", "Овощи", 95],
  ["Редис красный, 250 г", "Овощи", 95],
  ["Редька зеленая, 1 кг", "Овощи", 120],
  ["Репа свежая, 1 кг", "Овощи", 115],
  ["Тыква очищенная, 500 г", "Овощи", 135],
  ["Кукуруза вареная, 2 шт", "Овощи", 160],
  ["Горошек зеленый стручковый, 250 г", "Овощи", 190],
  ["Фасоль стручковая, 400 г", "Овощи", 210],
  ["Сельдерей стеблевой, 1 уп", "Овощи", 180],
  ["Сельдерей корневой, 1 кг", "Овощи", 170],
  ["Имбирь свежий, 250 г", "Овощи", 160],
  ["Батат, 1 кг", "Овощи", 280],
  ["Топинамбур, 500 г", "Овощи", 210],
  ["Клубника свежая, 250 г", "Ягоды", 299],
  ["Голубика свежая, 125 г", "Ягоды", 260],
  ["Земляника садовая, 200 г", "Ягоды", 340],
  ["Малина свежая, 125 г", "Ягоды", 310],
  ["Ежевика свежая, 125 г", "Ягоды", 290],
  ["Черника свежая, 125 г", "Ягоды", 285],
  ["Смородина черная, 250 г", "Ягоды", 240],
  ["Смородина красная, 250 г", "Ягоды", 220],
  ["Крыжовник зеленый, 250 г", "Ягоды", 210],
  ["Брусника свежая, 250 г", "Ягоды", 270],
  ["Клюква свежая, 250 г", "Ягоды", 250],
  ["Облепиха замороженная, 300 г", "Ягоды", 230],
  ["Вишня свежая, 500 г", "Ягоды", 330],
  ["Черешня отборная, 500 г", "Ягоды", 390],
  ["Арбуз красный, 1 кг", "Ягоды", 69],
  ["Дыня Колхозница, 1 кг", "Ягоды", 110],
  ["Укроп свежий, 50 г", "Зелень", 59],
  ["Петрушка свежая, 50 г", "Зелень", 58],
  ["Кинза свежая, 50 г", "Зелень", 64],
  ["Зеленый лук, 70 г", "Зелень", 70],
  ["Базилик зеленый, 30 г", "Зелень", 115],
  ["Мята свежая, 30 г", "Зелень", 95],
  ["Шпинат свежий, 75 г", "Зелень", 140],
  ["Руккола свежая, 65 г", "Зелень", 155],
  ["Салат айсберг, 1 шт", "Зелень", 145],
  ["Салат листовой, 1 шт", "Зелень", 130],
  ["Салат романо, 1 шт", "Зелень", 160],
  ["Мангольд свежий, 100 г", "Зелень", 150],
  ["Щавель свежий, 80 г", "Зелень", 120],
  ["Черемша свежая, 100 г", "Зелень", 180],
  ["Тимьян свежий, 30 г", "Зелень", 110],
  ["Розмарин свежий, 30 г", "Зелень", 115],
  ["Орегано свежий, 30 г", "Зелень", 115],
  ["Эстрагон свежий, 30 г", "Зелень", 125],
  ["Мелисса свежая, 30 г", "Зелень", 105],
  ["Микрозелень гороха, 50 г", "Зелень", 160],
  ["Микс салатный Тоскана, 125 г", "Зелень", 198],
  ["Шампиньоны свежие, 400 г", "Грибы", 170],
  ["Вешенки свежие, 300 г", "Грибы", 180],
  ["Шиитаке, 150 г", "Грибы", 260],
  ["Эноки, 100 г", "Грибы", 210],
  ["Портобелло, 250 г", "Грибы", 290],
  ["Белые грибы замороженные, 300 г", "Грибы", 420],
  ["Лисички свежие, 250 г", "Грибы", 430],
  ["Опята маринованные, 350 г", "Грибы", 190],
  ["Маслята маринованные, 350 г", "Грибы", 210],
  ["Подберезовики сушеные, 50 г", "Грибы", 260],
  ["Подосиновики сушеные, 50 г", "Грибы", 280],
  ["Грузди соленые, 300 г", "Грибы", 240],
  ["Рыжики маринованные, 300 г", "Грибы", 260],
  ["Сморчки сушеные, 40 г", "Грибы", 390],
  ["Трюфельная паста с грибами, 90 г", "Грибы", 450],
  ["Грибное ассорти, 300 г", "Грибы", 275],
];

const storeFactors = {
  pyaterochka: 0.92,
  perekrestok: 1.04,
  auchan: 0.9,
  magnit: 0.95,
  vkusvill: 1.1,
  lenta: 0.98,
  dixy: 0.97,
  metro: 1.02,
  azbuka: 1.18,
  samokat: 1.08,
  lavka: 1.06,
};

const storeNameAdditions = {
  pyaterochka: ["Красная цена", "Свежий ряд", "Домашняя корзина"],
  perekrestok: ["Market Collection", "Зеленая линия", "Фермерский выбор"],
  auchan: ["Каждый день", "Фермерский прилавок", "Свежий выбор"],
  magnit: ["Моя цена", "Магнит fresh", "Семейный выбор"],
  vkusvill: ["ВкусВилл", "Свежая полка", "Фермерская линия"],
  lenta: ["Лента", "365 дней", "Большой выбор"],
  dixy: ["Дикси fresh", "Первым делом", "Каждый день"],
  metro: ["Metro Chef", "Fine Life", "Metro Premium"],
  azbuka: ["Азбука Вкуса", "Почти готово", "Наша ферма"],
  samokat: ["Самокат", "Свежее сегодня", "Без очереди"],
  lavka: ["Лавка", "Из лавки", "Быстрая доставка"],
};

const state = {
  storeId: "auchan",
  query: "",
  categories: new Set(categories),
  selectedIds: new Set(),
  loadingStoreId: null,
  refreshingStoreId: null,
  loadError: "",
  dataNotice: "",
};

const elements = {
  storeSwitcher: document.querySelector("#storeSwitcher"),
  categoryRow: document.querySelector("#categoryRow"),
  searchInput: document.querySelector("#searchInput"),
  rows: document.querySelector("#productRows"),
  chart: document.querySelector("#priceChart"),
  chartEmpty: document.querySelector("#chartEmpty"),
  chartHoverHint: document.querySelector("#chartHoverHint"),
  chartSummary: document.querySelector("#chartSummary"),
  toast: document.querySelector("#selectionToast"),
  averageNote: document.querySelector("#averageNote"),
  refreshButton: document.querySelector("#refreshButton"),
  dataStatus: document.querySelector("#dataStatus"),
};

const catalog = stores.flatMap((store) =>
  baseCatalog.map(([name, category, basePrice], index) => {
    const price = store.id === "auchan"
      ? basePrice
      : Math.round(basePrice * storeFactors[store.id] + ((index % 5) - 2) * 7);
    return {
      id: `${store.id}-${index}`,
      storeId: store.id,
      name: withStoreFlavor(name, store.id, index),
      category,
      price,
      color: productColors[index % productColors.length],
      history: makeHistory(price, index, store.id),
    };
  }),
);

const externalCatalogByStore = {};
const externalNoticeByStore = {};
const externalUpdatedAtByStore = {};

const hasServerApi = window.location.protocol !== "file:" && !window.location.hostname.endsWith("github.io");

const storeDataSources = {
  auchan: hasServerApi ? "/api/stores/auchan/products" : "./data/auchan-products.json",
};

let chartScale = null;
let chartHintTimer = null;
let chartSummaryLocked = false;
let chartIgnoreNextClick = false;
const chartPointer = {
  activeIndex: 0,
  x: 0,
  y: 0,
};

function withStoreFlavor(name, storeId, index) {
  if (storeId === "auchan") return name;
  const addition = storeNameAdditions[storeId][index % storeNameAdditions[storeId].length];
  if (index % 4 === 0) return `${name} ${addition}`;
  return name;
}

function makeHistory(price, index, storeId) {
  const storeShift = stores.findIndex((store) => store.id === storeId) * 8;
  return Array.from({ length: 7 }, (_, point) => {
    const wave = Math.sin((point + index) * 0.95) * 18;
    const drift = (point - 3) * ((index % 4) - 1.5) * 3;
    return Math.max(25, Math.round(price + wave + drift + storeShift));
  });
}

function renderStores() {
  elements.storeSwitcher.innerHTML = stores
    .map((store) => {
      const active = store.id === state.storeId ? " is-active" : "";
      const logo = store.logo
        ? `<img src="${store.logo}" alt="" />`
        : `<span>${store.short}</span>`;
      const logoClass = store.logoClass ? ` ${store.logoClass}` : "";
      return `
        <button class="store-button${active}" type="button" data-store="${store.id}" aria-label="${store.name}">
          <span class="store-logo${logoClass}" style="background:${store.color}">${logo}</span>
        </button>
      `;
    })
    .join("");
}

function renderCategories() {
  elements.categoryRow.innerHTML = categories
    .map((category) => {
      const active = state.categories.has(category) ? " is-active" : "";
      return `<button class="category-chip${active}" type="button" data-category="${category}">${category}</button>`;
    })
    .join("");
}

function filteredProducts() {
  const normalizedQuery = state.query.trim().toLowerCase();
  return currentCatalog().filter((product) => {
    const sameStore = product.storeId === state.storeId;
    const sameCategory = state.categories.has(product.category);
    const matchesQuery = !normalizedQuery || product.name.toLowerCase().includes(normalizedQuery);
    return sameStore && sameCategory && matchesQuery;
  });
}

function currentCatalog() {
  return externalCatalogByStore[state.storeId] || catalog;
}

function renderRows() {
  if (state.loadingStoreId === state.storeId) {
    elements.averageNote.innerHTML = "Загружаем сохраненный<br />каталог и цены...";
    elements.rows.innerHTML = `
      <tr class="loading-row">
        <td colspan="4">
          <span class="loader" aria-hidden="true"></span>
          Загружаем позиции выбранной сети
        </td>
      </tr>
    `;
    updateRefreshUi();
    updateToast();
    return;
  }

  const products = filteredProducts();
  elements.averageNote.innerHTML = "Приблизительная закупочная цена<br />~ на 30% ниже розничной";
  updateRefreshUi();

  if (state.loadError) {
    elements.rows.innerHTML = `
      <tr class="empty-row">
        <td colspan="4">${state.loadError}</td>
      </tr>
    `;
    updateToast();
    return;
  }

  if (!products.length) {
    elements.rows.innerHTML = `
      <tr class="empty-row">
        <td colspan="4">Ничего не найдено. Попробуйте изменить поиск или категорию.</td>
      </tr>
    `;
    updateToast();
    return;
  }

  elements.rows.innerHTML = products
    .map((product) => {
      const checked = state.selectedIds.has(product.id) ? "checked" : "";
      const color = product.color || categoryColors[product.category];
      return `
        <tr>
          <td>
            <input class="product-check" type="checkbox" data-product="${product.id}" ${checked} aria-label="Выбрать ${product.name}" />
          </td>
          <td><span class="product-dot" style="background:${color}"></span></td>
          <td>${product.name}</td>
          <td class="price-cell">${formatPrice(product.price)}</td>
        </tr>
      `;
    })
    .join("");
  updateToast();
}

function drawChart() {
  const selected = selectedProducts();
  const width = CHART_WIDTH;
  const height = CHART_HEIGHT;
  const padding = CHART_PADDING;
  const values = selected.flatMap((product) => product.history);
  const domain = getChartDomain(values);
  const minValue = domain.min;
  const maxValue = domain.max;
  const range = Math.max(1, maxValue - minValue);
  const dates = CHART_DATES;

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const x = (index) => padding.left + (index * plotWidth) / (dates.length - 1);
  const y = (value) => padding.top + ((maxValue - value) * plotHeight) / range;
  chartScale = { x, y, plotWidth, plotHeight, minValue, maxValue };

  let markup = "";
  for (let i = 0; i <= 8; i += 1) {
    const lineY = padding.top + (i * plotHeight) / 8;
    const label = maxValue - (i * range) / 8;
    markup += `<line class="grid-line" x1="${padding.left}" y1="${lineY}" x2="${width - padding.right}" y2="${lineY}" />`;
    markup += `<text class="axis-text" text-anchor="end" x="${padding.left - 12}" y="${lineY + 4}">${formatAxisValue(label)}</text>`;
  }

  dates.forEach((date, index) => {
    const lineX = x(index);
    markup += `<line class="grid-line-vertical" x1="${lineX}" y1="${padding.top}" x2="${lineX}" y2="${height - padding.bottom}" />`;
    markup += `<text class="axis-text axis-text--x" text-anchor="middle" x="${lineX}" y="${height - 13}">${date}</text>`;
  });

  selected.forEach((product) => {
    const color = product.color || categoryColors[product.category];
    const points = product.history.map((value, index) => ({ x: x(index), y: y(value) }));
    const path = buildSmoothPath(points);
    markup += `<path class="chart-path" d="${path}" stroke="${color}" />`;
  });

  markup += `
    <g class="chart-target" id="chartTarget" aria-hidden="true">
      <line class="chart-target-line" data-target="x" x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" />
      <line class="chart-target-line" data-target="y" x1="${padding.left}" y1="${padding.top}" x2="${width - padding.right}" y2="${padding.top}" />
      <circle class="chart-target-ring" cx="${padding.left}" cy="${padding.top}" r="10" />
      <circle class="chart-target-dot" cx="${padding.left}" cy="${padding.top}" r="4" />
      <g class="chart-target-label chart-target-label--y">
        <rect x="${padding.left - 42}" y="${padding.top - 10}" width="34" height="20" rx="6" />
        <text x="${padding.left - 25}" y="${padding.top + 4}" text-anchor="middle">0</text>
      </g>
      <g class="chart-target-label chart-target-label--x">
        <rect x="${padding.left - 17}" y="${height - padding.bottom + 11}" width="34" height="20" rx="6" />
        <text x="${padding.left}" y="${height - padding.bottom + 25}" text-anchor="middle">${dates[0]}</text>
      </g>
    </g>
  `;

  elements.chart.innerHTML = markup;
  elements.chartEmpty.style.display = selected.length ? "none" : "flex";
  resetChartInteraction();
}

function selectedProducts() {
  return currentCatalog().filter((product) => state.selectedIds.has(product.id));
}

function getChartDomain(values) {
  if (!values.length) {
    return { min: 0, max: 1000 };
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max(10, (max - min) * 0.16);
  const roundedMin = Math.max(0, Math.floor((min - padding) / 10) * 10);
  const roundedMax = Math.ceil((max + padding) / 10) * 10;

  if (roundedMax === roundedMin) {
    return { min: Math.max(0, roundedMin - 10), max: roundedMax + 10 };
  }

  return { min: roundedMin, max: roundedMax };
}

function formatAxisValue(value) {
  const rounded = Math.round(value);
  return rounded >= 1000 ? `${(rounded / 1000).toLocaleString("ru-RU", { maximumFractionDigits: 1 })}k` : String(rounded);
}

function buildSmoothPath(points) {
  if (!points.length) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

  return points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x} ${point.y}`;

    const previous = points[index - 1];
    const controlX = previous.x + (point.x - previous.x) / 2;
    return `${path} C ${controlX} ${previous.y}, ${controlX} ${point.y}, ${point.x} ${point.y}`;
  }, "");
}

function resetChartInteraction() {
  window.clearTimeout(chartHintTimer);
  chartSummaryLocked = false;
  chartIgnoreNextClick = false;
  elements.chartHoverHint.classList.remove("is-visible");
  elements.chartSummary.hidden = true;
  const target = elements.chart.querySelector("#chartTarget");
  if (target) target.classList.remove("is-visible");
}

function closeChartSummary() {
  chartSummaryLocked = false;
  chartIgnoreNextClick = false;
  elements.chartSummary.hidden = true;
  elements.chartHoverHint.classList.remove("is-visible");
  const target = elements.chart.querySelector("#chartTarget");
  if (target) target.classList.remove("is-visible");
}

function getChartPointer(event) {
  const rect = elements.chart.getBoundingClientRect();
  const rawX = ((event.clientX - rect.left) * CHART_WIDTH) / rect.width;
  const rawY = ((event.clientY - rect.top) * CHART_HEIGHT) / rect.height;
  const plotLeft = CHART_PADDING.left;
  const plotRight = CHART_WIDTH - CHART_PADDING.right;
  const plotTop = CHART_PADDING.top;
  const plotBottom = CHART_HEIGHT - CHART_PADDING.bottom;
  const x = Math.min(plotRight, Math.max(plotLeft, rawX));
  const y = Math.min(plotBottom, Math.max(plotTop, rawY));
  const value = chartScale
    ? chartScale.maxValue - ((y - plotTop) / (plotBottom - plotTop)) * (chartScale.maxValue - chartScale.minValue)
    : 0;
  const activeIndex = Math.min(
    CHART_DATES.length - 1,
    Math.max(0, Math.round(((x - plotLeft) / (plotRight - plotLeft)) * (CHART_DATES.length - 1))),
  );

  return { x, y, value, activeIndex };
}

function moveChartTarget(point) {
  const target = elements.chart.querySelector("#chartTarget");
  if (!target) return;

  target.classList.add("is-visible");
  target.querySelector('[data-target="x"]').setAttribute("x1", point.x);
  target.querySelector('[data-target="x"]').setAttribute("x2", point.x);
  target.querySelector('[data-target="y"]').setAttribute("y1", point.y);
  target.querySelector('[data-target="y"]').setAttribute("y2", point.y);
  target.querySelector(".chart-target-ring").setAttribute("cx", point.x);
  target.querySelector(".chart-target-ring").setAttribute("cy", point.y);
  target.querySelector(".chart-target-dot").setAttribute("cx", point.x);
  target.querySelector(".chart-target-dot").setAttribute("cy", point.y);
  target.querySelector(".chart-target-label--y rect").setAttribute("y", point.y - 10);
  target.querySelector(".chart-target-label--y text").setAttribute("y", point.y + 4);
  target.querySelector(".chart-target-label--y text").textContent = formatCursorValue(point.value);
  target.querySelector(".chart-target-label--x rect").setAttribute("x", point.x - 17);
  target.querySelector(".chart-target-label--x text").setAttribute("x", point.x);
  target.querySelector(".chart-target-label--x text").textContent = CHART_DATES[point.activeIndex];
}

function formatCursorValue(value) {
  return Number(value).toLocaleString("ru-RU", {
    maximumFractionDigits: value >= 100 ? 0 : 1,
  });
}

function positionChartPopup(element, point, width, height) {
  const offset = 14;
  const rect = elements.chart.getBoundingClientRect();
  const visibleRight = Math.min(CHART_WIDTH, ((window.innerWidth - rect.left - 8) * CHART_WIDTH) / rect.width);
  const visibleBottom = Math.min(CHART_HEIGHT, ((window.innerHeight - rect.top - 8) * CHART_HEIGHT) / rect.height);
  const maxLeft = Math.max(8, visibleRight - width);
  const maxTop = Math.max(8, visibleBottom - height);
  const left = Math.min(maxLeft, point.x + offset);
  const top = Math.min(maxTop, point.y + offset);
  element.style.setProperty("--chart-popup-left", `${Math.max(8, left)}px`);
  element.style.setProperty("--chart-popup-top", `${Math.max(8, top)}px`);
}

function scheduleChartHint() {
  window.clearTimeout(chartHintTimer);
  elements.chartHoverHint.classList.remove("is-visible");
  chartHintTimer = window.setTimeout(() => {
    if (!selectedProducts().length) return;
    positionChartPopup(elements.chartHoverHint, chartPointer, 276, 54);
    elements.chartHoverHint.classList.add("is-visible");
  }, 2000);
}

function renderChartSummary(point) {
  const selected = selectedProducts();
  if (!selected.length) return;

  chartSummaryLocked = true;
  const date = CHART_DATES[point.activeIndex];
  const rows = selected
    .map((product) => {
      const color = product.color || categoryColors[product.category];
      const value = product.history[point.activeIndex] ?? product.price;
      return `
        <div class="chart-summary__row">
          <span class="chart-summary__dot" style="background:${color}"></span>
          <span class="chart-summary__name">${product.name}</span>
          <span class="chart-summary__price">${formatPrice(value)}</span>
        </div>
      `;
    })
    .join("");

  elements.chartSummary.innerHTML = `
    <div class="chart-summary__date">${date}</div>
    <div class="chart-summary__body">${rows}</div>
  `;
  positionChartPopup(elements.chartSummary, point, 338, Math.min(300, 50 + selected.length * 34));
  elements.chartSummary.hidden = false;
}

function updateToast() {
  const activeCatalog = currentCatalog();
  const total = activeCatalog.filter((product) => product.storeId === state.storeId).length;
  const selectedInStore = activeCatalog.filter((product) => product.storeId === state.storeId && state.selectedIds.has(product.id)).length;
  elements.toast.textContent = `Выбрано ${selectedInStore} из ${total}`;
}

function formatPrice(value) {
  return `${value.toLocaleString("ru-RU", {
    minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
    maximumFractionDigits: 2,
  })} ₽`;
}

function rerender() {
  renderStores();
  renderCategories();
  renderRows();
  drawChart();
}

async function loadStoreCatalog(storeId) {
  state.loadError = "";
  state.dataNotice = "";

  if (!storeDataSources[storeId] || externalCatalogByStore[storeId]) {
    rerender();
    return;
  }

  state.loadingStoreId = storeId;
  renderRows();

  try {
    const response = await fetch(`${storeDataSources[storeId]}?v=${Date.now()}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Не удалось загрузить файл данных: ${response.status}`);
    }

    await wait(450);
    const payload = await response.json();
    externalCatalogByStore[storeId] = normalizeExternalProducts(payload.products || [], storeId);
    externalNoticeByStore[storeId] = payload.notice || `Данные загружены для сети ${stores.find((store) => store.id === storeId).name}`;
    externalUpdatedAtByStore[storeId] = payload.updatedAt || "";
    state.dataNotice = externalNoticeByStore[storeId];
  } catch (error) {
    state.loadError = "Каталог сейчас недоступен. Попробуйте обновить данные позже.";
    console.error(error);
  } finally {
    state.loadingStoreId = null;
    rerender();
  }
}

async function refreshStoreCatalog(storeId, { onlyIfStale = false } = {}) {
  if (storeId !== "auchan" || state.refreshingStoreId || !hasServerApi) return;

  state.loadError = "";
  state.refreshingStoreId = storeId;
  state.dataNotice = onlyIfStale ? "Проверяем актуальность данных Ашана..." : "Обновляем каталог Ашана...";
  renderRows();

  const endpoint = onlyIfStale
    ? "/api/stores/auchan/refresh-if-stale"
    : "/api/stores/auchan/refresh";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      cache: "no-store",
    });
    const payload = await readJsonResponse(response);
    let fallbackApplied = false;

    if (!response.ok) {
      if (payload.fallback?.products?.length) {
        externalCatalogByStore[storeId] = normalizeExternalProducts(payload.fallback.products, storeId);
        externalNoticeByStore[storeId] = payload.fallback.notice || "Ашан: показан последний сохраненный каталог.";
        externalUpdatedAtByStore[storeId] = payload.fallback.updatedAt || "";
        state.dataNotice = "Не удалось обновить каталог Ашана, попробуйте<br />еще раз. Показываем последний сохраненный список.";
        fallbackApplied = true;
      }
      const error = new Error(payload.details || payload.error || "Не удалось обновить каталог Ашана.");
      error.fallbackApplied = fallbackApplied;
      throw error;
    }

    externalCatalogByStore[storeId] = normalizeExternalProducts(payload.products || [], storeId);
    externalNoticeByStore[storeId] = payload.notice || "Ашан: каталог обновлен.";
    externalUpdatedAtByStore[storeId] = payload.updatedAt || "";
    state.dataNotice = externalNoticeByStore[storeId];
  } catch (error) {
    if (!error.fallbackApplied) {
      if (currentCatalog().some((product) => product.storeId === storeId)) {
        state.dataNotice = "Не удалось обновить каталог Ашана, попробуйте<br />еще раз. Показываем последний сохраненный список.";
      } else {
        state.dataNotice = "";
        state.loadError = "Не удалось обновить каталог Ашана, попробуйте еще раз.";
      }
    }
    console.error(error);
  } finally {
    state.refreshingStoreId = null;
    rerender();
  }
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function readJsonResponse(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch (error) {
    const contentType = response.headers.get("content-type") || "неизвестный тип ответа";
    throw new Error(`Сервер вернул не JSON (${contentType}).`);
  }
}

function normalizeExternalProducts(products, storeId) {
  return products
    .filter((product) => categories.includes(product.category))
    .map((product, index) => {
      const price = Number(product.price);
      return {
        id: product.id || `${storeId}-external-${index}`,
        storeId,
        name: product.name,
        category: product.category,
        price,
        color: productColors[index % productColors.length],
        history: Array.isArray(product.history) && product.history.length
          ? product.history.map(Number)
          : makeHistory(price, index, storeId),
      };
    });
}

function updateRefreshUi() {
  const isAuchan = state.storeId === "auchan";
  const isLoading = state.loadingStoreId === state.storeId || state.refreshingStoreId === state.storeId;

  elements.refreshButton.hidden = !isAuchan || !hasServerApi;
  elements.refreshButton.disabled = !isAuchan || !hasServerApi || isLoading;
  elements.refreshButton.classList.toggle("is-loading", state.refreshingStoreId === state.storeId);

  if (!isAuchan) {
    elements.dataStatus.textContent = "";
    return;
  }

  if (state.refreshingStoreId === state.storeId) {
    elements.dataStatus.textContent = "Запрашиваем свежие данные с сайта Ашана...";
    return;
  }

  if (state.dataNotice) {
    elements.dataStatus.innerHTML = state.dataNotice;
    return;
  }

  if (externalNoticeByStore[state.storeId]) {
    elements.dataStatus.textContent = externalNoticeByStore[state.storeId];
    return;
  }

  if (!hasServerApi) {
    elements.dataStatus.textContent = "Публичная версия показывает последний сохраненный каталог.";
    return;
  }

  elements.dataStatus.textContent = "Данные будут обновляться вручную или раз в 2 часа при открытой странице.";
}

elements.storeSwitcher.addEventListener("click", (event) => {
  const button = event.target.closest("[data-store]");
  if (!button) return;
  state.storeId = button.dataset.store;
  state.selectedIds.clear();
  rerender();
  loadStoreCatalog(state.storeId);
});

elements.refreshButton.addEventListener("click", () => {
  refreshStoreCatalog(state.storeId);
});

elements.categoryRow.addEventListener("click", (event) => {
  const button = event.target.closest("[data-category]");
  if (!button) return;
  const category = button.dataset.category;
  if (state.categories.has(category)) {
    state.categories.delete(category);
  } else {
    state.categories.add(category);
  }
  renderCategories();
  renderRows();
});

elements.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderRows();
});

elements.rows.addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-product]");
  if (!checkbox) return;
  if (checkbox.checked) {
    state.selectedIds.add(checkbox.dataset.product);
  } else {
    state.selectedIds.delete(checkbox.dataset.product);
  }
  updateToast();
  drawChart();
});

elements.chart.addEventListener("pointermove", (event) => {
  if (!selectedProducts().length || !chartScale || chartSummaryLocked) return;
  const point = getChartPointer(event);
  chartPointer.x = point.x;
  chartPointer.y = point.y;
  chartPointer.activeIndex = point.activeIndex;
  moveChartTarget(point);
  scheduleChartHint();
});

elements.chart.addEventListener("pointerleave", () => {
  window.clearTimeout(chartHintTimer);
  elements.chartHoverHint.classList.remove("is-visible");
  if (chartSummaryLocked) return;
  const target = elements.chart.querySelector("#chartTarget");
  if (target) target.classList.remove("is-visible");
});

elements.chart.addEventListener("click", (event) => {
  if (!selectedProducts().length || !chartScale) return;
  event.stopPropagation();
  if (chartIgnoreNextClick) {
    chartIgnoreNextClick = false;
    return;
  }

  if (chartSummaryLocked) {
    closeChartSummary();
    return;
  }

  const point = getChartPointer(event);
  chartPointer.x = point.x;
  chartPointer.y = point.y;
  chartPointer.activeIndex = point.activeIndex;
  elements.chartHoverHint.classList.remove("is-visible");
  moveChartTarget(point);
  renderChartSummary(point);
});

elements.chartSummary.addEventListener("click", (event) => {
  event.stopPropagation();
});

function handleChartOutsidePress(event) {
  if (!chartSummaryLocked || elements.chartSummary.contains(event.target)) return;
  closeChartSummary();
  chartIgnoreNextClick = elements.chart.contains(event.target);
}

document.addEventListener("pointerdown", handleChartOutsidePress, true);
document.addEventListener("mousedown", handleChartOutsidePress, true);

rerender();
loadStoreCatalog(state.storeId);

window.setInterval(() => {
  if (hasServerApi && state.storeId === "auchan") {
    refreshStoreCatalog("auchan", { onlyIfStale: true });
  }
}, REFRESH_INTERVAL_MS);

document.addEventListener("visibilitychange", () => {
  if (hasServerApi && !document.hidden && state.storeId === "auchan") {
    refreshStoreCatalog("auchan", { onlyIfStale: true });
  }
});
