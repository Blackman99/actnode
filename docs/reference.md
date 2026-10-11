# Command reference

```
actnode [scan] [PATH] [--target N] [--format text|json|md] [-o FILE] [--fix] [--fail] [--all]
actnode demo
actnode --version
```

| Flag | Meaning |
|---|---|
| `PATH` | repository root (default `.`) |
| `--target N` | minimum Node major an action must run on (default 24) |
| `--format` | `text` (default), `json` (every finding), `md` (problem table, for job summaries) |
| `-o FILE` | write to a file; `md` appends (so it works with `$GITHUB_STEP_SUMMARY`) |
| `--fix` | rewrite direct `uses:` lines to the suggested ref |
| `--fail` | exit code 1 if any step uses an older runtime |
| `--all` | in text mode, also show `ok`, composite and docker steps |

Exit codes: `0` ok, `1` old runtime found with `--fail`, `2` GitHub API rate limit (set a token).

## JSON shape

```json
{"target": 24, "findings": [
  {"file": ".github/workflows/ci.yml", "line": 7, "uses": "actions/checkout@v4",
   "runtime": "node20", "status": "old", "suggest": "actions/checkout@v5", "via": null, "note": ""}
]}
```
