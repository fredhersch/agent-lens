---
name: review-agentlens-issues
description: >-
  Systematic workflow for reviewing, triaging, implementing, and auto-closing GitHub issues
  created via the AgentLens inline DOM feedback widget.
---

# AgentLens Issue Review & Resolution Skill

This skill guides the AI coding agent through an automated loop for reviewing and resolving issues filed with the **AgentLens** widget.

## 1. Fetch & Parse Open Issues

Run the AgentLens CLI fetcher:
```bash
python3 cli/fetch_issues.py --repo <owner/repo>
```

The script extracts:
- **Target Page / File**: The exact HTML or source file path (e.g., `src/pages/dashboard.html`)
- **CSS Selector**: The exact DOM selector (e.g., `#main-cta > button.btn-primary`)
- **Element Text**: The exact text snippet on the page
- **HTML Snippet**: Clean outer HTML of the target component
- **Category & User Directive**: What needs to be fixed or modified

## 2. Locate in Codebase

For each issue, locate the element with exact grounding:
```bash
git grep -n "<Element Text Snippet>" <Target File>
```

Review the surrounding 20–40 lines to understand component styling and framework bindings.

## 3. Implement & Test

Apply the requested change cleanly:
- Follow existing project conventions, styles, and framework components.
- Do not introduce unrelated refactors.

## 4. Commit, Push & Auto-Close

Commit using GitHub issue closing keywords:
```bash
git add <modified files>
git commit -m "fix(ui): <description of fix> (fixes #<issue_number>)"
git push origin main
```
GitHub will automatically transition the issue to closed!
