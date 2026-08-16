---
name: configuring-telegram-approvals
description: Configure and troubleshoot Telegram notifications and remote tool approvals for Claude Code or Codex. Use when setting up the telegram-approvals plugin, finding Telegram IDs, changing approval timeouts, or diagnosing hook failures.
---

# Configuring Telegram Approvals

Use the setup instructions in `${CLAUDE_PLUGIN_ROOT}/README.md`. Treat Telegram as an approval surface with access to the same tool details shown in the terminal.

When helping with setup:

1. Confirm the user created a dedicated bot with BotFather and sent it one private message.
2. Never ask the user to paste the bot token into chat. Have them store it through Claude's plugin configuration or export it in their local shell for Codex.
3. Help them obtain the numeric chat and user IDs with the Bot API `getUpdates` method, without printing the bot token.
4. Require at least one explicit allowed user ID. A chat ID alone is not authorization.
5. Start with a short test timeout, then test a harmless command that requires approval.
6. If approval polling fails, check that the bot has no webhook configured and that no other process calls `getUpdates` for the same bot.

Remote approval sends tool input to Telegram. Warn the user before testing commands that contain credentials, personal data, or proprietary content.
