# Changelog

## v0.2.0 — 2026-10-12
- Reusable workflows (`uses: org/repo/.github/workflows/x.yml@ref`) scanned recursively (status `workflow` / `wfl`); nested findings show `(inside …)` and are not rewritten by `--fix`
- Remote scan without cloning: `actnode --repo owner/name` and `actnode --org owner` (public non-fork repos by default; `--fix` refused)
- Tag lookups cached under `~/.cache/actnode` (or `$XDG_CACHE_HOME/actnode`), 24h TTL; `--no-cache` to skip

## v0.1.0 — 2026-10-11
First release: scan, composite following, smallest-major suggestions, `--fix`, `--fail`, JSON/Markdown output, GitHub Action.
