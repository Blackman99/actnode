---
description: 用 actnode 把一个贴近真实的仓库从 Node 20 action 完整迁移出来的实录，包括 --fix 改不了的三种情况：本地 composite action、upload-pages-artifact 这类 composite，以及在内部锁定 node20 的第三方 action。
---
# 迁移出 Node 20 action：一次完整实操

*2026-10-11*

[上一篇](node20-warning-zh.md)讲了 “Node.js 20 actions are deprecated” 警告为什么一直消不掉。这篇是实操续集：把一个小而真实的仓库完整迁移一遍。文中每条命令和输出都来自 2026-10-11 用 `actnode` 0.1.0 实际运行的结果，版本号以上游仓库当天已发布的为准。

## 起点

两个 workflow 加一个本地 composite action，锁版本的方式和大多数仓库一样：带版本注释的 SHA、普通大版本 tag，再加几个第三方 action。

```yaml
# .github/workflows/ci.yml (steps)
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
- uses: actions/setup-node@v4
- uses: ./.github/actions/setup          # composite：actions/cache@v4 + npm ci
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

## 第 1 步：扫一遍

```console
$ export GITHUB_TOKEN=$(gh auth token)   # 避免匿名 60 次/小时的限流
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

整个扫描约 7.5 秒。有几点值得注意：

- **锁 SHA 的拿回的也是 SHA**，还带上版本注释，原有的锁定策略在升级后依然成立。
- **`peaceiris/actions-gh-pages@v4` 没问题。** 看起来旧的 tag 不一定有问题，actnode 读的是你实际引用的那个 ref 的 `runs.using`。
- **11 条里有 3 条是 `(inside …)`。** 这正是警告里会出现你在仓库里 `grep` 不到的 action 的原因。`codecov/codecov-action@v5` 是个 composite action，内部把 `actions/github-script` 锁在一个 node20 的 SHA 上，和 [codecov/codecov-action#1919](https://github.com/codecov/codecov-action/issues/1919) 里大家报告的一样。

## 第 2 步：用 `--fix` 改直接引用的行

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

改了 8 行，缩进和 `with:` 块都没动。再跑一次 `actnode`，只剩 3 条嵌套的：

```console
$ actnode
[OLD] .github/workflows/ci.yml:11    node20  actions/cache@v4  -> actions/cache@v5   (inside ./.github/actions/setup)
[OLD] .github/workflows/pages.yml:11 node20  actions/upload-artifact@v4  -> actions/upload-artifact@v6   (inside actions/upload-pages-artifact@v3)
[OLD] .github/workflows/pages.yml:21 node20  actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea  -> actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd # v8.0.0   (inside codecov/codecov-action@v5)

3 step(s) run an action older than node24; 3 have a newer release ready.
```

`--fix` 故意不碰这几条：需要改的那一行不在你的 workflow 文件里。三种情况各有各的改法。

## 第 3 步：三种嵌套情况

**本地 composite action**（`./.github/actions/setup`）。它*就在*你的仓库里，只是在另一个文件。打开 `.github/actions/setup/action.yml`，把 `actions/cache@v4` 改成建议的 `actions/cache@v5`。

**官方 composite**（`actions/upload-pages-artifact`）。要升级的是外层 composite，而不是里面的 action。升到哪个版本？改一下 ref 再扫一次，几秒钟的事：

```console
# with upload-pages-artifact@v4
[cmp] .github/workflows/pages.yml:11  composite  actions/upload-pages-artifact@v4
[OLD] .github/workflows/pages.yml:11  node20     actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02  -> actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6.0.0   (inside actions/upload-pages-artifact@v4)

# with upload-pages-artifact@v5
[cmp] .github/workflows/pages.yml:11  composite  actions/upload-pages-artifact@v5
[ok ] .github/workflows/pages.yml:11  node24     actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f     (inside actions/upload-pages-artifact@v5)
```

所以 **v4 不够**：它内部仍锁着一个 node20 的 `upload-artifact`。必须升到 `upload-pages-artifact@v5`（2026-04-10 发布）。这是 Pages workflow 里最常见的“全都升级了警告还在”的坑。

**第三方 composite**（`codecov/codecov-action`）。同样的办法：`@v6` 和 `@v7` 内部锁的 `actions/github-script@ed5974…` 都跑在 node24 上，所以跨度最小的是 `codecov/codecov-action@v6`。升级前先看它的 changelog：第三方 action 的大版本可能改了输入参数。

改完这三处：

```console
$ actnode
All actions run on node24 or newer (or are composite/docker).
```

## 没有 Node 24 版本怎么办

不是每个 action 都有出路。另一个仓库的结果：

```console
$ actnode
[OLD] .github/workflows/x.yml:6  node12  actions-rs/toolchain@v1  no release on node24 yet; ask upstream or fork
[OLD] .github/workflows/x.yml:7  node12  actions/checkout@v2  -> actions/checkout@v5
[OLD] .github/workflows/x.yml:8  node16  actions/setup-python@v4  -> actions/setup-python@v6

3 step(s) run an action older than node24; 2 have a newer release ready.
```

`actions-rs/toolchain` 从 2023 年起就已归档，去上游提 issue 没用：换掉它（Rust 可以直接用 `run: rustup toolchain install …`，或换一个仍在维护的替代品），或者 fork 后改 `runs.using`。actnode 的作用是让你现在就把这些找出来——趁 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` 还能暂时兜底，而不是等 Node 20 从 runner 上移除那天才发现。

## 第 4 步：防止回退

在 CI 里加上 Action。它会在 job summary 里写一张 Markdown 表；一旦有旧运行时的 action 混回来（比如复制粘贴的片段，或某个 composite action 被回滚），job 就失败：

```yaml
- uses: actions/checkout@v5
- uses: Blackman99/actnode@v0.1.0
```

本地同样的检查是 `actnode --fail`（发现问题时退出码为 1）；`actnode --format md -o report.md` 和 `--format json` 可以生成表格或机器可读的结果，方便贴到 PR 描述里。

## 清单

1. `export GITHUB_TOKEN=$(gh auth token)`，运行 `actnode`。
2. `actnode --fix`，逐个阅读大版本的 release notes，提交。
3. 每条 `(inside …)`：改本地 composite，或升级外层 action 后重新扫描，直到变成 `ok`。
4. “no release on node24 yet”：替换或 fork。
5. 在 CI 里加上 `Blackman99/actnode@v0.1.0`。

安装：`pipx install git+https://github.com/Blackman99/actnode`。源码与反馈：[github.com/Blackman99/actnode](https://github.com/Blackman99/actnode)。
