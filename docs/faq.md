# FAQ

**Why not just set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`?**
It runs node20 actions on Node 24 today, but the deprecation annotation still fires ([actions/runner#4295](https://github.com/actions/runner/issues/4295)) and the opt-out disappears when Node 20 is removed from runners. Actually upgrading the actions is the durable fix.

**Doesn't Dependabot do this?**
Dependabot opens version bumps if it's configured for `github-actions`, one PR per action, and doesn't tell you which ones are about the runtime or which are hidden inside composite actions. actnode answers the runtime question across the whole repo in one run, and works where Dependabot isn't set up.

**Why the smallest major and not the latest?**
Fewer breaking changes. `actions/checkout@v5` already runs on Node 24; you don't need to jump to v7 to clear the warning. Pick the latest on your own schedule.

**An action has no Node 24 release. Now what?**
actnode reports it as `OLD` with "no release on node24 yet". Look for an open issue upstream (many exist: search "Node.js 24" in that repo), fork and change `runs.using`, or replace the action.

**Does it work with private actions?**
Actions in private repos need a token that can read them (`GITHUB_TOKEN`). Local `./` actions are read from disk.

**Reusable workflows (`uses: org/repo/.github/workflows/x.yml@v1`)?**
Reported as `?` in v0.1. Recursive scanning of reusable workflows is on the [roadmap](https://github.com/Blackman99/actnode/blob/main/ROADMAP.md).
