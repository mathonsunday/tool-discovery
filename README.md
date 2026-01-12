# Tool Discovery Assistant for Cursor

A lightweight tool discovery system that helps you find developer tools relevant to your workflow pain points.

## What is this?

Instead of browsing endless "awesome lists" or reading tool roundups, this project enables **conversational tool discovery** inside Cursor:

1. You describe a workflow issue or pain point
2. Cursor reasons about which tools from the database might help
3. You discuss whether it resonates with your use case
4. If yes - try it out; if no - move on (no pushy recommendations)

## Components

- **`tool-database.json`** - Database of 50-100 developer tools scraped from popular awesome lists, filtered by quality (500+ GitHub stars)
- **`tool-discovery-skill.md`** - Cursor skill that knows how to use the database for tool discovery conversations

## Usage

1. Copy the skill file to your Cursor skills directory
2. Copy the tool database to a location Cursor can read
3. Ask Cursor about workflow issues and let it suggest relevant tools

## Data Sources

Tools are scraped from:
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) - MCP servers for AI tools
- [awesome-cli-apps](https://github.com/agarrharr/awesome-cli-apps) - CLI utilities
- [awesome-mac](https://github.com/jaywcjlove/awesome-mac) - Mac productivity apps
- And other curated lists

## Refreshing the Database

```bash
python scrape_tools.py
```

This will re-scrape the awesome lists and update the tool database.

## License

MIT
