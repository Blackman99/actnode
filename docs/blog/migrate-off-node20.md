---
description: A worked example of moving a real-world set of GitHub Actions workflows off Node 20 with actnode, including the three cases --fix can't do for you (local composite actions, composites like upload-pages-artifact, and third-party actions that pin node20 internally).
---
# Migrating off Node 20 actions: a worked example

*2026-10-11*

The [first post](node20-warning.md) explained why the "Node.js 20 actions are deprecated" warning sticks around. This one is the practical follow-up: a full migration of a small but realistic repository, with every command and every line of output copied from a real run of `actnode` 0.1.0 on 2026-10-11. Versions are whatever the upstream repositories had published that day.

## The starting point

Two workflows and one local composite action, pinned the way most repos are: a SHA pin with a version comment, plain major tags, a few third-party actions.

```yaml
# .github/workflows/ci.yml (steps)
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
- uses: actions/setup-node@v4
- uses: ./.github/actions/setup          # composite: actions/cache@v4 + npm ci
- run: npm test
- uses: actions/upload-artifact@v4

# .github/workflows/pages.yml (steps)
- uses: actions/checkout@v4
- uses: actions/configure-pages@v5
- uses: actions/upload-pages-artifact@v3
- uses: actions/deploy-pages@v4
- uses: softprops/action-gh-release@v2
- uses: peaceiris/actions-gh-pages@v4
- uses: docker/setup-buildx-action@v3
- uses: codecov/codecov-action@v5
```

## Step 1: one scan

```console
$ export GITHUB_TOKEN=$(gh auth token)   # avoids the 60 req/h anonymous limit
$ actnode --all
[OLD] .github/workflows/ci.yml:7     node20     actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  -> actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0
[OLD] .github/workflows/ci.yml:8     node20     actions/setup-node@v4  -> actions/setup-node@v5
[cmp] .github/workflows/ci.yml:11    composite  ./.github/actions/setup
[OLD] .github/workflows/ci.yml:11    node20     actions/cache@v4  -> actions/cache@v5   (inside ./.github/actions/setup)
[OLD] .github/workflows/ci.yml:13    node20     actions/upload-artifact@v4  -> actions/upload-artifact@v6
[OLD] .github/workflows/pages.yml:9  node20     actions/checkout@v4  -> actions/checkout@v5
[OLD] .github/workflows/pages.yml:10 node20     actions/configure-pages@v5  -> actions/configure-pages@v6
[cmp] .github/workflows/pages.yml:11 composite  actions/upload-pages-artifact@v3
[OLD] .github/workflows/pages.yml:11 node20     actions/upload-artifact@v4  -> actions/upload-artifact@v6   (inside actions/upload-pages-artifact@v3)
[OLD] .github/workflows/pages.yml:14 node20     actions/deploy-pages@v4  -> actions/deploy-pages@v5
[OLD] .github/workflows/pages.yml:18 node20     softprops/action-gh-release@v2  -> softprops/action-gh-release@v3
[ok ] .github/workflows/pages.yml:19 node24     peaceiris/actions-gh-pages@v4
[OLD] .github/workflows/pages.yml:20 node20     docker/setup-buildx-action@v3  -> docker/setup-buildx-action@v4
[cmp] .github/workflows/pages.yml:21 composite  codecov/codecov-action@v5
[OLD] .github/workflows/pages.yml:21 node20     actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea  -> actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd # v8.0.0   (inside codecov/codecov-action@v5)

11 step(s) run an action older than node24; 11 have a newer release ready.
```

The whole scan took about 7.5 seconds. A few things are already worth noticing:

- **The SHA pin got a SHA back**, with the version comment, so a pinning policy survives the bump.
- **`peaceiris/actions-gh-pages@v4` is fine.** Not every old-looking tag is a problem; actnode reads the `runs.using` of the ref you actually use.
- **Three of the eleven are `(inside …)`.** They are why the warning names actions you can't find with `grep`. `codecov/codecov-action@v5` is a composite action that pins `actions/github-script` at a node20 SHA, exactly what people reported in [codecov/codecov-action#1919](https://github.com/codecov/codecov-action/issues/1919).

## Step 2: `--fix` the direct lines

