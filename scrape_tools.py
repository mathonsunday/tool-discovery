#!/usr/bin/env python3
"""
Scrape developer tools from GitHub using search API.
Much faster than parsing awesome lists individually.
"""

import json
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Dict
import urllib.parse


@dataclass
class Tool:
    name: str
    description: str
    url: str
    stars: int
    category: str
    tags: List[str]


def run_gh_search(query: str, limit: int = 30) -> List[Dict]:
    """Run a GitHub search using gh CLI."""
    try:
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        endpoint = f"/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={limit}"
        
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data.get("items", [])
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return []
    except json.JSONDecodeError:
        return []


def generate_tags(description: str, topics: List[str], category: str) -> List[str]:
    """Generate relevant tags from description and topics."""
    tags = set([category])
    
    # Add GitHub topics
    for topic in topics[:5]:
        tags.add(topic.replace("-", " "))
    
    # Common keywords to look for in description
    keywords = {
        "cli": ["cli", "command-line", "terminal"],
        "mcp": ["mcp", "model context protocol"],
        "ai": ["ai", "llm", "gpt", "claude", "machine learning"],
        "git": ["git", "github", "version control"],
        "mac": ["mac", "macos", "osx"],
        "productivity": ["productivity", "workflow", "automation"],
        "documentation": ["documentation", "docs"],
        "api": ["api", "rest", "http"],
        "search": ["search", "find", "grep"],
        "testing": ["test", "testing"],
        "docker": ["docker", "container", "kubernetes"],
    }
    
    desc_lower = (description or "").lower()
    for tag, patterns in keywords.items():
        if any(p in desc_lower for p in patterns):
            tags.add(tag)
    
    return list(tags)[:8]


def search_tools_by_category(query: str, category: str, min_stars: int = 500) -> List[Tool]:
    """Search for tools in a specific category."""
    print(f"  Searching: {query}")
    
    results = run_gh_search(f"{query} stars:>{min_stars}", limit=30)
    tools = []
    
    for repo in results:
        if repo.get("fork"):  # Skip forks
            continue
            
        description = repo.get("description") or ""
        if len(description) < 10:  # Skip repos with no real description
            continue
        
        tools.append(Tool(
            name=repo["name"],
            description=description[:300],
            url=repo["html_url"],
            stars=repo["stargazers_count"],
            category=category,
            tags=generate_tags(description, repo.get("topics", []), category)
        ))
    
    return tools


def main():
    print("=" * 60)
    print("Tool Discovery Database Builder (Fast Mode)")
    print("=" * 60)
    
    all_tools = []
    seen_urls = set()
    
    # Define search queries by category
    searches = [
        # MCP Servers
        ("topic:mcp-server", "mcp-server"),
        ("mcp server in:name,description", "mcp-server"),
        
        # CLI Tools
        ("topic:cli-tool", "cli-tool"),
        ("cli tool developer in:description", "cli-tool"),
        ("terminal utility in:description", "cli-tool"),
        
        # Mac Apps
        ("topic:macos-app", "mac-app"),
        ("macos menu bar in:description", "mac-app"),
        ("mac productivity in:description", "mac-app"),
        
        # AI Tools
        ("topic:ai-tools", "ai-tooling"),
        ("llm developer tool in:description", "ai-tooling"),
        ("cursor ai in:description", "ai-tooling"),
        
        # Developer Tools
        ("topic:developer-tools", "dev-tool"),
        ("developer productivity in:description", "dev-tool"),
    ]
    
    print("\nSearching GitHub...")
    for query, category in searches:
        tools = search_tools_by_category(query, category, min_stars=500)
        for tool in tools:
            if tool.url not in seen_urls:
                seen_urls.add(tool.url)
                all_tools.append(tool)
        print(f"    Found {len(tools)} tools, total unique: {len(all_tools)}")
    
    # Sort by stars and limit
    all_tools.sort(key=lambda t: t.stars, reverse=True)
    all_tools = all_tools[:100]
    
    print(f"\nFinal database: {len(all_tools)} tools")
    
    # Output to JSON
    output = {
        "metadata": {
            "version": "1.0",
            "tool_count": len(all_tools),
            "min_stars": 500,
            "description": "Developer tools database for conversational discovery"
        },
        "tools": [asdict(t) for t in all_tools]
    }
    
    with open("tool-database.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n✓ Saved to tool-database.json")
    print("\nTop 15 tools by stars:")
    for tool in all_tools[:15]:
        print(f"  {tool.stars:>6,} ★  {tool.name}: {tool.description[:60]}...")


if __name__ == "__main__":
    main()
