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
CATEGORY_PRIORITY = ("Ягоды", "Зелень", "Грибы", "Овощи", "Фрукты")

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

CATALOG_URLS = (
    "https://www.auchan.ru/catalog/ovoschi-frukty-zelen-griby-yagody/ovoschi/",
    "https://www.auchan.ru/catalog/ovoschi-frukty-zelen-griby-yagody/frukty-yagody/",
    "https://www.auchan.ru/catalog/ovoschi-frukty-zelen-griby-yagody/yagody/",
    "https://www.auchan.ru/catalog/ovoschi-frukty-zelen-griby-yagody/zelen-salaty-griby/",
    "https://www.auchan.ru/catalog/ovoschi-frukty-zelen-griby-yagody/griby/",
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
        "лук зелен",
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
    parser.add_argument("--headed", action="store_true", help="Run browser fallback with a visible browser window.")
    parser.add_argument("--no-browser-fallback", action="store_true", help="Disable Camoufox fallback after QRator/HTTP failure.")
    parser.add_argument("--debug-dir", default="", help="Optional directory for browser fallback HTML and screenshots.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        products = fetch_products(
            args.query_delay,
            limit=args.limit,
            browser_fallback=not args.no_browser_fallback,
            headless=not args.headed,
            debug_dir=Path(args.debug_dir) if args.debug_dir else None,
        )
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


def fetch_products(
    query_delay: float,
    *,
    limit: int,
    browser_fallback: bool,
    headless: bool,
    debug_dir: Optional[Path],
) -> list[dict[str, Any]]:
    opener = build_opener()
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    try:
        for query in SEARCH_QUERIES:
            page = fetch_search_page(opener, query)
            collect_products_from_page(page, products, seen)
            if len(products) >= limit:
                break
            time.sleep(query_delay)
    except RuntimeError as exc:
        if not browser_fallback or not is_qrator_or_http_block(exc):
            raise
        print(f"HTTP fetch failed ({exc}). Trying Camoufox browser fallback...", file=sys.stderr)
        return fetch_products_with_browser(query_delay, limit=limit, headless=headless, debug_dir=debug_dir)

    if not products:
        raise RuntimeError(
            "Could not fetch Auchan data. The site returned no product data. "
            "Most likely QRator blocked the scraper session; open https://www.auchan.ru/ "
            "in a browser, check that the catalog works with the current VPN, then retry."
        )

    return products


def collect_products_from_page(page: str, products: list[dict[str, Any]], seen: set[str]) -> None:
    for product in extract_products(page):
        product_id = str(product.get("id") or product.get("url") or product.get("name"))
        if product_id in seen:
            continue
        seen.add(product_id)
        products.append(product)


def is_qrator_or_http_block(error: RuntimeError) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in ("qrator", "qauth", "http 401", "http 403", "no product data"))


def fetch_products_with_browser(
    query_delay: float,
    *,
    limit: int,
    headless: bool,
    debug_dir: Optional[Path],
) -> list[dict[str, Any]]:
    try:
        from camoufox.sync_api import Camoufox
    except ImportError as exc:
        raise RuntimeError(
            "Camoufox is not installed. Run:\n"
            "  python3.12 -m pip install camoufox\n"
            "  python3.12 -m camoufox fetch"
        ) from exc

    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    with Camoufox(headless=headless, locale="ru-RU") as browser:
        page = browser.new_page()
        page.set_default_timeout(8000)

        for catalog_url in CATALOG_URLS:
            try:
                page.goto(catalog_url, wait_until="domcontentloaded", timeout=15000)
                wait_for_browser_page(page)
                body = page.content()
                save_browser_debug(debug_dir, catalog_url, body, page)
            except Exception as exc:
                print(f"Skipped Auchan category {catalog_url!r}: {exc}", file=sys.stderr)
                continue

            if "qauth.js" in body or "__qrator" in body:
                raise RuntimeError("Auchan returned QRator qauth challenge in browser fallback.")

            collect_products_from_page(body, products, seen)
            print(f"Auchan browser category {catalog_url!r}: {len(products)} raw products total", file=sys.stderr)
            if len(products) >= limit:
                break
            time.sleep(query_delay)

    if not products:
        raise RuntimeError("Camoufox opened Auchan pages, but no product data was detected.")

    return products


def save_browser_debug(debug_dir: Optional[Path], label: str, body: str, page: Any) -> None:
    if not debug_dir:
        return

    debug_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(label.rstrip("/").split("/")[-1]) or "page"
    (debug_dir / f"{slug}.html").write_text(body, encoding="utf-8")
    try:
        page.screenshot(path=str(debug_dir / f"{slug}.png"), full_page=False)
    except Exception as exc:
        print(f"Could not save screenshot for {label!r}: {exc}", file=sys.stderr)


def wait_for_browser_page(page: Any) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=12000)
    except Exception:
        pass

    selectors = (
        "article",
        "[data-testid*='product']",
        "[class*='product']",
        "script#__NEXT_DATA__",
    )
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=5000)
            return
        except Exception:
            continue


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
    card_pattern = re.compile(
        r"<a[^>]+class=[\"'][^\"']*productCardContentPanel_link[^\"']*[\"'][^>]+"
        r"title=[\"'](?P<title>[^\"']+)[\"'][^>]+href=[\"'](?P<href>[^\"']+)[\"'][^>]*>\s*"
        r"<p[^>]+class=[\"'][^\"']*productCardContentPanel_name[^\"']*[\"'][^>]*>"
        r"(?P<name>.*?)</p>\s*</a>.*?"
        r"<div[^>]+class=[\"'][^\"']*productCardContentPanel_price[^\"']*[\"'][^>]*>"
        r"(?P<price>\d[\d\s]*(?:[,.]\d{1,2})?)",
        re.S,
    )
    for match in card_pattern.finditer(page):
        name = clean_text(match.group("name")) or clean_text(match.group("title"))
        href = html.unescape(match.group("href"))
        result.append(
            {
                "name": name,
                "price": match.group("price"),
                "url": f"https://www.auchan.ru{href}" if href.startswith("/") else href,
            }
        )

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
    for category in CATEGORY_PRIORITY:
        keywords = PRODUCT_KEYWORDS[category]
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
