# Usage

Run from a repository root (or pass a path):

```bash
actnode                 # problems only
actnode path/to/repo --all   # every step, including the ones already on node24
```

What it scans: every file in `.github/workflows/*.yml|yaml`, plus a root `action.yml` if the repo is itself an action. Every `uses:` is resolved:

| Status | Meaning |
|---|---|
| `ok` | the action runs on node24 (or the `--target`) or newer |
| `OLD` + `->` | runs on an older Node; a newer release on node24 exists, shown after `->` |
| `OLD` + note | runs on an older Node and **no** release runs on node24 yet: open an issue upstream, fork, or replace it |
| `cmp` | composite action; the steps inside are checked and shown with `(inside …)` |
| `dkr` | Docker action, not affected |
| `?` | could not read `action.yml` (private repo, deleted ref, unpinned ref) |

## Fix

```bash
actnode --fix
git diff
```

Only direct `uses:` lines with a suggestion are rewritten. Quotes, indentation and trailing comments are kept; for SHA pins the trailing comment becomes the new version. Actions found *inside* composite actions can't be fixed in your repo: bump the composite action or ask its maintainer.

Major bumps can carry breaking changes (for example `upload-artifact` v4 → v6). Read the release notes before merging.

## Formats

```bash
actnode --format json -o actnode.json
actnode --format md -o "$GITHUB_STEP_SUMMARY"
```

## Gate

```bash
actnode --fail   # exit 1 if any old-runtime action is found
```
