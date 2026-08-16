#!/usr/bin/env python3
"""Forward hook events to Telegram and resolve permission requests."""

from __future__ import annotations

import hashlib
import html
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class TelegramError(RuntimeError):
    pass


def option(name: str, fallback: str) -> str:
    return os.environ.get(f"CLAUDE_PLUGIN_OPTION_{name.upper()}") or os.environ.get(fallback, "")


class Config:
    def __init__(self) -> None:
        self.token = option("bot_token", "TELEGRAM_BOT_TOKEN").strip()
        self.chat_id = option("chat_id", "TELEGRAM_CHAT_ID").strip()
        raw_users = option("allowed_user_ids", "TELEGRAM_ALLOWED_USER_IDS")
        try:
            self.allowed_users = {int(value.strip()) for value in raw_users.split(",") if value.strip()}
        except ValueError as exc:
            raise ValueError("allowed user IDs must be comma-separated integers") from exc

        raw_timeout = option("approval_timeout", "TELEGRAM_APPROVAL_TIMEOUT") or "120"
        try:
            self.timeout = min(300, max(15, int(float(raw_timeout))))
        except ValueError as exc:
            raise ValueError("approval timeout must be a number") from exc

        cache_root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        bot_id = hashlib.sha256(self.token.encode()).hexdigest()[:16]
        self.data_dir = cache_root / "telegram-approvals" / bot_id

    def validate(self, approval: bool) -> None:
        missing = []
        if not self.token:
            missing.append("bot token")
        if not self.chat_id:
            missing.append("chat ID")
        if approval and not self.allowed_users:
            missing.append("allowed user IDs")
        if missing:
            raise ValueError("missing Telegram configuration: " + ", ".join(missing))


