# Goal

**Tell you, in one command, which GitHub Actions steps still run on an outdated Node.js runtime and exactly which release of each action moves it to the current one, and apply that change safely.**

In scope: resolving `uses:` refs to their real runtime, composite/reusable nesting, suggesting and applying version bumps, CI gating and reporting.

Out of scope: general action version management unrelated to the runtime (that's Dependabot/Renovate), security pinning policy, running or linting workflows.
