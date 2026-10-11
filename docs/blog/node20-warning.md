---
description: Why GitHub's "Node.js 20 actions are deprecated" warning keeps appearing, why FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 doesn't clear it, and how to find and bump every affected action.
---
# The Node 20 warning that won't go away

*2026-10-11*

Since June 2, 2026 GitHub-hosted runners run JavaScript actions on Node 24 by default. Every job that still uses an action whose `action.yml` says `using: node20` ends with an annotation like:

> Node.js 20 actions are deprecated. The following actions are running on Node.js 20 and may not work as expected: actions/checkout@v4.

Thousands of repositories have opened PRs and issues about it: [redis/redis#14938](https://github.com/redis/redis/pull/14938), [actions/deploy-pages#410](https://github.com/actions/deploy-pages/issues/410), and countless "Support Node.js 24" issues in third-party actions.

## Three things the warning doesn't tell you

1. **Where.** It names `actions/checkout@v4`, not the twelve workflow files and lines that use it.
2. **Hidden actions.** A composite action you call may itself use a node20 action. The warning names the inner action, which doesn't appear anywhere in your repo.
3. **The fix.** Which version runs on Node 24? For `checkout` it's v5; for `upload-artifact`, v6. For some third-party actions there is no such release yet.

The `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` switch runs them on Node 24 but the annotation still fires ([actions/runner#4295](https://github.com/actions/runner/issues/4295)), and it's a stopgap until Node 20 is removed from runners.

## How actnode answers them

For each `uses:` line, actnode downloads that action's `action.yml` **at the exact ref you pinned** and reads `runs.using`. If it's `composite`, it reads the steps inside and repeats. For anything older than Node 24 it lists the action's tags, walks majors from newest to oldest, and picks the smallest major whose newest release runs on Node 24. If you pinned a SHA, you get the SHA of that release back.

```console
$ actnode --fix
[OLD] .github/workflows/ci.yml:7   node20  actions/checkout@v4   -> actions/checkout@v5
actnode: rewrote 1 line(s)
```

Then keep it from coming back with the Action:

```yaml
- uses: Blackman99/actnode@v0.1.0
```

**Next:** [Migrating off Node 20 actions: a worked example](migrate-off-node20.md) walks through a full migration, including the nested cases `--fix` can't rewrite for you.

Source and issues: [github.com/Blackman99/actnode](https://github.com/Blackman99/actnode).
