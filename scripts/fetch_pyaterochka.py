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
import os
import sys
import typing
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener, urlopen


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
    parser.add_argument("--timeout-ms", type=float, default=45000, help="Browser and API timeout in milliseconds.")
    parser.add_argument("--proxy", default="", help="Optional explicit proxy URL. By default no proxy is used.")
    parser.add_argument("--use-env-proxy", action="store_true", help="Use HTTPS_PROXY/https_proxy from the environment.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip the fast 5ka.ru block-page check.")
    parser.add_argument("--latitude", type=float, default=55.7558, help="Fallback latitude for detecting a Pyaterochka store.")
    parser.add_argument("--longitude", type=float, default=37.6173, help="Fallback longitude for detecting a Pyaterochka store.")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    ensure_supported_python()
    ensure_typing_override()

    try:
        from pyaterochka_api import PyaterochkaAPI as BasePyaterochkaAPI
    except ImportError as exc:
        print(
            "Could not import pyaterochka_api or one of its dependencies.\n"
            f"Original import error: {exc}\n"
            "Run:\n"
            "  python3.12 -m pip install -r requirements-scraper.txt\n"
            "  python3.12 -m camoufox fetch",
            file=sys.stderr,
        )
        return 2

    PyaterochkaAPI = build_resilient_pyaterochka_api(BasePyaterochkaAPI)

    proxy = resolve_proxy(args)
    try:
        products = await fetch_with_proxy_fallback(args, PyaterochkaAPI, proxy)
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


async def fetch_with_proxy_fallback(args: argparse.Namespace, api_class: type[Any], proxy: str | None) -> list[dict[str, Any]]:
    attempts = [proxy]
    if proxy:
        attempts.append(None)

    errors: list[str] = []
    for attempt_proxy in attempts:
        label = "env proxy" if attempt_proxy else "direct connection"
        try:
            if not args.skip_preflight:
                preflight_error = check_site_access(attempt_proxy)
                if preflight_error:
                    raise RuntimeError(preflight_error)

            print(f"Trying Pyaterochka via {label}")
            async with api_class(
                headless=args.headless,
                timeout_ms=args.timeout_ms,
                proxy=attempt_proxy,
            ) as api:
                sap_code = args.sap_code or await selected_sap_code(api, args.longitude, args.latitude)
                print(f"Using Pyaterochka SAP store code: {sap_code}")

                categories = await fetch_categories(api, sap_code)
                return await fetch_products(api, sap_code, categories, args.category_limit)
        except Exception as exc:
            errors.append(f"{label}: {exc}")
            print(f"Pyaterochka attempt failed via {label}: {exc}", file=sys.stderr)

    raise RuntimeError("; ".join(errors))


def ensure_supported_python() -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("pyaterochka_api requires Python 3.10+. Install Python 3.12 and run this script with python3.12.")


def ensure_typing_override() -> None:
    if hasattr(typing, "override"):
        return

    from typing_extensions import override

    typing.override = override  # type: ignore[attr-defined]


def resolve_proxy(args: argparse.Namespace) -> str | None:
    if args.proxy:
        return args.proxy
    if args.use_env_proxy:
        return (
            os.getenv("HTTPS_PROXY")
            or os.getenv("https_proxy")
            or os.getenv("HTTP_PROXY")
            or os.getenv("http_proxy")
        )
    return None


def check_site_access(proxy: str | None = None) -> str:
    request = Request(
        "https://5ka.ru",
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
        },
    )
    try:
        opener = build_opener(ProxyHandler({"http": proxy, "https": proxy})) if proxy else None
        open_request = opener.open if opener else urlopen
        with open_request(request, timeout=20) as response:
            response.read(1024)
        return ""
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 403 and "Проверьте настройки интернета и VPN" in body:
            return (
                "Could not fetch Pyaterochka data.\n"
                "5ka.ru returned a network/VPN block page before the browser collector started.\n"
                "Disable VPN/proxy or switch to an IP accepted by 5ka.ru, then run the script again.\n"
                f"Original HTTP status: {exc.code}."
            )
        return f"Could not reach 5ka.ru before starting the browser collector: HTTP {exc.code}."
    except (TimeoutError, URLError) as exc:
        return f"Could not reach 5ka.ru before starting the browser collector: {exc}."


class JsonResponse:
    def __init__(self, body: str, url: str) -> None:
        self.body = body
        self.url = url

    def json(self) -> Any:
        return json.loads(self.body)


