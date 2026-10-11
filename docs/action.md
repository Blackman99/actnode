# GitHub Action

```yaml
name: node-runtime
on: [pull_request, workflow_dispatch]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: Blackman99/actnode@v0.1.0
        with:
          fail: true
```

The step writes a Markdown table to the job summary and fails if any step uses an action older than Node 24.

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `path` | `.` | repository root to scan |
| `target` | `24` | minimum Node major |
| `fail` | `true` | fail the step when something old is found |
| `token` | `github.token` | used to list tags of the actions you use |

## Outputs

| Output | Meaning |
|---|---|
| `report` | path to the JSON report |
