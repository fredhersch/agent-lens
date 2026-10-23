# AgentLens Workflow for Claude Code

## Commands to Review Issues
- Fetch open UI directives: `python3 cli/fetch_issues.py --repo <owner/repo>`
- Format issues as JSON: `python3 cli/fetch_issues.py --repo <owner/repo> --format json`

## Directive Grounding Strategy
1. Read the parsed `Target Page / File` and `CSS Selector`.
2. Grep for the `Element Text` within the target file.
3. Apply the directive requested by the user.
4. Auto-close via commit: `git commit -m "fix(ui): resolve #<issue_number>"`