class Telegram:
    def __init__(self, token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}/"

    def call(self, method: str, payload: dict[str, Any], timeout: int = 15) -> Any:
        request = urllib.request.Request(
            self.base_url + method,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise TelegramError(f"Telegram {method} request failed") from exc
        if not body.get("ok"):
            raise TelegramError(f"Telegram {method} failed: {body.get('description', 'unknown error')}")
        return body.get("result")


def host_name(event: dict[str, Any]) -> str:
    return "Codex" if event.get("model") or event.get("turn_id") else "Claude Code"


def project_name(event: dict[str, Any]) -> str:
    cwd = str(event.get("cwd") or "")
    return Path(cwd).name if cwd else "unknown project"


def compact(value: Any, limit: int) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def approval_text(event: dict[str, Any]) -> str:
    tool = html.escape(str(event.get("tool_name") or "unknown tool"))
    details = html.escape(compact(event.get("tool_input") or {}, 1800))
    return (
        f"<b>{html.escape(host_name(event))} needs approval</b>\n"
        f"Project: <code>{html.escape(project_name(event))}</code>\n"
        f"Tool: <code>{tool}</code>\n\n"
        f"<pre>{details}</pre>"
    )


def notification_text(event: dict[str, Any]) -> str:
    host = html.escape(host_name(event))
    project = html.escape(project_name(event))
    if event.get("hook_event_name") == "Stop":
        message = str(event.get("last_assistant_message") or "Turn complete")
        title = f"{host} finished"
    else:
        message = str(event.get("message") or event.get("notification_type") or "Needs attention")
        title = html.escape(str(event.get("title") or f"{host} notification"))
    return f"<b>{title}</b>\nProject: <code>{project}</code>\n{html.escape(message[:1200])}"


def decision(behavior: str, message: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"behavior": behavior}
    if behavior == "deny" and message:
        result["message"] = message
    return {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": result}}


def read_offset(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError, OSError):
        return None


def write_offset(path: Path, offset: int) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(str(offset))
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def acquire_lock(path: Path, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            path.mkdir(mode=0o700)
            return
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > 60:
                    path.rmdir()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("another Telegram approval is already pending")
            time.sleep(0.1)


def prepare_offset(api: Telegram, offset_path: Path) -> int | None:
    offset = read_offset(offset_path)
    if offset is not None:
        return offset
    updates = api.call("getUpdates", {"offset": -1, "limit": 1, "timeout": 0, "allowed_updates": ["callback_query"]})
    if updates:
        offset = int(updates[-1]["update_id"]) + 1
        write_offset(offset_path, offset)
    return offset


def wait_for_decision(api: Telegram, config: Config, event: dict[str, Any]) -> str:
    config.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(config.data_dir, 0o700)
    lock_path = config.data_dir / "updates.lock"
    acquire_lock(lock_path)
    try:
        offset_path = config.data_dir / "update-offset"
        offset = prepare_offset(api, offset_path)
        request_token = secrets.token_hex(12)
        prefix = f"tap:{request_token}:"
        sent = api.call(
            "sendMessage",
            {
                "chat_id": config.chat_id,
                "text": approval_text(event),
                "parse_mode": "HTML",
                "protect_content": True,
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "Allow", "callback_data": prefix + "allow", "style": "success"},
                        {"text": "Deny", "callback_data": prefix + "deny", "style": "danger"},
                    ]]
                },
            },
        )
        message_id = int(sent["message_id"])
        deadline = time.monotonic() + config.timeout

        while time.monotonic() < deadline:
            os.utime(lock_path)
            poll_timeout = max(1, min(20, int(deadline - time.monotonic())))
            payload: dict[str, Any] = {
                "limit": 100,
                "timeout": poll_timeout,
                "allowed_updates": ["callback_query"],
            }
            if offset is not None:
                payload["offset"] = offset
            updates = api.call("getUpdates", payload, timeout=poll_timeout + 5)
            for update in updates:
                offset = int(update["update_id"]) + 1
                write_offset(offset_path, offset)
                callback = update.get("callback_query") or {}
                data = str(callback.get("data") or "")
                if not data.startswith(prefix):
                    if data.startswith("tap:"):
                        api.call("answerCallbackQuery", {"callback_query_id": callback["id"], "text": "Approval expired"})
                    continue
                sender = int((callback.get("from") or {}).get("id", 0))
                message = callback.get("message") or {}
                callback_chat = str((message.get("chat") or {}).get("id", ""))
                valid_origin = callback_chat == config.chat_id and int(message.get("message_id", 0)) == message_id
                if sender not in config.allowed_users or not valid_origin:
                    api.call("answerCallbackQuery", {"callback_query_id": callback["id"], "text": "Not authorized", "show_alert": True})
                    continue
                choice = data.removeprefix(prefix)
                if choice not in {"allow", "deny"}:
                    continue
                api.call("answerCallbackQuery", {"callback_query_id": callback["id"], "text": choice.title()})
                api.call("editMessageReplyMarkup", {"chat_id": config.chat_id, "message_id": message_id, "reply_markup": {}})
                return choice

        api.call("editMessageReplyMarkup", {"chat_id": config.chat_id, "message_id": message_id, "reply_markup": {}})
        raise TimeoutError("Telegram approval timed out")
    finally:
        try:
            lock_path.rmdir()
        except FileNotFoundError:
            pass


def handle(event: dict[str, Any]) -> dict[str, Any] | None:
    is_approval = event.get("hook_event_name") == "PermissionRequest"
    config = Config()
    config.validate(is_approval)
    api = Telegram(config.token)
    if is_approval:
        choice = wait_for_decision(api, config, event)
        return decision(choice, "Denied from Telegram" if choice == "deny" else None)
    api.call(
        "sendMessage",
        {
            "chat_id": config.chat_id,
            "text": notification_text(event),
            "parse_mode": "HTML",
            "protect_content": True,
        },
    )
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
        result = handle(event)
    except Exception as exc:
        is_approval = "event" in locals() and event.get("hook_event_name") == "PermissionRequest"
        print(f"telegram-approvals: {exc}", file=sys.stderr)
        if is_approval:
            print(json.dumps(decision("deny", f"Telegram approval failed: {exc}")))
        return 0
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
