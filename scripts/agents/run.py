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
    command = [sys.executable, *store["command"], "--output", str(output_path)]
    started_at = now_iso()

    print(f"[{store_id}] updating {store['name']} -> {output_path}")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        print(completed.stderr or completed.stdout, file=sys.stderr)
        return build_status(
            "failed",
            started_at=started_at,
            finished_at=now_iso(),
            store=store,
            error=(completed.stderr or completed.stdout or f"exit code {completed.returncode}").strip(),
            output_file=str(output_path),
            return_code=completed.returncode,
        )

    payload = read_json(output_path, default={})
    product_count = len(payload.get("products", [])) if isinstance(payload.get("products"), list) else 0
    return build_status(
        "success",
        started_at=started_at,
        finished_at=now_iso(),
        store=store,
        output_file=str(output_path),
        product_count=product_count,
        source_updated_at=payload.get("updatedAt"),
    )


def build_status(status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": status,
        "checkedAt": extra.pop("finished_at", None) or now_iso(),
    }
    store = extra.pop("store", None)
    if store:
        payload["name"] = store.get("name")
        payload["source"] = store.get("source")
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
