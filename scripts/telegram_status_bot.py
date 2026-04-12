#!/usr/bin/env python3

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import error, parse, request


def getenv_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


BOT_TOKEN = getenv_required("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = getenv_required("TELEGRAM_STATUS_ALLOWED_CHAT_ID")
API_HEALTH_URL = os.getenv(
    "STATUS_API_HEALTH_URL", "https://api.wobbly.site/health"
).strip()
API_READY_URL = os.getenv(
    "STATUS_API_READY_URL", "https://api.wobbly.site/ready"
).strip()
POLL_TIMEOUT = int(os.getenv("TELEGRAM_STATUS_POLL_TIMEOUT", "30"))
REQUEST_TIMEOUT = int(os.getenv("TELEGRAM_STATUS_REQUEST_TIMEOUT", "10"))

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


@dataclass
class CheckResult:
    name: str
    ok: bool
    status_code: int | None
    latency_ms: int | None
    details: str


def telegram_api(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(
        f"{TELEGRAM_API_BASE}/{method}",
        data=data,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    with request.urlopen(req, timeout=REQUEST_TIMEOUT + 5) as response:
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not parsed.get("ok"):
        raise RuntimeError(f"Telegram API error for {method}: {body}")
    return parsed


def send_message(chat_id: str, text: str) -> None:
    telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
    )


def perform_http_check(name: str, url: str) -> CheckResult:
    started = time.perf_counter()
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            status_code = response.getcode()
            response.read()
        latency_ms = int((time.perf_counter() - started) * 1000)
        ok = 200 <= status_code < 300
        details = f"HTTP {status_code}"
        return CheckResult(
            name=name,
            ok=ok,
            status_code=status_code,
            latency_ms=latency_ms,
            details=details,
        )
    except error.HTTPError as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return CheckResult(
            name=name,
            ok=False,
            status_code=exc.code,
            latency_ms=latency_ms,
            details=f"HTTP {exc.code}",
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.perf_counter() - started) * 1000)
        return CheckResult(
            name=name,
            ok=False,
            status_code=None,
            latency_ms=latency_ms,
            details=str(exc),
        )


def format_status_message() -> str:
    checks = [
        perform_http_check("API health", API_HEALTH_URL),
        perform_http_check("API ready", API_READY_URL),
    ]
    checked_at = (
        datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    )
    lines = ["Wobbly status", f"Checked at: {checked_at}", ""]
    for result in checks:
        icon = "OK" if result.ok else "FAIL"
        latency = f"{result.latency_ms}ms" if result.latency_ms is not None else "n/a"
        lines.append(f"{icon} {result.name}: {result.details}, {latency}")
    return "\n".join(lines)


def extract_command(update: dict[str, Any]) -> tuple[str | None, str | None]:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    text = (message.get("text") or "").strip()
    if not chat_id or not text:
        return None, None

    command = text.split()[0]
    if "@" in command:
        command = command.split("@", 1)[0]
    return chat_id, command.lower()


def main() -> int:
    offset = 0
    while True:
        try:
            params = parse.urlencode(
                {
                    "timeout": POLL_TIMEOUT,
                    "offset": offset,
                    "allowed_updates": json.dumps(["message", "edited_message"]),
                }
            )
            updates = telegram_api(f"getUpdates?{params}")
            for item in updates.get("result", []):
                offset = int(item["update_id"]) + 1
                chat_id, command = extract_command(item)
                if not chat_id or command != "/status":
                    continue
                if chat_id != ALLOWED_CHAT_ID:
                    send_message(chat_id, "This bot is not enabled for this chat.")
                    continue
                send_message(chat_id, format_status_message())
        except KeyboardInterrupt:
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"telegram status bot loop error: {exc}", file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
