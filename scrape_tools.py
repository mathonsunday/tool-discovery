#!/usr/bin/env python3
"""
Scrape developer tools from popular awesome lists on GitHub.
Filters by GitHub stars and outputs a structured JSON database.
"""

import json
import re
import time
from dataclasses import dataclass, asdict
from typing import Optional
import subprocess


@dataclass
class Tool:
    name: str
    description: str
    url: str
    stars: int
    category: str
    source_list: str
    tags: list[str]


def run_gh_api(endpoint: str) -> dict | list | None:
    """Run a GitHub API call using the gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error calling GitHub API: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing JSON from: {endpoint}")
        return None


def get_repo_stars(owner: str, repo: str) -> int:
    """Get the star count for a GitHub repository."""
    data = run_gh_api(f"/repos/{owner}/{repo}")
    if data and isinstance(data, dict):
        return data.get("stargazers_count", 0)
    return 0


def extract_github_repo(url: str) -> tuple[str, str] | None:
    """Extract owner/repo from a GitHub URL."""
    patterns = [
        r"github\.com/([^/]+)/([^/\s\)#]+)",
        r"github\.com/([^/]+)/([^/\s\)#]+)\.git",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip("/").rstrip(")")
            # Clean up any trailing characters
            repo = re.sub(r"[^\w\-\.]", "", repo)
            return owner, repo
    return None


def parse_awesome_list_content(content: str, source_list: str, category: str) -> list[dict]:
    """Parse markdown content from an awesome list to extract tools."""
    tools = []
    
    # Pattern to match markdown links with descriptions
    # Format: - [Name](URL) - Description or * [Name](URL) - Description
    pattern = r"[-*]\s*\[([^\]]+)\]\(([^)]+)\)\s*[-–—:]?\s*(.+?)(?=\n|$)"
    
    matches = re.findall(pattern, content, re.MULTILINE)
    
    for name, url, description in matches:
        # Skip non-GitHub links for now (we need stars)
        if "github.com" not in url.lower():
            continue
        
        # Clean up description
        description = description.strip()
        description = re.sub(r"\s*\[!\[.*?\]\(.*?\)\]\(.*?\)", "", description)  # Remove badges
        description = re.sub(r"!\[.*?\]\(.*?\)", "", description)  # Remove images
        description = description.strip(" .-–—")
        
        if len(description) < 10:  # Skip entries with very short/no descriptions
            continue
        
        tools.append({
            "name": name.strip(),
            "url": url.strip(),
            "description": description[:300],  # Truncate long descriptions
            "source_list": source_list,
            "category": category
        })
    
    return tools


def fetch_awesome_list(owner: str, repo: str, path: str = "README.md") -> str | None:
    """Fetch the content of an awesome list README."""
    # Get the file content
    data = run_gh_api(f"/repos/{owner}/{repo}/contents/{path}")
    if data and isinstance(data, dict) and "download_url" in data:
        # Fetch the raw content
        import urllib.request
        try:
            with urllib.request.urlopen(data["download_url"]) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            print(f"Error fetching content: {e}")
    return None


def enrich_with_stars(tools: list[dict], min_stars: int = 500) -> list[Tool]:
    """Add star counts to tools and filter by minimum stars."""
    enriched = []
    seen_repos = set()
    
    for i, tool in enumerate(tools):
        repo_info = extract_github_repo(tool["url"])
        if not repo_info:
            continue
        
        owner, repo = repo_info
        repo_key = f"{owner}/{repo}".lower()
        
        # Skip duplicates
        if repo_key in seen_repos:
            continue
        seen_repos.add(repo_key)
        
        # Rate limiting - be nice to GitHub
        if i > 0 and i % 10 == 0:
            print(f"  Processed {i}/{len(tools)} tools...")
            time.sleep(1)
        
        stars = get_repo_stars(owner, repo)
        
        if stars >= min_stars:
            # Generate tags from description and category
            tags = generate_tags(tool["description"], tool["category"])
            
            enriched.append(Tool(
                name=tool["name"],
                description=tool["description"],
                url=f"https://github.com/{owner}/{repo}",
                stars=stars,
                category=tool["category"],
                source_list=tool["source_list"],
                tags=tags
            ))
            print(f"  ✓ {tool['name']}: {stars} stars")
        else:
            print(f"  ✗ {tool['name']}: {stars} stars (below threshold)")
    
    return enriched


def generate_tags(description: str, category: str) -> list[str]:
    """Generate relevant tags from description and category."""
    tags = [category]
    
    # Common keywords to look for
    keywords = {
        "cli": ["cli", "command-line", "terminal", "command line"],
        "mcp": ["mcp", "model context protocol"],
        "ai": ["ai", "llm", "gpt", "claude", "machine learning", "artificial intelligence"],
        "git": ["git", "github", "version control"],
        "mac": ["mac", "macos", "osx"],
        "productivity": ["productivity", "workflow", "automation"],
        "documentation": ["documentation", "docs", "readme"],
        "api": ["api", "rest", "http", "request"],
        "json": ["json", "yaml", "data"],
        "search": ["search", "find", "grep"],
        "editor": ["editor", "ide", "vim", "code"],
        "testing": ["test", "testing", "qa"],
        "deployment": ["deploy", "deployment", "ci", "cd"],
        "docker": ["docker", "container", "kubernetes"],
        "database": ["database", "sql", "postgres", "mysql"],
    }
    
    desc_lower = description.lower()
    for tag, patterns in keywords.items():
        if any(p in desc_lower for p in patterns):
            if tag not in tags:
                tags.append(tag)
    
    return tags[:6]  # Limit to 6 tags


def scrape_awesome_mcp_servers() -> list[dict]:
    """Scrape awesome-mcp-servers list."""
    print("Scraping awesome-mcp-servers...")
    content = fetch_awesome_list("punkpeye", "awesome-mcp-servers")
    if content:
        return parse_awesome_list_content(content, "awesome-mcp-servers", "mcp-server")
    return []


def scrape_awesome_cli_apps() -> list[dict]:
    """Scrape awesome-cli-apps list."""
    print("Scraping awesome-cli-apps...")
    content = fetch_awesome_list("agarrharr", "awesome-cli-apps")
    if content:
        return parse_awesome_list_content(content, "awesome-cli-apps", "cli-tool")
    return []


def scrape_awesome_mac() -> list[dict]:
    """Scrape awesome-mac list."""
    print("Scraping awesome-mac...")
    content = fetch_awesome_list("jaywcjlove", "awesome-mac")
    if content:
        return parse_awesome_list_content(content, "awesome-mac", "mac-app")
    return []


def main():
    print("=" * 60)
    print("Tool Discovery Database Builder")
    print("=" * 60)
    
    all_tools = []
    
    # Scrape each awesome list
    all_tools.extend(scrape_awesome_mcp_servers())
    all_tools.extend(scrape_awesome_cli_apps())
    all_tools.extend(scrape_awesome_mac())
    
    print(f"\nFound {len(all_tools)} total tools from awesome lists")
    print("\nEnriching with GitHub stars (filtering for 500+ stars)...")
    
    # Enrich with stars and filter
    enriched_tools = enrich_with_stars(all_tools, min_stars=500)
    
    # Sort by stars descending
    enriched_tools.sort(key=lambda t: t.stars, reverse=True)
    
    # Limit to top 100 tools
    enriched_tools = enriched_tools[:100]
    
    print(f"\nFinal database: {len(enriched_tools)} tools")
    
    # Output to JSON
    output = {
        "metadata": {
            "version": "1.0",
            "tool_count": len(enriched_tools),
            "min_stars": 500,
            "sources": [
                "punkpeye/awesome-mcp-servers",
                "agarrharr/awesome-cli-apps", 
                "jaywcjlove/awesome-mac"
            ]
        },
        "tools": [asdict(t) for t in enriched_tools]
    }
    
    output_path = "tool-database.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved to {output_path}")
    print("\nTop 10 tools by stars:")
    for tool in enriched_tools[:10]:
        print(f"  {tool.stars:,} ★ {tool.name}")


if __name__ == "__main__":
    main()
