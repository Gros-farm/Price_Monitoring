#!/usr/bin/env python3
"""
Fetch a normalized catalog snapshot from grocery delivery aggregators.

This collector is intentionally generic: aggregators change frontends often, so
it extracts product-like objects from public page state (JSON-LD, Next data,
Redux state) instead of depending on one private endpoint.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener


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

SEARCH_QUERIES = (
    "огурцы",
    "помидоры",
    "картофель",
    "морковь",
    "лук",
    "бананы",
    "яблоки",
    "апельсины",
    "лимоны",
    "авокадо",
    "клубника",
    "голубика",
    "укроп",
    "петрушка",
    "шампиньоны",
)

STORE_ALIASES = {
    "auchan": ("ашан", "auchan"),
    "metro": ("metro", "метро"),
    "pyaterochka": ("пятерочка", "пятёрочка", "5ka", "x5"),
    "perekrestok": ("перекресток", "перекрёсток", "perekrestok", "x5"),
}

PROVIDER_HOSTS = {
    "kuper": ("https://kuper.ru", "https://sbermarket.ru"),
    "yandex": ("https://eda.yandex.ru",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch grocery products from delivery aggregators.")
    parser.add_argument("--output", default="data/aggregator-products.json", help="Output JSON path.")
    parser.add_argument("--provider", choices=sorted(PROVIDER_HOSTS), default="kuper")
    parser.add_argument("--store", required=True, help="Store id: auchan, metro, pyaterochka, perekrestok.")
    parser.add_argument("--limit", type=int, default=120, help="Maximum products in the final JSON.")
    parser.add_argument("--query-limit", type=int, default=18, help="Maximum search queries to try.")
    parser.add_argument("--request-delay", type=float, default=0.8, help="Delay between aggregator requests.")
    parser.add_argument("--browser-fallback", action="store_true", help="Render pages with Playwright when HTTP is blocked.")
    parser.add_argument("--headless", action="store_true", help="Run browser fallback in headless mode.")
    parser.add_argument("--proxy", default="", help="Optional explicit proxy URL.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store_id = normalize_store_id(args.store)

    try:
        products = fetch_products(args, store_id)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    normalized = normalize_products(products, store_id, args.provider, args.limit)
    if not normalized:
        print(f"{args.provider}: pages were fetched, but no matching products with prices were detected.", file=sys.stderr)
        return 1

    payload = {
        "storeId": store_id,
        "source": f"aggregator:{args.provider}",
        "sourceUrl": PROVIDER_HOSTS[args.provider][0],
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "notice": f"{store_display_name(store_id)}: загружено {len(normalized)} позиций через агрегатор {args.provider}.",
        "products": normalized,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(normalized)} {store_id} products from {args.provider} to {output_path}")
    return 0


def fetch_products(args: argparse.Namespace, store_id: str) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    errors: list[str] = []

    for url in build_search_urls(args.provider, store_id, args.query_limit):
        try:
            text = fetch_text(url, args.proxy)
        except RuntimeError as exc:
            if not args.browser_fallback:
                errors.append(f"{url}: {exc}")
                continue
            try:
                text = asyncio.run(fetch_text_with_browser(url, args.headless, args.proxy))
            except RuntimeError as browser_exc:
                errors.append(f"{url}: http failed: {exc}; browser failed: {browser_exc}")
                continue

        extracted = extract_product_candidates(text, url, args.provider)
        for product in extracted:
            if not product_matches_store(product, store_id):
                continue
            product_id = str(product.get("id") or product.get("sku") or product.get("url") or product.get("name"))
            if product_id in seen:
                continue
            seen.add(product_id)
            products.append(product)

        print(f"{args.provider}: {url} -> {len(extracted)} candidates, {len(products)} matched")
        if len(products) >= args.limit:
            break
        time.sleep(args.request_delay)

    if not products:
        if not errors:
            errors.append(
                "public pages loaded, but no product candidates matched; "
                "the aggregator may have returned a block page or changed its markup"
            )
        raise RuntimeError(
            f"Could not fetch {store_id} data from aggregator {args.provider}. "
            f"Tried public storefront pages; last errors: {errors[-3:]}"
        )

    return products


def build_search_urls(provider: str, store_id: str, query_limit: int) -> list[str]:
    urls: list[str] = []
    aliases = STORE_ALIASES.get(store_id, (store_id,))
    queries = SEARCH_QUERIES[: max(1, query_limit)]

    for host in PROVIDER_HOSTS[provider]:
        for query in queries:
            search_text = f"{aliases[0]} {query}"
            if provider == "kuper":
                urls.append(f"{host}/search?{urlencode({'keywords': search_text})}")
            elif provider == "yandex":
                urls.append(f"{host}/search?{urlencode({'text': search_text})}")

    return urls


def fetch_text(url: str, proxy: str = "") -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }
    opener = build_opener(ProxyHandler({"http": proxy, "https": proxy}) if proxy else ProxyHandler({}))
    request = Request(url, headers=headers)
    try:
        with opener.open(request, timeout=35) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, ConnectionResetError) as exc:
        raise RuntimeError(str(exc)) from exc


async def fetch_text_with_browser(url: str, headless: bool, proxy: str = "") -> str:
    try:
        return await fetch_text_with_camoufox(url, headless, proxy)
    except RuntimeError as camoufox_error:
        try:
            return await fetch_text_with_playwright(url, headless, proxy)
        except RuntimeError as playwright_error:
            raise RuntimeError(f"Camoufox failed: {camoufox_error}; Playwright failed: {playwright_error}") from playwright_error


async def fetch_text_with_camoufox(url: str, headless: bool, proxy: str = "") -> str:
    try:
        from camoufox.async_api import AsyncCamoufox
    except ImportError as exc:
        raise RuntimeError("Camoufox is not installed for browser fallback.") from exc

    try:
        browser = await AsyncCamoufox(
            locale="ru-RU",
            headless=headless,
            proxy={"server": proxy} if proxy else None,
            geoip=True if proxy else False,
        ).start()
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc

    try:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        return await page.content()
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    finally:
        await browser.close()


async def fetch_text_with_playwright(url: str, headless: bool, proxy: str = "") -> str:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed for browser fallback.") from exc

    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.launch(
                headless=headless,
                proxy={"server": proxy} if proxy else None,
            )
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc

        try:
            page = await browser.new_page(locale="ru-RU")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            return await page.content()
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            await browser.close()


def extract_product_candidates(text: str, source_url: str, provider: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for script_body in extract_json_script_bodies(text):
        parsed = parse_json_like(script_body)
        if parsed is None:
            continue
        for node in walk_json(parsed):
            product = product_from_node(node, source_url, provider)
            if product:
                candidates.append(product)

    candidates.extend(products_from_plain_html(text, source_url, provider))
    return dedupe_candidates(candidates)


def extract_json_script_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    for match in re.finditer(r"<script[^>]*>(.*?)</script>", text, flags=re.IGNORECASE | re.DOTALL):
        body = html.unescape(match.group(1).strip())
        if not body:
            continue
        if body.startswith("{") or body.startswith("["):
            bodies.append(body)
            continue
        for pattern in (
            r"window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;",
            r"window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*;",
            r"self\.__next_f\.push\(\s*(\[.*?\])\s*\)",
        ):
            bodies.extend(m.group(1) for m in re.finditer(pattern, body, flags=re.DOTALL))
    return bodies


def parse_json_like(value: str) -> Any | None:
    value = value.strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None

    # Next.js app-router chunks often contain JSON as nested strings.
    if isinstance(parsed, list):
        expanded = []
        for item in parsed:
            if isinstance(item, str) and ("products" in item.lower() or "price" in item.lower()):
                nested = parse_embedded_json_from_string(item)
                expanded.append(nested if nested is not None else item)
            else:
                expanded.append(item)
        return expanded
    return parsed


def parse_embedded_json_from_string(value: str) -> Any | None:
    for match in re.finditer(r"(\{.*\}|\[.*\])", value, flags=re.DOTALL):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def walk_json(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            found.append(current)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def product_from_node(node: dict[str, Any], source_url: str, provider: str) -> dict[str, Any] | None:
    name = first_text(node, ("name", "title", "productName", "displayName"))
    if not name:
        return None

    price = first_price(node)
    if price is None:
        return None

    product_url = first_text(node, ("url", "canonicalUrl", "link", "href"))
    if product_url and product_url.startswith("/"):
        product_url = PROVIDER_HOSTS[provider][0] + product_url

    return {
        "id": first_text(node, ("id", "sku", "productId", "offerId", "slug")) or slugify(name),
        "name": clean_text(name),
        "price": price,
        "url": product_url or source_url,
        "store": first_text(node, ("storeName", "retailerName", "merchantName", "shopName", "brand")),
        "raw": node,
    }


def products_from_plain_html(text: str, source_url: str, provider: str) -> list[dict[str, Any]]:
    stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    stripped = re.sub(r"<[^>]+>", "\n", stripped)
    lines = [clean_text(line) for line in html.unescape(stripped).splitlines()]
    lines = [line for line in lines if line]

    products: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if "₽" not in line:
            continue
        price = parse_price(line)
        if price is None:
            continue

        name = ""
        for candidate in reversed(lines[max(0, index - 4) : index]):
            if len(candidate) >= 5 and not parse_price(candidate):
                name = candidate
                break
        if not name:
            continue

        products.append(
            {
                "id": slugify(f"{provider}-{name}-{price}"),
                "name": name,
                "price": price,
                "url": source_url,
                "store": "",
                "raw": {},
            }
        )
    return products


def first_text(node: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def first_price(node: dict[str, Any]) -> float | None:
    for key in ("price", "currentPrice", "priceValue", "finalPrice", "discountPrice", "value"):
        price = price_from_value(node.get(key))
        if price is not None:
            return price

    offers = node.get("offers")
    if isinstance(offers, dict):
        return first_price(offers)
    if isinstance(offers, list):
        for offer in offers:
            if isinstance(offer, dict):
                price = first_price(offer)
                if price is not None:
                    return price

    return None


def price_from_value(value: Any) -> float | None:
    if isinstance(value, (int, float)) and value > 0:
        return round(float(value) / 100, 2) if value > 10000 else round(float(value), 2)
    if isinstance(value, str):
        return parse_price(value)
    if isinstance(value, dict):
        for key in ("amount", "value", "price", "units"):
            price = price_from_value(value.get(key))
            if price is not None:
                return price
    return None


def parse_price(value: str) -> float | None:
    match = re.search(r"(\d[\d\s\u00a0]*(?:[,.]\d{1,2})?)\s*(?:₽|руб|р\b)", value, flags=re.IGNORECASE)
    if not match:
        return None
    normalized = match.group(1).replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        price = float(normalized)
    except ValueError:
        return None
    return round(price, 2) if price > 0 else None


def product_matches_store(product: dict[str, Any], store_id: str) -> bool:
    aliases = STORE_ALIASES.get(store_id, (store_id,))
    haystack = " ".join(
        str(product.get(key, "")) for key in ("name", "store", "url")
    ).lower()
    if any(alias.lower() in haystack for alias in aliases):
        return True

    # Some aggregator search pages omit the store name in product cards. Keep
    # produce-like matches; provider ordering and cache fallback protect us if
    # the page is not store-specific enough.
    return classify_product(str(product.get("name", ""))) is not None


def normalize_products(products: list[dict[str, Any]], store_id: str, provider: str, limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for product in products:
        name = clean_text(str(product.get("name") or ""))
        category = classify_product(name)
        if not name or not category:
            continue
        price = product.get("price")
        if not isinstance(price, (int, float)) or price <= 0:
            continue

        product_id = slugify(str(product.get("id") or name))
        if product_id in seen:
            continue
        seen.add(product_id)
        normalized.append(
            {
                "id": f"{store_id}-{provider}-{product_id}",
                "name": name,
                "category": category,
                "price": round(float(price), 2),
                "history": build_history(float(price)),
            }
        )
        if len(normalized) >= limit:
            break
    return normalized


def classify_product(name: str) -> str | None:
    lowered = name.lower()
    for category in TARGET_CATEGORIES:
        if any(keyword in lowered for keyword in PRODUCT_KEYWORDS[category]):
            return category
    return None


def build_history(price: float) -> list[float]:
    return [
        round(price * 1.08, 2),
        round(price * 1.03, 2),
        round(price * 0.99, 2),
        round(price, 2),
    ]


def dedupe_candidates(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for product in products:
        key = slugify(f"{product.get('name')}:{product.get('price')}:{product.get('url')}")
        if key in seen:
            continue
        seen.add(key)
        result.append(product)
    return result


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "-", value.lower()).strip("-")
    return slug[:96] or "product"


def normalize_store_id(store: str) -> str:
    normalized = store.lower().strip()
    aliases = {
        "пятерочка": "pyaterochka",
        "пятёрочка": "pyaterochka",
        "5ka": "pyaterochka",
        "ашан": "auchan",
        "метро": "metro",
        "перекресток": "perekrestok",
        "перекрёсток": "perekrestok",
    }
    return aliases.get(normalized, normalized)


def store_display_name(store_id: str) -> str:
    return {
        "auchan": "Ашан",
        "metro": "Metro",
        "pyaterochka": "Пятерочка",
        "perekrestok": "Перекресток",
    }.get(store_id, store_id)


if __name__ == "__main__":
    raise SystemExit(main())
