#!/usr/bin/env python3
"""
Fetch an Auchan catalog snapshot and write it to data/auchan-products.json.

The script is intentionally separate from the static frontend. It can be
started by server.js locally, or by a scheduled job later. If Auchan returns a
QRator challenge instead of catalog HTML, the script fails without overwriting
the previous cache.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener


TARGET_CATEGORIES = ("Фрукты", "Овощи", "Ягоды", "Зелень", "Грибы")

SEARCH_QUERIES = (
    "томаты",
    "огурцы",
    "бананы",
    "яблоки",
    "лимоны",
    "авокадо",
    "клубника",
    "голубика",
    "укроп",
    "петрушка",
    "шампиньоны",
    "вешенки",
)

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
    parser = argparse.ArgumentParser(description="Fetch Auchan products for the price monitor.")
    parser.add_argument("--output", default="data/auchan-products.json", help="Output JSON path.")
    parser.add_argument("--limit", type=int, default=120, help="Maximum products in the final JSON.")
    parser.add_argument("--query-delay", type=float, default=0.6, help="Delay between search requests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        products = fetch_products(args.query_delay)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    normalized = normalize_products(products, args.limit)
    if not normalized:
        print("Auchan returned pages, but no matching product cards were detected.", file=sys.stderr)
        return 1

    payload = {
        "storeId": "auchan",
        "source": "auchan.ru",
        "sourceUrl": "https://www.auchan.ru/",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "notice": f"Ашан: загружено {len(normalized)} позиций с сайта.",
        "products": normalized,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(normalized)} products to {output_path}")
    return 0


def fetch_products(query_delay: float) -> list[dict[str, Any]]:
    opener = build_opener()
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    for query in SEARCH_QUERIES:
        page = fetch_search_page(opener, query)
        for product in extract_products(page):
            product_id = str(product.get("id") or product.get("url") or product.get("name"))
            if product_id in seen:
                continue
            seen.add(product_id)
            products.append(product)
        time.sleep(query_delay)

    if not products:
        raise RuntimeError(
            "Could not fetch Auchan data. The site returned no product data. "
            "Most likely QRator blocked the scraper session; open https://www.auchan.ru/ "
            "in a browser, check that the catalog works with the current VPN, then retry."
        )

    return products


def fetch_search_page(opener: Any, query: str) -> str:
    url = f"https://www.auchan.ru/search/?text={quote(query)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.7,en;q=0.6",
            "Cache-Control": "no-cache",
        },
    )

    try:
        with opener.open(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401 and "qauth" in body:
            raise RuntimeError("Auchan returned QRator qauth challenge instead of search results.")
        raise RuntimeError(f"Auchan search request failed with HTTP {exc.code}.")
    except URLError as exc:
        raise RuntimeError(f"Auchan search request failed: {exc}") from exc

    if "qauth.js" in body or "__qrator" in body:
        raise RuntimeError("Auchan returned QRator qauth challenge instead of search results.")

    return body


def extract_products(page: str) -> list[dict[str, Any]]:
    products = []
    products.extend(extract_json_ld_products(page))
    products.extend(extract_next_data_products(page))
    products.extend(extract_card_products(page))
    return products


def extract_json_ld_products(page: str) -> list[dict[str, Any]]:
    result = []
    for match in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page, re.S):
        raw = html.unescape(match.group(1)).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in walk_dicts(data):
            item_type = item.get("@type")
            if item_type == "Product" or (isinstance(item_type, list) and "Product" in item_type):
                result.append(item)
    return result


def extract_next_data_products(page: str) -> list[dict[str, Any]]:
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
    if not match:
        return []

    try:
        data = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError:
        return []

    result = []
    for item in walk_dicts(data):
        name = item.get("name") or item.get("title")
        price = extract_price(item)
        if name and price:
            result.append(item)
    return result


def extract_card_products(page: str) -> list[dict[str, Any]]:
    result = []
    for block in re.findall(r"(<article\b.*?</article>)", page, re.S):
        name_match = re.search(r'(?:aria-label|title)=["\']([^"\']{3,160})["\']', block)
        if not name_match:
            name_match = re.search(r"<h[2-4][^>]*>(.*?)</h[2-4]>", block, re.S)
        price_match = re.search(r"(\d[\d\s]{0,6}(?:[,.]\d{1,2})?)\s*₽", block)
        if name_match and price_match:
            result.append(
                {
                    "name": clean_text(name_match.group(1)),
                    "price": price_match.group(1),
                }
            )
    return result


def normalize_products(products: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for product in products:
        name = clean_text(str(product.get("name") or product.get("title") or ""))
        if not name:
            continue

        category = classify_product(name)
        if not category:
            continue

        price = extract_price(product)
        if price is None:
            continue

        product_id = str(product.get("sku") or product.get("id") or product.get("url") or slugify(name))
        normalized.append(
            {
                "id": f"auchan-{slugify(product_id)}",
                "name": name,
                "category": category,
                "price": price,
                "history": build_history(price),
            }
        )

        if len(normalized) >= limit:
            break

    return normalized


def classify_product(name: str) -> Optional[str]:
    lowered = name.lower()
    for category, keywords in PRODUCT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return None


def extract_price(product: dict[str, Any]) -> Optional[float]:
    candidates = [
        product.get("price"),
        product.get("lowPrice"),
        product.get("highPrice"),
        product.get("regularPrice"),
        product.get("currentPrice"),
        product.get("discountPrice"),
    ]

    offers = product.get("offers")
    if isinstance(offers, dict):
        candidates.extend(offers.values())

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
        cleaned = value.replace(",", ".").replace("₽", "").replace("&nbsp;", "").replace(" ", "").strip()
        try:
            return coerce_price(float(cleaned))
        except ValueError:
            return None
    return None


def walk_dicts(value: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(value, dict):
        result.append(value)
        for nested in value.values():
            result.extend(walk_dicts(nested))
    elif isinstance(value, list):
        for nested in value:
            result.extend(walk_dicts(nested))
    return result


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


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


if __name__ == "__main__":
    raise SystemExit(main())
