#!/usr/bin/env python3
"""
Run store data collectors and keep agent status metadata.

Each store adapter writes a normalized JSON file into data/. The frontend and
server only read those files, so parsing failures never erase the last good
catalog.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "scripts" / "agents"
DEFAULT_DATA_DIR = ROOT / "data"
STATUS_FILE_NAME = "agent-status.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run price monitor store agents.")
    parser.add_argument("--store", action="append", help="Store id to update. Repeat for multiple stores.")
    parser.add_argument("--all", action="store_true", help="Update every configured store.")
    parser.add_argument("--data-dir", default=os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR)))
    parser.add_argument("--config", default=str(AGENT_DIR / "stores.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = read_json(Path(args.config))
    stores = config.keys() if args.all else args.store

    if not stores:
        print("Choose --store <id> or --all.", file=sys.stderr)
        return 2

    data_dir = Path(args.data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    status_path = data_dir / STATUS_FILE_NAME
    status = read_json(status_path, default={"stores": {}})

    exit_code = 0
    for store_id in stores:
        if store_id not in config:
            print(f"Unknown store: {store_id}", file=sys.stderr)
            status["stores"][store_id] = build_status("failed", error="Unknown store")
            exit_code = 2
            continue

        result = run_store(store_id, config[store_id], data_dir)
        status["stores"][store_id] = result
        if result["status"] != "success":
            exit_code = 1

    status["updatedAt"] = now_iso()
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return exit_code


def run_store(store_id: str, store: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    output_path = data_dir / store["dataFile"]
    output_label = relative_label(output_path)
    started_at = now_iso()
    provider_errors: list[dict[str, Any]] = []

    print(f"[{store_id}] updating {store['name']} -> {output_path}")
    for provider in store_providers(store):
        result = run_provider(store, provider, output_path)
        if result["return_code"] == 0:
            payload = read_json(output_path, default={})
            product_count = len(payload.get("products", [])) if isinstance(payload.get("products"), list) else 0
            return build_status(
                "success",
                started_at=started_at,
                finished_at=now_iso(),
                store=store,
                provider=provider,
                output_file=output_label,
                product_count=product_count,
                source_updated_at=payload.get("updatedAt"),
                providers_attempted=provider_errors + [provider_result_summary(provider, result)],
            )

        print(result["error"], file=sys.stderr)
        provider_errors.append(provider_result_summary(provider, result))

    cached_payload = read_json(output_path, default={})
    cached_products = cached_payload.get("products") if isinstance(cached_payload, dict) else None
    if isinstance(cached_products, list) and cached_products:
        return build_status(
            "success",
            started_at=started_at,
            finished_at=now_iso(),
            store=store,
            output_file=output_label,
            product_count=len(cached_products),
            source_updated_at=cached_payload.get("updatedAt"),
            used_cached_data=True,
            warning=(
                "All store providers failed, so the agent kept the last saved catalog. "
                "See providers_attempted for collector failures."
            ),
            error=provider_errors[-1]["error"] if provider_errors else None,
            providers_attempted=provider_errors,
        )

    return build_status(
        "failed",
        started_at=started_at,
        finished_at=now_iso(),
        store=store,
        error=provider_errors[-1]["error"] if provider_errors else "No provider returned data.",
        output_file=output_label,
        providers_attempted=provider_errors,
    )


def store_providers(store: dict[str, Any]) -> list[dict[str, Any]]:
    providers = store.get("providers")
    if isinstance(providers, list) and providers:
        return providers

    return [
        {
            "id": "direct",
            "name": "Direct store collector",
            "source": store.get("source"),
            "python": store.get("python"),
            "command": store.get("command", []),
            "timeoutSeconds": store.get("timeoutSeconds", 180),
        }
    ]


def run_provider(store: dict[str, Any], provider: dict[str, Any], output_path: Path) -> dict[str, Any]:
    python_executable = provider.get("python") or store.get("python") or sys.executable
    command = [python_executable, *provider["command"], "--output", str(output_path)]
    timeout_seconds = int(provider.get("timeoutSeconds", store.get("timeoutSeconds", 180)))

    print(f"  provider {provider.get('id', 'unknown')} ({provider.get('source', store.get('source', 'unknown'))})")
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        output = "\n".join(normalize_process_text(part) for part in (exc.stderr, exc.stdout) if part)
        return {
            "return_code": 124,
            "error": f"Store provider timed out after {timeout_seconds}s." + (f"\n{output}" if output else ""),
        }

    result = {
        "return_code": completed.returncode,
    }
    if completed.returncode != 0:
        result["error"] = truncate_text((completed.stderr or completed.stdout or f"exit code {completed.returncode}").strip())
    return result


def provider_result_summary(provider: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "id": provider.get("id"),
        "name": provider.get("name"),
        "source": provider.get("source"),
        "return_code": result.get("return_code"),
    }
    if result.get("error"):
        summary["error"] = truncate_text(str(result["error"]))
    return {key: value for key, value in summary.items() if value is not None}


def truncate_text(value: str, limit: int = 2500) -> str:
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "\n... truncated ..."


def build_status(status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": status,
        "checkedAt": extra.pop("finished_at", None) or now_iso(),
    }
    store = extra.pop("store", None)
    if store:
        payload["name"] = store.get("name")
        payload["source"] = store.get("source")
    provider = extra.pop("provider", None)
    if provider:
        payload["provider"] = {
            "id": provider.get("id"),
            "name": provider.get("name"),
            "source": provider.get("source"),
        }
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def normalize_process_text(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def relative_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
