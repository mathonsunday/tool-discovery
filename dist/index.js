#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Load tool database
function loadToolDatabase() {
    // Try multiple locations for the database
    const possiblePaths = [
        path.join(__dirname, "..", "tool-database.json"), // When running from dist/
        path.join(__dirname, "tool-database.json"), // When in same dir
        path.join(process.cwd(), "tool-database.json"), // Current working directory
    ];
    for (const dbPath of possiblePaths) {
        if (fs.existsSync(dbPath)) {
            const data = fs.readFileSync(dbPath, "utf-8");
            return JSON.parse(data);
        }
    }
    throw new Error("Could not find tool-database.json");
}
// Tips for common tools (expandable)
const TOOL_TIPS = {
    "mac dictation": [
        "Enable 'Enhanced Dictation' in System Settings → Keyboard → Dictation for offline mode and better accuracy",
        "Use punctuation commands: say 'comma', 'period', 'new paragraph', 'new line'",
        "Say 'caps on' and 'caps off' to control capitalization",
        "It learns from your typing - using technical terms in text helps recognition",
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
        "Use 'git blame' to see who changed each line",
    ],
    "vscode": [
        "Cmd+Shift+P opens the command palette",
        "Cmd+P for quick file open, then type @ to jump to symbols",
        "Multi-cursor: Cmd+D to select next occurrence",
    ],
    "terminal": [
        "Use Ctrl+R for reverse history search",
        "Use 'cd -' to go back to previous directory",
        "Use '!!' to repeat last command",
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
// Score a tool's relevance to a problem description
function scoreToolRelevance(tool, problem) {
    const problemLower = problem.toLowerCase();
    const words = problemLower.split(/\s+/);
    let score = 0;
    // Check description match
    const descLower = tool.description.toLowerCase();
    for (const word of words) {
        if (word.length > 3 && descLower.includes(word)) {
            score += 2;
        }
    }
    // Check tag match
    for (const tag of tool.tags) {
        const tagLower = tag.toLowerCase();
        if (problemLower.includes(tagLower)) {
            score += 3;
        }
        for (const word of words) {
            if (word.length > 3 && tagLower.includes(word)) {
                score += 1;
            }
        }
    }
    // Check name match
    if (problemLower.includes(tool.name.toLowerCase())) {
        score += 5;
    }
    // Bonus for star count (normalized)
    score += Math.log10(tool.stars + 1) * 0.5;
    return score;
}
// Find relevant tools for a problem
function findRelevantTools(db, problem, limit = 5) {
    const scored = db.tools.map(tool => ({
        tool,
        score: scoreToolRelevance(tool, problem),
    }));
    scored.sort((a, b) => b.score - a.score);
    // Filter out low-relevance results
    const relevant = scored.filter(s => s.score > 2);
    return relevant.slice(0, limit).map(s => s.tool);
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
                description: `Help users discover developer tools for their workflow pain points. 
        
This tool:
1. Provides tips for tools the user is already using (if mentioned)
2. Suggests relevant alternatives from a curated database of 100+ tools
3. Returns structured results that can be formatted nicely

Use this when a user describes a workflow issue, asks about tools for a task, 
or wants to improve their development setup.`,
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
    if (request.params.name !== "discover_tools") {
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
    const args = DiscoverToolsSchema.parse(request.params.arguments);
    const db = loadToolDatabase();
    // Find tips for existing tools
    const existingTools = args.existing_tools || [];
    const tips = findTipsForTools(existingTools);
    // Find relevant alternatives
    const alternatives = findRelevantTools(db, args.problem, 5);
    // Format response
    const response = {
        tips_for_existing_tools: tips,
        alternatives: alternatives.map(t => ({
            name: t.name,
            description: t.description,
            url: t.url,
            stars: t.stars,
            category: t.category,
        })),
        handoff_message: "Would you like step-by-step help with any of these options?",
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
