import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "telegram_hook.py"
SPEC = importlib.util.spec_from_file_location("telegram_hook", SCRIPT)
telegram_hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(telegram_hook)


class FakeTelegram:
    def __init__(self, sender_ids, choice="allow"):
        self.sender_ids = iter(sender_ids)
        self.choice = choice
        self.calls = []
        self.callback_data = ""

    def call(self, method, payload, timeout=15):
        self.calls.append((method, payload))
        if method == "sendMessage":
            self.callback_data = payload["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
            self.callback_data = self.callback_data.removesuffix("allow") + self.choice
            return {"message_id": 42}
        if method == "getUpdates" and payload.get("offset") == -1:
            return []
        if method == "getUpdates":
            sender_id = next(self.sender_ids)
            return [
                {
                    "update_id": len(self.calls),
                    "callback_query": {
                        "id": f"callback-{sender_id}",
                        "from": {"id": sender_id},
                        "message": {"message_id": 42, "chat": {"id": 100}},
                        "data": self.callback_data,
                    },
                }
            ]
        return True


class TelegramHookTests(unittest.TestCase):
    def config(self, directory):
        config = telegram_hook.Config.__new__(telegram_hook.Config)
        config.token = "test-token"
        config.chat_id = "100"
        config.allowed_users = {7}
        config.timeout = 15
        config.data_dir = Path(directory)
        return config

    def event(self):
        return {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "echo '<ok>'"},
            "cwd": "/workspace/example",
        }

    def test_authorized_callback_allows_request(self):
        with tempfile.TemporaryDirectory() as directory:
            api = FakeTelegram([7])
            result = telegram_hook.wait_for_decision(api, self.config(directory), self.event())

        self.assertEqual(result, "allow")
        self.assertLess(len(api.callback_data.encode()), 65)
        self.assertIn("&lt;ok&gt;", api.calls[1][1]["text"])
        self.assertEqual(api.calls[-1][0], "editMessageReplyMarkup")

    def test_authorized_callback_denies_request(self):
        with tempfile.TemporaryDirectory() as directory:
            api = FakeTelegram([7], choice="deny")
            result = telegram_hook.wait_for_decision(api, self.config(directory), self.event())

        self.assertEqual(result, "deny")

    def test_unauthorized_callback_is_rejected_before_authorized_one(self):
        with tempfile.TemporaryDirectory() as directory:
            api = FakeTelegram([8, 7])
            result = telegram_hook.wait_for_decision(api, self.config(directory), self.event())

        self.assertEqual(result, "allow")
        unauthorized_answers = [
            payload
            for method, payload in api.calls
            if method == "answerCallbackQuery" and payload.get("show_alert")
        ]
        self.assertEqual(unauthorized_answers[0]["text"], "Not authorized")

    def test_deny_decision_uses_shared_hook_schema(self):
        self.assertEqual(
            telegram_hook.decision("deny", "Denied from Telegram"),
            {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "deny", "message": "Denied from Telegram"},
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