```console
$ actnode --fix
...
actnode: rewrote 8 line(s)
$ git diff
-      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
-      - uses: actions/setup-node@v4
+      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0
+      - uses: actions/setup-node@v5
...
-      - uses: actions/upload-artifact@v4
+      - uses: actions/upload-artifact@v6
...
-      - uses: actions/checkout@v4
-      - uses: actions/configure-pages@v5
+      - uses: actions/checkout@v5
+      - uses: actions/configure-pages@v6
...
-      - uses: actions/deploy-pages@v4
+      - uses: actions/deploy-pages@v5
...
-      - uses: softprops/action-gh-release@v2
+      - uses: softprops/action-gh-release@v3
...
-      - uses: docker/setup-buildx-action@v3
+      - uses: docker/setup-buildx-action@v4
```

Eight lines, indentation and `with:` blocks untouched. Running `actnode` again leaves exactly the three nested findings:

```console
$ actnode
[OLD] .github/workflows/ci.yml:11    node20  actions/cache@v4  -> actions/cache@v5   (inside ./.github/actions/setup)
[OLD] .github/workflows/pages.yml:11 node20  actions/upload-artifact@v4  -> actions/upload-artifact@v6   (inside actions/upload-pages-artifact@v3)
[OLD] .github/workflows/pages.yml:21 node20  actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea  -> actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd # v8.0.0   (inside codecov/codecov-action@v5)

3 step(s) run an action older than node24; 3 have a newer release ready.
```

`--fix` deliberately doesn't touch these: the line that needs to change isn't in your workflow file. Each of them needs a different move.

## Step 3: the three nested cases

**A local composite action** (`./.github/actions/setup`). This one *is* in your repo, just in another file. Edit `.github/actions/setup/action.yml` and change `actions/cache@v4` to the suggested `actions/cache@v5`.

**A first-party composite** (`actions/upload-pages-artifact`). The fix is to bump the composite, not the inner action. Which version? Change the ref and re-scan; it takes seconds:

```console
# with upload-pages-artifact@v4
[cmp] .github/workflows/pages.yml:11  composite  actions/upload-pages-artifact@v4
[OLD] .github/workflows/pages.yml:11  node20     actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02  -> actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6.0.0   (inside actions/upload-pages-artifact@v4)

# with upload-pages-artifact@v5
[cmp] .github/workflows/pages.yml:11  composite  actions/upload-pages-artifact@v5
[ok ] .github/workflows/pages.yml:11  node24     actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f     (inside actions/upload-pages-artifact@v5)
```

So **v4 is not enough**: it still pins a node20 `upload-artifact`. You need `upload-pages-artifact@v5` (released 2026-04-10). This is the most common "I bumped everything and the warning is still there" trap on Pages workflows.

**A third-party composite** (`codecov/codecov-action`). Same technique: `@v6` and `@v7` both pin `actions/github-script@ed5974…` which runs on node24, so `codecov/codecov-action@v6` is the smallest jump. Check its changelog first: a major bump of a third-party action can change inputs.

After those three edits:

```console
$ actnode
All actions run on node24 or newer (or are composite/docker).
```

## When there is no Node 24 release

Not every action has a way out. On another repo:

```console
$ actnode
[OLD] .github/workflows/x.yml:6  node12  actions-rs/toolchain@v1  no release on node24 yet; ask upstream or fork
[OLD] .github/workflows/x.yml:7  node12  actions/checkout@v2  -> actions/checkout@v5
[OLD] .github/workflows/x.yml:8  node16  actions/setup-python@v4  -> actions/setup-python@v6

3 step(s) run an action older than node24; 2 have a newer release ready.
```

`actions-rs/toolchain` has been archived since 2023, so asking upstream won't help: replace it (for Rust, a `run: rustup toolchain install …` step or a maintained alternative) or fork it and change `runs.using`. actnode's job is to make sure you find these now, while `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` still papers over them, rather than when Node 20 is removed from runners.

## Step 4: keep it from coming back

Add the Action to CI. It writes a Markdown table to the job summary and fails the job if an old-runtime action sneaks back in (for example through a copy-pasted snippet or a composite action that gets reverted):

```yaml
- uses: actions/checkout@v5
- uses: Blackman99/actnode@v0.1.0
```

Locally, the same gate is `actnode --fail` (exit 1 on any finding), and `actnode --format md -o report.md` / `--format json` give you the table or machine-readable output for a PR description.

## Checklist

1. `export GITHUB_TOKEN=$(gh auth token)` and run `actnode`.
2. `actnode --fix`, read the release notes of each major bump, commit.
3. For every `(inside …)` line: edit your local composite, or bump the outer action and re-scan until it's `ok`.
4. For "no release on node24 yet": replace or fork.
5. Add `Blackman99/actnode@v0.1.0` to CI.

Install: `pipx install git+https://github.com/Blackman99/actnode`. Source and issues: [github.com/Blackman99/actnode](https://github.com/Blackman99/actnode).
