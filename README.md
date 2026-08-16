# yannelli-agents

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) of plugins, skills, and agents.

## Installation

Add the marketplace from inside Claude Code:

```
/plugin marketplace add yannelli/agents
```

Then install a plugin:

```
/plugin install starter@yannelli-agents
```

Other useful commands:

```
/plugin marketplace update yannelli-agents   # pull the latest plugin listings
/plugin update starter@yannelli-agents       # update an installed plugin
/plugin disable starter@yannelli-agents      # turn a plugin off without uninstalling
```

## Available plugins

| Plugin | Description |
|--------|-------------|
| [`starter`](plugins/starter/) | Example plugin demonstrating the skill and agent formats. Use it as a template for new plugins. |
| [`workflows`](plugins/workflows/) | Reusable execution directives for development tasks, starting with the `scoped-task-execution` skill for tightly scoped issue and ticket implementation. |

## Repository layout

```
.claude-plugin/
  marketplace.json      # Marketplace manifest: name, owner, plugin listings
plugins/
  <plugin-name>/
    .claude-plugin/
      plugin.json       # Plugin manifest: name, version, author
    skills/
      <skill-name>/
        SKILL.md        # A skill: YAML frontmatter + instructions
    agents/
      <agent-name>.md   # A subagent definition
    hooks/
      hooks.json        # Optional lifecycle hooks
    .mcp.json           # Optional MCP server definitions
```

## Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` (see [`plugins/starter/`](plugins/starter/) for a template).
2. Add skills under `plugins/<name>/skills/<skill-name>/SKILL.md`, and optionally agents, hooks, or MCP servers.
3. Register the plugin in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) with `"source": "./plugins/<name>"`.
4. Validate before committing:

   ```bash
   claude plugin validate ./plugins/<name>
   ```

5. Users pick up the new plugin with `/plugin marketplace update yannelli-agents`.

## License

[MIT](LICENSE)
