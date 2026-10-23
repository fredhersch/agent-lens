#!/usr/bin/env python3
"""
AgentLens CLI - Issue Fetcher & Directive Parser
Pulls open issues from GitHub created by the AgentLens widget, extracts
grounded DOM selectors and directives, and formats them for AI coding agents.

Usage:
  python3 fetch_issues.py --repo owner/repo [--token GITHUB_TOKEN]
  python3 fetch_issues.py (uses GITHUB_REPOSITORY or AGENTLENS_REPO env vars)
"""

import os
import sys
import json
import re
import argparse
import urllib.request
import ssl

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and parse AgentLens issues for AI coding agents.")
    parser.add_argument("--repo", "-r", help="Target GitHub repository (owner/repo)", default=os.environ.get("AGENTLENS_REPO") or os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--token", "-t", help="GitHub Personal Access Token", default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    parser.add_argument("--state", "-s", choices=["open", "closed", "all"], default="open", help="Issue state (default: open)")
    parser.add_argument("--limit", "-n", type=int, default=30, help="Max issues to fetch (default: 30)")
    parser.add_argument("--format", "-f", choices=["markdown", "json", "compact"], default="markdown", help="Output format")
    return parser.parse_args()

def fetch_issues(repo, token=None, state="open", limit=30):
    if not repo or "/" not in repo:
        raise ValueError("Repository must be in 'owner/repo' format. Provide --repo or set AGENTLENS_REPO.")

    url = f"https://api.github.com/repos/{repo}/issues?state={state}&per_page={limit}"
    headers = {
        "User-Agent": "AgentLens-CLI/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    except Exception:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)

    data = json.loads(resp.read().decode("utf-8"))
    return [i for i in data if "pull_request" not in i]

def parse_directive_metadata(body):
    meta = {
        "page": None,
        "selector": None,
        "element_text": None,
        "directive": None,
        "category": "UI Fix",
        "coordinates": None,
        "html_snippet": None
    }
    if not body:
        return meta

    # Directive / Instruction
    dir_match = re.search(r"#### 💬 User Instruction\s*>\s*(.*?)(?=\n---|####|$)", body, re.DOTALL)
    if dir_match:
        meta["directive"] = dir_match.group(1).strip()

    # Category
    cat_match = re.search(r"\*\*Category\*\*:\s*`([^`]+)`", body)
    if cat_match:
        meta["category"] = cat_match.group(1).strip()

    # Page / File
    page_match = re.search(r"- \*\*Target Page / File\*\*:\s*`([^`]+)`", body)
    if page_match:
        meta["page"] = page_match.group(1).strip()

    # CSS Selector
    sel_match = re.search(r"- \*\*CSS Selector\*\*:\s*`([^`]+)`", body)
    if sel_match:
        meta["selector"] = sel_match.group(1).strip()

    # Element Text
    text_match = re.search(r"- \*\*Element Text\*\*:\s*`([^`]+)`", body)
    if text_match:
        meta["element_text"] = text_match.group(1).strip()

    # HTML Snippet
    snippet_match = re.search(r"```html\s*\n(.*?)\n```", body, re.DOTALL)
    if snippet_match:
        meta["html_snippet"] = snippet_match.group(1).strip()

    return meta

def main():
    args = parse_args()
    if not args.repo:
        print("Error: No repository specified. Please pass --repo owner/repo or set AGENTLENS_REPO environment variable.", file=sys.stderr)
        sys.exit(1)

    try:
        issues = fetch_issues(args.repo, args.token, args.state, args.limit)
    except Exception as e:
        print(f"Error fetching issues: {e}", file=sys.stderr)
        sys.exit(1)

    parsed_items = []
    for issue in issues:
        meta = parse_directive_metadata(issue.get("body", ""))
        parsed_items.append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "url": issue.get("html_url"),
            "user": issue.get("user", {}).get("login"),
            "labels": [l.get("name") for l in issue.get("labels", [])],
            **meta
        })

    if args.format == "json":
        print(json.dumps(parsed_items, indent=2))
        return

    if args.format == "compact":
        for item in parsed_items:
            print(f"#{item['number']} [{item['category']}] {item['page']} -> {item['directive'] or item['title']}")
        return

    # Markdown format
    print(f"# 🎯 AgentLens Issues for `{args.repo}` ({len(parsed_items)} total)\n")
    if not parsed_items:
        print("No open issues found.")
        return

    print("| # | Category | Target File | Element Selector / Text | Directive | Link |")
    print("|---|----------|-------------|-------------------------|-----------|------|")
    for item in parsed_items:
        page = item['page'] or "N/A"
        selector = item['selector'] or item['element_text'] or "N/A"
        if len(selector) > 35:
            selector = selector[:32] + "..."
        directive = item['directive'] or item['title']
        if len(directive) > 60:
            directive = directive[:57] + "..."
        print(f"| **#{item['number']}** | `{item['category']}` | `{page}` | `{selector}` | {directive} | [View]({item['url']}) |")

    print("\n## 📋 Grouped Directives for AI Agent Execution\n")
    grouped = {}
    for item in parsed_items:
        p = item['page'] or "General"
        grouped.setdefault(p, []).append(item)

    for page, items in grouped.items():
        print(f"### 📄 `{page}` ({len(items)} task{'s' if len(items) > 1 else ''})")
        for it in items:
            print(f"\n- **Issue #{it['number']}** ({it['category']}): {it['directive'] or it['title']}")
            if it['selector']:
                print(f"  - **Selector**: `{it['selector']}`")
            if it['element_text']:
                print(f"  - **Element Text**: `{it['element_text']}`")
            if it['html_snippet']:
                print(f"  - **Snippet**: `{it['html_snippet'].replace(chr(10), ' ')}`")

if __name__ == "__main__":
    main()
