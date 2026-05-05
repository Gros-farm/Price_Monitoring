#!/usr/bin/env python3
"""
Fetch a Pyaterochka catalog snapshot and write it to data/pyaterochka-products.json.

This script intentionally runs outside the static website. GitHub Pages cannot
scrape retailer sites at click time, so the site reads the JSON artifact that
this script creates.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


TARGET_CATEGORIES = ("Фрукты", "Овощи", "Ягоды", "Зелень", "Грибы")

PRODUCT_KEYWORDS = {
    "Фрукты": (
        "яблок",
        "груш",
        "банан",
        "апельсин",
        "мандарин",
        "лимон",
        "лайм",
        "грейпфрут",
        "киви",
        "виноград",
        "персик",
        "нектарин",
        "абрикос",
        "слив",
        "хурм",
        "гранат",
        "ананас",
        "манго",
        "авокадо",
        "кокос",
        "помело",
        "фейхоа",
        "инжир",
        "финик",
    ),
    "Овощи": (
        "огур",
        "томат",
        "помидор",
        "картоф",
        "морков",
        "лук",
        "чеснок",
        "свекл",
        "капуст",
        "брокколи",
        "кабач",
        "баклаж",
        "перец",
        "редис",
        "редьк",
        "реп",
        "тыкв",
        "кукуруз",
        "горош",
        "фасол",
        "сельдер",
        "имбир",
        "батат",
        "топинамбур",
    ),
    "Ягоды": (
        "клубник",
        "земляник",
        "малин",
        "ежевик",
        "голубик",
        "черник",
        "смородин",
        "крыжовник",
        "брусник",
        "клюкв",
        "облепих",
        "вишн",
        "черешн",
        "арбуз",
        "дын",
    ),
    "Зелень": (
        "укроп",
        "петруш",
        "кинз",
        "зеленый лук",
        "зелёный лук",
        "базилик",
        "мята",
        "шпинат",
        "руккол",
        "салат",
        "айсберг",
        "романо",
        "мангольд",
        "щавел",
        "черемш",
        "тимьян",
        "розмарин",
        "орегано",
        "эстрагон",
        "мелисс",
        "микрозел",
    ),
    "Грибы": (
        "шампин",
        "вешен",
        "шиитак",
        "эноки",
        "портобел",
        "белые гриб",
        "лисич",
        "опят",
        "маслят",
        "подберез",
        "подосинов",
        "грузд",
        "рыжик",
        "сморч",
        "трюф",
        "гриб",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Pyaterochka products for the price monitor.")
    parser.add_argument("--output", default="data/pyaterochka-products.json", help="Output JSON path.")
    parser.add_argument("--limit", type=int, default=120, help="Maximum products in the final JSON.")
    parser.add_argument("--category-limit", type=int, default=120, help="Maximum products requested per catalog category.")
    parser.add_argument("--sap-code", default="", help="Known Pyaterochka SAP store code. If omitted, the selected delivery store is used.")
    parser.add_argument("--headless", action="store_true", help="Run Camoufox in headless mode.")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    ensure_supported_python()

    try:
        from pyaterochka_api import PyaterochkaAPI
    except ImportError:
        print(
            "pyaterochka_api is not installed. Run:\n"
            "  python3.12 -m pip install -r requirements-scraper.txt\n"
            "  python3.12 -m camoufox fetch",
            file=sys.stderr,
        )
        return 2

    try:
        async with PyaterochkaAPI(headless=args.headless, timeout_ms=30000) as api:
            sap_code = args.sap_code or await selected_sap_code(api)
            print(f"Using Pyaterochka SAP store code: {sap_code}")

            categories = await fetch_categories(api, sap_code)
            products = await fetch_products(api, sap_code, categories, args.category_limit)
    except Exception as exc:
        print(
            "Could not fetch Pyaterochka data.\n"
            "Most likely 5ka.ru blocked or reset the browser session from this network.\n"
            "Open https://5ka.ru/ in your normal browser, choose city/address, disable VPN if needed, "
            "then run the script again. Original error:\n"
            f"  {exc}",
            file=sys.stderr,
        )
        return 1

    normalized = normalize_products(products, args.limit)
    payload = {
        "storeId": "pyaterochka",
        "source": "pyaterochka_api",
        "sourceUrl": "https://5ka.ru/",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "notice": f"Пятерочка: загружено {len(normalized)} позиций из локального сборщика.",
        "products": normalized,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(normalized)} products to {output_path}")
    return 0


def ensure_supported_python() -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("pyaterochka_api requires Python 3.10+. Install Python 3.12 and run this script with python3.12.")


async def selected_sap_code(api: Any) -> str:
    store_info = await api.delivery_panel_store()
    selected_store = store_info.get("selectedStore") or {}
    sap_code = selected_store.get("sapCode")
    if not sap_code:
        raise RuntimeError("Could not detect selected Pyaterochka store. Try opening 5ka.ru in the browser and selecting a city/address first.")
    return str(sap_code)


async def fetch_categories(api: Any, sap_code: str) -> list[dict[str, Any]]:
    response = await api.Catalog.tree(sap_code_store_id=sap_code, subcategories=True)
    tree = response.json()
    flat = flatten_categories(tree)
    selected = [category for category in flat if is_relevant_category(category.get("name", ""))]

    if not selected:
        selected = flat

    print(f"Found {len(selected)} relevant catalog categories")
    return selected


def flatten_categories(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    stack = list(nodes)
    while stack:
        node = stack.pop(0)
        result.append(node)
        children = node.get("categories") or node.get("children") or []
        stack.extend(child for child in children if isinstance(child, dict))
    return result


def is_relevant_category(name: str) -> bool:
    lowered = name.lower()
    return any(word in lowered for word in ("овощ", "фрукт", "ягод", "зел", "гриб"))


async def fetch_products(api: Any, sap_code: str, categories: list[dict[str, Any]], category_limit: int) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    for category in categories:
        category_id = category.get("id")
        if not category_id:
            continue

        try:
            response = await api.Catalog.products_list(
                category_id=str(category_id),
                sap_code_store_id=sap_code,
                limit=min(max(category_limit, 1), 499),
            )
            data = response.json()
        except Exception as exc:
            print(f"Skipped category {category.get('name')} ({category_id}): {exc}", file=sys.stderr)
            continue

        for product in data.get("products", []):
            product_id = str(product.get("plu") or product.get("id") or product.get("masterDataGroupId") or product.get("name"))
            if product_id in seen:
                continue
            seen.add(product_id)
            product["_sourceCategoryName"] = category.get("name")
            products.append(product)

    print(f"Fetched {len(products)} raw products")
    return products


def normalize_products(products: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for product in products:
        name = str(product.get("name") or product.get("title") or "").strip()
        if not name:
            continue

        category = classify_product(name, str(product.get("_sourceCategoryName") or ""))
        if not category:
            continue

        price = extract_price(product)
        if price is None:
            continue

        product_id = str(product.get("plu") or product.get("id") or slugify(name))
        normalized.append(
            {
                "id": f"pyaterochka-{product_id}",
                "name": name,
                "category": category,
                "price": price,
                "history": build_history(price),
            }
        )

        if len(normalized) >= limit:
            break

    return normalized


def classify_product(name: str, source_category: str) -> Optional[str]:
    combined = f"{name} {source_category}".lower()
    for category, keywords in PRODUCT_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            return category
    return None


def extract_price(product: dict[str, Any]) -> Optional[float]:
    candidates = [
        product.get("price"),
        product.get("regularPrice"),
        product.get("currentPrice"),
        product.get("discountPrice"),
        product.get("promoPrice"),
    ]

    prices = product.get("prices")
    if isinstance(prices, dict):
        candidates.extend(prices.values())

    for candidate in candidates:
        value = coerce_price(candidate)
        if value:
            return value

    for value in walk_values(product):
        price = coerce_price(value)
        if price and 1 <= price <= 100000:
            return price

    return None


def coerce_price(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        price = float(value)
        if price > 10000:
            price = price / 100
        return round(price, 2) if math.isfinite(price) and price > 0 else None
    if isinstance(value, str):
        cleaned = value.replace(",", ".").replace("₽", "").replace(" ", "").strip()
        try:
            return coerce_price(float(cleaned))
        except ValueError:
            return None
    return None


def walk_values(value: Any) -> list[Any]:
    result: list[Any] = []
    if isinstance(value, dict):
        for nested in value.values():
            result.extend(walk_values(nested))
    elif isinstance(value, list):
        for nested in value:
            result.extend(walk_values(nested))
    else:
        result.append(value)
    return result


def build_history(price: float) -> list[float]:
    return [round(price * factor, 2) for factor in (1.04, 1.03, 1.01, 1, 0.99, 1, 1)]


def slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
