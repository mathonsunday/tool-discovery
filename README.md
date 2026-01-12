# Tool Discovery MCP Server

An MCP server that searches GitHub in real-time to find developer tools for your workflow pain points. Works with Cursor and other MCP-compatible AI tools.

## What It Does

When you ask about tools or describe a workflow issue:
1. **Searches GitHub** in real-time for relevant tools
2. **Filters for quality** - only returns tools with 500+ stars, updated in last 2 years
3. **Provides tips** for tools you're already using (if mentioned)

## Why Use This Instead of Just Asking the AI?

- Returns only **real tools** that exist on GitHub
- **Validates quality** via star count and recent activity
- Prevents recommendations of abandoned, obscure, or non-existent tools
- Provides **actual URLs** and star counts as quality signals

## Installation

```bash
cd tool-discovery
npm install
npm run build
```

## Adding to Cursor

Add to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "tool-discovery": {
      "command": "node",
      "args": ["/path/to/tool-discovery/dist/index.js"]
    }
  }
}
```

Then restart Cursor (or toggle the MCP server off/on in settings).

## Usage

Just ask naturally in Cursor agent mode:

- "Is there a tool for pomodoro/focus timers?"
- "Find me a CSS animation library"
- "I need a better way to manage git branches"
- "What tools exist for API testing?"

The AI will automatically call `discover_tools` and present the results.

## The Tool

**`discover_tools`**

| Parameter | Type | Description |
|-----------|------|-------------|
| `problem` | string | Description of the workflow issue or what you're looking for |
| `existing_tools` | string[] | (Optional) Tools you're already using - will get tips for these |

**Returns:**
- `tools_found` - GitHub repos matching your query (name, description, URL, stars, topics)
- `tips_for_existing_tools` - Tips for tools you mentioned
- `search_query` - The query that was searched
- `handoff_message` - Offer for follow-up help

## Development

```bash
# Build
npm run build

# Test manually
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node dist/index.js

# Test a search
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"discover_tools","arguments":{"problem":"pomodoro timer"}}}' | node dist/index.js
```

## License

MIT