def build_resilient_pyaterochka_api(base_class: type[Any]) -> type[Any]:
    class ResilientPyaterochkaAPI(base_class):
        async def _warmup(self) -> None:
            from camoufox.async_api import AsyncCamoufox
            from human_requests import HumanBrowser
            from human_requests.abstraction import FetchResponse, Proxy
            from human_requests.network_analyzer.anomaly_sniffer import (
                HeaderAnomalySniffer,
                WaitHeader,
                WaitSource,
            )
            from playwright.async_api import Error as PlaywrightError
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError

            br = await AsyncCamoufox(
                locale="ru-RU",
                headless=self.headless,
                proxy=Proxy(self.proxy).as_dict() if self.proxy else None,
                geoip=True if self.proxy else False,
                block_images=False,
                **self.browser_opts,
            ).start()

            self.session = HumanBrowser.replace(br)
            self.ctx = await self.session.new_context()
            self.page = await self.ctx.new_page()

            sniffer = HeaderAnomalySniffer(
                include_subresources=True,
                url_filter=lambda url: url.startswith(self.CATALOG_URL),
            )
            await sniffer.start(self.ctx)

            await self._warmup_page(PlaywrightError, PlaywrightTimeoutError)
            try:
                await asyncio.wait_for(
                    sniffer.wait(
                        tasks=[
                            WaitHeader(
                                source=WaitSource.REQUEST,
                                headers=["x-app-version", "x-device-id", "x-platform"],
                            )
                        ],
                        timeout_ms=min(self.timeout_ms, 20000),
                    ),
                    timeout=25,
                )
            except Exception:
                pass

            result_sniffer = await sniffer.complete()
            headers: dict[str, set[str]] = {}
            for response_headers in result_sniffer["request"].values():
                for header, values in response_headers.items():
                    headers.setdefault(header, set()).update(values)

            self.unstandard_headers = {key: next(iter(values)) for key, values in headers.items() if values}
            await self._ensure_fallback_headers()

        async def _warmup_page(self, playwright_error: type[Exception], playwright_timeout: type[Exception]) -> None:
            last_error: Exception | None = None
            for _attempt in range(3):
                try:
                    await self.page.goto(self.MAIN_SITE_URL, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    await self._click_robot_if_present(playwright_error, playwright_timeout)
                    try:
                        await self.page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 15000))
                    except Exception:
                        pass
                    try:
                        await self.page.wait_for_timeout(5000)
                    except AttributeError:
                        await asyncio.sleep(5)
                    return
                except Exception as exc:
                    last_error = exc
                    try:
                        await self.page.reload(wait_until="domcontentloaded", timeout=min(self.timeout_ms, 15000))
                    except Exception:
                        pass

            raise RuntimeError(f"Pyaterochka warmup failed after retries: {last_error}")

        async def _ensure_fallback_headers(self) -> None:
            storage = await self.page.local_storage()
            self.unstandard_headers.setdefault("x-platform", "web")
            self.unstandard_headers.setdefault("x-device-id", storage.get("deviceId") or str(uuid.uuid4()))
            self.unstandard_headers.setdefault("x-app-version", "0.1.1.dev")

        async def _click_robot_if_present(
            self,
            playwright_error: type[Exception],
            playwright_timeout: type[Exception],
        ) -> None:
            try:
                await self.page.locator('label[for="is-robot"].captcha-label').click(timeout=self.timeout_ms)
            except (playwright_error, playwright_timeout):
                return

        async def _request(
            self,
            method: Any,
            url: str,
            *,
            json_body: Any | None = None,
            add_unstandard_headers: bool = True,
            credentials: bool = True,
        ) -> FetchResponse:
            headers = {"Accept": "application/json, text/plain, */*"}
            if add_unstandard_headers:
                headers.update(self.unstandard_headers)
            try:
                return await self.page.fetch(
                    url=url,
                    method=method,
                    body=json_body,
                    mode="cors",
                    credentials="include" if credentials else "omit",
                    timeout_ms=self.timeout_ms,
                    referrer=self.MAIN_SITE_URL,
                    headers=headers,
                )
            except Exception as exc:
                return await self._urllib_request(
                    method,
                    url,
                    json_body=json_body,
                    headers=headers,
                    credentials=credentials,
                    browser_error=exc,
                )

        async def _urllib_request(
            self,
            method: Any,
            url: str,
            *,
            json_body: Any | None,
            headers: dict[str, str],
            credentials: bool,
            browser_error: Exception,
        ) -> JsonResponse:
            request_headers = {
                **headers,
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                "Origin": self.MAIN_SITE_URL,
                "Referer": self.MAIN_SITE_URL + "/",
            }
            if credentials:
                cookies = await self.ctx.cookies()
                cookie_header = "; ".join(
                    f"{cookie['name']}={cookie['value']}" for cookie in cookies if cookie.get("name")
                )
                if cookie_header:
                    request_headers["Cookie"] = cookie_header

            data = None
            if json_body is not None:
                data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
                request_headers["Content-Type"] = "application/json"

            method_value = getattr(method, "value", str(method))
            proxy_handler = ProxyHandler({"http": self.proxy, "https": self.proxy}) if self.proxy else ProxyHandler({})
            opener = build_opener(proxy_handler)
            request = Request(url, data=data, headers=request_headers, method=method_value)
            try:
                with opener.open(request, timeout=max(int(self.timeout_ms / 1000), 20)) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    return JsonResponse(body, url)
            except (HTTPError, URLError, TimeoutError) as exc:
                raise RuntimeError(f"browser fetch failed: {browser_error}; urllib fallback failed: {exc}") from exc

    return ResilientPyaterochkaAPI


async def selected_sap_code(api: Any, longitude: float, latitude: float) -> str:
    try:
        store_info = await api.delivery_panel_store()
    except Exception:
        store_info = {}

    selected_store = store_info.get("selectedStore") or {}
    sap_code = selected_store.get("sapCode")
    if sap_code:
        return str(sap_code)

    response = await api.Geolocation.find_store(longitude=longitude, latitude=latitude)
    data = response.json()
    fallback_store = first_store_with_sap_code(data)
    sap_code = fallback_store.get("sapCode") or fallback_store.get("sap_code")
    if not sap_code:
        raise RuntimeError(
            "Could not detect selected Pyaterochka store and geolocation fallback returned no SAP store code."
        )

    return str(sap_code)


def first_store_with_sap_code(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        if value.get("sapCode") or value.get("sap_code"):
            return value
        for nested in value.values():
            result = first_store_with_sap_code(nested)
            if result:
                return result
    elif isinstance(value, list):
        for nested in value:
            result = first_store_with_sap_code(nested)
            if result:
                return result
    return {}


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
