# Telegram Approvals

Telegram notifications and remote tool approvals for Claude Code and Codex. The plugin uses lifecycle hooks and the Telegram Bot API directly, with Python 3 and no third-party packages.

## Behavior

- Claude Code forwards its `Notification` events, including permission, idle, and input prompts.
- Codex sends a notification when a turn stops because Codex doesn't currently expose the `Notification` hook event.
- Both hosts send `PermissionRequest` events with Allow and Deny buttons. A valid Telegram response returns the host's documented hook decision JSON.
- Requests deny on timeout, configuration errors, Telegram errors, unauthorized responses, and concurrent approval attempts.

## Telegram setup

1. Create a dedicated bot with [BotFather](https://t.me/BotFather).
2. Open a private chat with the bot and send `/start`.
3. Get your numeric IDs by calling `getUpdates` locally. Keep the token out of shell history where possible:

   ```bash
   read -rsp "Bot token: " TELEGRAM_BOT_TOKEN; echo
   curl -sS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates" | jq
   unset TELEGRAM_BOT_TOKEN
   ```

   Use `message.chat.id` as the chat ID and `message.from.id` as an allowed user ID.

Use a private chat unless a group is necessary. The plugin restricts decisions by chat, message, one-time callback token, and the configured user IDs.

## Claude Code

Install and configure the plugin:

```text
/plugin marketplace add yannelli/agents
/plugin install telegram-approvals@yannelli-agents
/plugin enable telegram-approvals@yannelli-agents
```

The plugin installs disabled because it runs external hooks. Claude prompts for the bot token, chat ID, allowed user IDs, and timeout when the plugin is enabled. The token is marked sensitive and goes to the platform's secure plugin credential storage. Review and trust the bundled hooks when prompted.

For non-interactive installation, use `claude plugin install ... --config key=value` from a terminal. Avoid putting `bot_token` directly on a shared command line.

## Codex

Add this repository as a marketplace, install the plugin from the Codex plugin browser, then export these variables in the environment that starts Codex:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="123456789"
export TELEGRAM_ALLOWED_USER_IDS="123456789"
export TELEGRAM_APPROVAL_TIMEOUT="120"  # optional, 15-300 seconds
```

Codex skips plugin hooks until you review and trust their definitions. Codex currently has no plugin `userConfig` credential prompt, so its hook reads environment variables.

## Security and operating limits

- Tool input is included in approval messages so a decision isn't blind. It can contain source code, paths, commands, URLs, or secrets. Telegram receives that data.
- Use a bot dedicated to this plugin. Telegram `getUpdates` is a single-consumer queue, and webhooks are mutually exclusive with polling.
- Only one approval can poll per bot token at a time, including across Claude Code and Codex. A second concurrent request is denied after five seconds rather than risk consuming the first request's callback.
- Callback data contains a random one-time token and stays below Telegram's 64-byte limit.
- Approval waits at most 300 seconds. The hook timeout is 330 seconds.
- The bot token never appears in hook output or plugin files.

State is stored under `~/.cache/telegram-approvals/` (or `$XDG_CACHE_HOME`). It contains a Telegram update offset and a lock directory, partitioned by a truncated hash of the bot token.

## References

The implementation follows the current official documentation:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Telegram Bot API](https://core.telegram.org/bots/api)
