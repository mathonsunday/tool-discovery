# Tool Discovery MCP Server

An MCP server that helps you discover developer tools based on workflow pain points. Works with Cursor, Claude, and other MCP-compatible AI tools.

## What It Does

When you describe a workflow issue:
1. **Provides tips** for tools you're already using
2. **Suggests alternatives** from a curated database of 100+ tools
3. **Offers handoff** for step-by-step help if you want it

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

Then restart Cursor.

## Usage

Just describe a workflow issue naturally in Cursor agent mode. The AI will automatically use the `discover_tools` function when relevant.

**Example prompts:**
- "I'm using Mac dictation for voice input but it makes mistakes. What tools are available?"
- "I need a better way to test API endpoints"
- "My terminal workflow feels slow"

## The Tool

**`discover_tools`**

| Parameter | Type | Description |
|-----------|------|-------------|
| `problem` | string | Description of the workflow issue |
| `existing_tools` | string[] | (Optional) Tools you're already using |

**Returns:**
- `tips_for_existing_tools` - Tips for tools you mentioned
- `alternatives` - Relevant tools from the database
- `handoff_message` - Offer for deeper help

## Refreshing the Tool Database

```bash
python3 scrape_tools.py
npm run build
```

## Development

```bash
# Run in development mode
npm run dev

# Build
npm run build

# Test manually
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node dist/index.js
```

## License

MIT
