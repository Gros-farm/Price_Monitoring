#!/usr/bin/env python3
"""
Fetch a Metro catalog snapshot and write it to data/metro-products.json.

Metro protects direct category pages with a browser challenge, but its Nuxt app
uses a GraphQL endpoint that returns the same product data after the homepage
sets public store cookies.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener


SOURCE_URL = "https://online.metro-cc.ru/"
GRAPHQL_URL = "https://online.metro-cc.ru/graphql"
DEFAULT_STORE_ID = 10
TARGET_CATEGORIES = {
    "Овощи": 413430,
    "Фрукты": 413432,
    "Ягоды": 413435,
    "Зелень": 413441,
    "Грибы": 413440,
}

GET_PRODUCTS_QUERY = """
query getProductsByCategory(
  $storeId: Int!,
  $text: String,
  $filters: [FieldFilter],
  $from: Int!,
  $size: Int!,
  $attributes: [AttributeFilter],
  $in_stock: Boolean,
  $eshop_order: Boolean,
  $is_action: Boolean,
  $priceLevelsOnline: Boolean,
  $gurman: Boolean
) {
  search(text: $text) {
    products(
      storeId: $storeId,
      inStock: $in_stock,
      eshopAvailability: $eshop_order,
      isPromo: $is_action,
      priceLevelsOnline: $priceLevelsOnline,
      attributeFilters: $attributes,
      from: $from,
      size: $size,
      fieldFilters: $filters,
      gurman: $gurman
    ) {
      total
      products {
        id
        slug
        name
        article
        category_id
        category { name }
        images
        packing { size type }
        stocks {
          value
          text
          scale
          eshop_availability
          prices {
            price
            old_price
            is_promo
            discount
          }
          prices_per_unit {
            price
            old_price
            is_promo
            discount
          }
        }
      }
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Metro products for the price monitor.")
    parser.add_argument("--output", default="data/metro-products.json", help="Output JSON path.")
    parser.add_argument("--limit", type=int, default=120, help="Maximum products in the final JSON.")
    parser.add_argument("--category-limit", type=int, default=80, help="Maximum products requested per Metro category.")
    parser.add_argument("--store-id", type=int, default=DEFAULT_STORE_ID, help="Metro store id used by online.metro-cc.ru.")
    parser.add_argument("--request-delay", type=float, default=0.35, help="Delay between category GraphQL requests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        products = fetch_products(
            store_id=args.store_id,
            category_limit=args.category_limit,
            request_delay=args.request_delay,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    normalized = normalize_products(products, args.limit)
    if not normalized:
        print("Metro returned data, but no products with prices were detected.", file=sys.stderr)
        return 1

    payload = {
        "storeId": "metro",
        "source": "online.metro-cc.ru",
        "sourceUrl": SOURCE_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "notice": f"Metro: загружено {len(normalized)} позиций с сайта.",
        "products": normalized,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(normalized)} products to {output_path}")
    return 0


def fetch_products(*, store_id: int, category_limit: int, request_delay: float) -> list[dict[str, Any]]:
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    warm_up_session(opener)

    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_category = min(max(category_limit, 1), 200)

    for category_name, category_id in TARGET_CATEGORIES.items():
        try:
            data = graphql_request(
                opener,
                operation_name="getProductsByCategory",
                query=GET_PRODUCTS_QUERY,
                variables={
                    "storeId": store_id,
                    "text": "",
                    "filters": [{"field": "category_id", "value": str(category_id)}],
                    "from": 0,
                    "size": per_category,
                    "attributes": [],
                    "in_stock": True,
                    "eshop_order": True,
                    "is_action": False,
                    "priceLevelsOnline": False,
                    "gurman": False,
                },
            )
        except RuntimeError as exc:
            print(f"Skipped Metro category {category_name} ({category_id}): {exc}", file=sys.stderr)
            continue

        result = data.get("data", {}).get("search", {}).get("products", {})
        for product in result.get("products", []):
            product_id = str(product.get("article") or product.get("id") or product.get("slug") or product.get("name"))
            if product_id in seen:
                continue
            seen.add(product_id)
            product["_sourceCategoryName"] = category_name
            products.append(product)

        print(f"Metro category {category_name}: {len(result.get('products', []))} products, {result.get('total')} total")
        time.sleep(request_delay)

    if not products:
        raise RuntimeError(
            "Could not fetch Metro data. Homepage is reachable, but GraphQL returned no category products."
        )

    return products


def warm_up_session(opener: Any) -> None:
    request = Request(SOURCE_URL, headers=default_headers())
    try:
        with opener.open(request, timeout=30) as response:
            response.read(1024)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Metro homepage request failed: {exc}") from exc


def graphql_request(
    opener: Any,
    *,
    operation_name: str,
    query: str,
    variables: dict[str, Any],
    attempts: int = 3,
) -> dict[str, Any]:
    body = json.dumps(
        {
            "operationName": operation_name,
            "variables": variables,
            "query": query,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    for attempt in range(1, attempts + 1):
        request = Request(
            GRAPHQL_URL,
            data=body,
            headers={
                **default_headers(),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://online.metro-cc.ru",
                "Referer": SOURCE_URL,
            },
            method="POST",
        )

        try:
            with opener.open(request, timeout=40) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == attempts:
                raise RuntimeError(f"Metro GraphQL request failed: {exc}") from exc
            time.sleep(0.8 * attempt)
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            if "bp_chl" in raw or "captcha" in raw.lower():
                raise RuntimeError("Metro returned a browser challenge instead of GraphQL JSON.") from exc
            raise RuntimeError("Metro returned invalid GraphQL JSON.") from exc

        if data.get("errors"):
            raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
        return data

    raise RuntimeError("Metro GraphQL request failed.")


def default_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.7,en;q=0.6",
        "Cache-Control": "no-cache",
    }


def normalize_products(products: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for product in products:
        name = clean_text(str(product.get("name") or ""))
        if not name:
            continue

        price = extract_price(product)
        if price is None:
            continue

        category = classify_product(product)
        product_id = str(product.get("article") or product.get("id") or product.get("slug") or slugify(name))
        normalized.append(
            {
                "id": f"metro-{slugify(product_id)}",
                "name": name,
                "category": category,
                "price": price,
                "history": build_history(price),
            }
        )

        if len(normalized) >= limit:
            break

    return normalized


def classify_product(product: dict[str, Any]) -> str:
    source_category = str(product.get("_sourceCategoryName") or "")
    if source_category in TARGET_CATEGORIES:
        return source_category

    category = product.get("category")
    category_name = str(category.get("name") if isinstance(category, dict) else "")
    return category_name if category_name in TARGET_CATEGORIES else "Овощи"


def extract_price(product: dict[str, Any]) -> Optional[float]:
    for stock in product.get("stocks") or []:
        if not isinstance(stock, dict):
            continue
        prices = stock.get("prices")
        if isinstance(prices, dict):
            value = coerce_price(prices.get("price"))
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


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


if __name__ == "__main__":
    raise SystemExit(main())
