const stores = [
  { id: "pyaterochka", name: "Пятерочка", short: "5", color: "#f52618" },
  { id: "perekrestok", name: "Перекресток", short: "X", color: "#00a85a" },
  { id: "dixy", name: "Дикси", short: "Д", color: "#f47b20" },
];

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

const baseCatalog = [
  ["Яблоки Голден, 1 кг", "Фрукты", 156],
  ["Груши Конференция, 1 кг", "Фрукты", 219],
  ["Бананы спелые, 1 кг", "Фрукты", 129],
  ["Апельсины Навелин, 1 кг", "Фрукты", 169],
  ["Мандарины Надоркотт, 1 кг", "Фрукты", 250],
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
  dixy: 0.97,
};

const storeNameAdditions = {
  pyaterochka: ["Красная цена", "Свежий ряд", "Домашняя корзина"],
  perekrestok: ["Market Collection", "Зеленая линия", "Фермерский выбор"],
  dixy: ["Дикси fresh", "Первым делом", "Каждый день"],
};

const state = {
  storeId: "pyaterochka",
  query: "",
  categories: new Set(categories),
  selectedIds: new Set(),
  loadingStoreId: null,
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
  toast: document.querySelector("#selectionToast"),
  averageNote: document.querySelector("#averageNote"),
};

const catalog = stores.flatMap((store) =>
  baseCatalog.map(([name, category, basePrice], index) => {
    const price = Math.round(basePrice * storeFactors[store.id] + ((index % 5) - 2) * 7);
    return {
      id: `${store.id}-${index}`,
      storeId: store.id,
      name: withStoreFlavor(name, store.id, index),
      category,
      price,
      history: makeHistory(price, index, store.id),
    };
  }),
);

const externalCatalogByStore = {};
const externalNoticeByStore = {};

const storeDataSources = {
  pyaterochka: "./data/pyaterochka-products.json",
};

function withStoreFlavor(name, storeId, index) {
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
      return `
        <button class="store-button${active}" type="button" data-store="${store.id}" aria-label="${store.name}">
          <span class="store-logo" style="background:${store.color}">${store.short}</span>
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
    elements.averageNote.textContent = "Загружаем ассортимент и цены...";
    elements.rows.innerHTML = `
      <tr class="loading-row">
        <td colspan="4">
          <span class="loader" aria-hidden="true"></span>
          Загружаем реальные позиции выбранной сети
        </td>
      </tr>
    `;
    updateToast();
    return;
  }

  const products = filteredProducts();
  const currentStore = stores.find((store) => store.id === state.storeId);
  elements.averageNote.textContent = state.dataNotice || externalNoticeByStore[state.storeId] || `Приблизительная закупочная цена для сети ${currentStore.name}`;

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
      const color = categoryColors[product.category];
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
  const selected = currentCatalog().filter((product) => state.selectedIds.has(product.id));
  const width = 980;
  const height = 300;
  const padding = { top: 18, right: 24, bottom: 34, left: 42 };
  const values = selected.flatMap((product) => product.history);
  const minValue = values.length ? Math.floor(Math.min(...values) / 50) * 50 : 0;
  const maxValue = values.length ? Math.ceil(Math.max(...values) / 50) * 50 : 1000;
  const range = Math.max(1, maxValue - minValue);
  const dates = ["24.01", "25.01", "26.01", "27.01", "28.01", "29.01", "30.01"];

  const x = (index) => padding.left + (index * (width - padding.left - padding.right)) / 6;
  const y = (value) => padding.top + ((maxValue - value) * (height - padding.top - padding.bottom)) / range;

  let markup = "";
  for (let i = 0; i <= 8; i += 1) {
    const lineY = padding.top + (i * (height - padding.top - padding.bottom)) / 8;
    const label = Math.round(maxValue - (i * range) / 8);
    markup += `<line class="grid-line" x1="${padding.left}" y1="${lineY}" x2="${width - padding.right}" y2="${lineY}" />`;
    markup += `<text class="axis-text" x="8" y="${lineY + 4}">${label}</text>`;
  }

  dates.forEach((date, index) => {
    markup += `<text class="axis-text" text-anchor="middle" x="${x(index)}" y="${height - 8}">${date}</text>`;
  });

  selected.forEach((product, productIndex) => {
    const color = categoryColors[product.category];
    const path = product.history
      .map((value, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(value)}`)
      .join(" ");
    markup += `<path class="chart-path" d="${path}" stroke="${color}" />`;
    product.history.forEach((value, index) => {
      markup += `<circle class="chart-dot" cx="${x(index)}" cy="${y(value)}" r="4" fill="${color}" />`;
    });
    markup += `<text class="axis-text" x="${width - padding.right - 220}" y="${26 + productIndex * 18}" fill="${color}">${product.name.slice(0, 34)}</text>`;
  });

  elements.chart.innerHTML = markup;
  elements.chartEmpty.style.display = selected.length ? "none" : "flex";
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
    state.dataNotice = externalNoticeByStore[storeId];
  } catch (error) {
    state.loadError = "Не удалось загрузить внешний каталог Пятерочки. Сейчас показ невозможен без обновленного файла данных.";
    console.error(error);
  } finally {
    state.loadingStoreId = null;
    rerender();
  }
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
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
        history: Array.isArray(product.history) && product.history.length
          ? product.history.map(Number)
          : makeHistory(price, index, storeId),
      };
    });
}

elements.storeSwitcher.addEventListener("click", (event) => {
  const button = event.target.closest("[data-store]");
  if (!button) return;
  state.storeId = button.dataset.store;
  state.selectedIds.clear();
  rerender();
  loadStoreCatalog(state.storeId);
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

rerender();
loadStoreCatalog(state.storeId);
