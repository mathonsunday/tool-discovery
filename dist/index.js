#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
// Search GitHub for tools matching a query
async function searchGitHub(query, minStars = 500) {
    // Build search query with quality filters
    const searchQuery = encodeURIComponent(`${query} stars:>=${minStars} archived:false`);
    const url = `https://api.github.com/search/repositories?q=${searchQuery}&sort=stars&order=desc&per_page=10`;
    console.error(`[tool-discovery] Searching GitHub: ${query}`);
    const response = await fetch(url, {
        headers: {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "tool-discovery-mcp",
        },
    });
    if (!response.ok) {
        console.error(`[tool-discovery] GitHub API error: ${response.status}`);
        throw new Error(`GitHub API error: ${response.status}`);
    }
    const data = await response.json();
    console.error(`[tool-discovery] Found ${data.total_count} results`);
    // Filter to only recently updated repos (within last 2 years)
    const twoYearsAgo = new Date();
    twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
    return data.items.filter(repo => {
        const updatedAt = new Date(repo.updated_at);
        return updatedAt > twoYearsAgo && !repo.archived;
    });
}
// Tips for common tools (expandable)
const TOOL_TIPS = {
    "mac dictation": [
        "Enable 'Enhanced Dictation' in System Settings → Keyboard → Dictation for offline mode and better accuracy",
        "Use punctuation commands: say 'comma', 'period', 'new paragraph', 'new line'",
        "Say 'caps on' and 'caps off' to control capitalization",
    ],
    "cursor": [
        "Use Cmd+K for inline edits, Cmd+L for chat",
        "@ mention files to include them as context",
        "Use .cursorrules for project-specific instructions",
        "Composer mode (Cmd+I) is better for multi-file changes",
    ],
    "git": [
        "Use 'git stash' to temporarily save changes without committing",
        "Use 'git log --oneline --graph' for a visual branch history",
    ],
    "vscode": [
        "Cmd+Shift+P opens the command palette",
        "Cmd+P for quick file open, then type @ to jump to symbols",
    ],
    "homebrew": [
        "Use 'brew bundle' to manage all your packages in a Brewfile",
        "Use 'brew upgrade --greedy' to update cask apps too",
    ],
    "raycast": [
        "Use snippets for frequently typed text",
        "Clipboard history (Cmd+Shift+V) saves tons of time",
    ],
};
// Find tips for mentioned tools
function findTipsForTools(existingTools) {
    const results = [];
    for (const tool of existingTools) {
        const toolLower = tool.toLowerCase();
        for (const [knownTool, tips] of Object.entries(TOOL_TIPS)) {
            if (toolLower.includes(knownTool) || knownTool.includes(toolLower)) {
                results.push({ tool, tips });
                break;
            }
        }
    }
    return results;
}
// Create the MCP server
const server = new Server({
    name: "tool-discovery",
    version: "1.0.0",
}, {
    capabilities: {
        tools: {},
    },
});
// Define the discover_tools schema
const DiscoverToolsSchema = z.object({
    problem: z.string().describe("Description of the workflow issue or pain point"),
    existing_tools: z.array(z.string()).optional().describe("Tools the user is already using (to provide tips)"),
});
// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "discover_tools",
                description: `Search GitHub in real-time to find developer tools for workflow pain points.

WHEN TO USE THIS TOOL:
- User asks "is there a tool for X?"
- User describes a workflow problem or pain point
- User wants recommendations for utilities, CLI tools, or productivity apps
- User asks about alternatives to a tool they're using

WHY USE THIS INSTEAD OF ANSWERING DIRECTLY:
- Returns only REAL tools that exist on GitHub with 500+ stars
- Filters to actively maintained projects (updated in last 2 years)
- Provides actual GitHub URLs and star counts as quality signals
- Prevents recommending abandoned, obscure, or non-existent tools`,
                inputSchema: {
                    type: "object",
                    properties: {
                        problem: {
                            type: "string",
                            description: "Description of the workflow issue or pain point",
                        },
                        existing_tools: {
                            type: "array",
                            items: { type: "string" },
                            description: "Tools the user is already using (to provide tips for them first)",
                        },
                    },
                    required: ["problem"],
                },
            },
        ],
    };
});
// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    console.error(`[tool-discovery] Tool called: ${request.params.name}`);
    console.error(`[tool-discovery] Arguments: ${JSON.stringify(request.params.arguments)}`);
    if (request.params.name !== "discover_tools") {
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
    const args = DiscoverToolsSchema.parse(request.params.arguments);
    // Find tips for existing tools
    const existingTools = args.existing_tools || [];
    const tips = findTipsForTools(existingTools);
    // Search GitHub for relevant tools
    let githubResults = [];
    try {
        githubResults = await searchGitHub(args.problem);
    }
    catch (error) {
        console.error(`[tool-discovery] GitHub search failed: ${error}`);
    }
    // Format response
    const response = {
        tips_for_existing_tools: tips,
        tools_found: githubResults.map(repo => ({
            name: repo.name,
            full_name: repo.full_name,
            description: repo.description,
            url: repo.html_url,
            stars: repo.stargazers_count,
            topics: repo.topics,
            last_updated: repo.updated_at,
        })),
        search_query: args.problem,
        handoff_message: githubResults.length > 0
            ? "Would you like more details about any of these tools, or should I search with different keywords?"
            : "No results found. Would you like me to try different search terms?",
    };
    return {
        content: [
            {
                type: "text",
                text: JSON.stringify(response, null, 2),
            },
        ],
    };
});
// Start the server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Tool Discovery MCP Server running on stdio");
}
main().catch(console.error);
