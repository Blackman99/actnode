---
description: 为什么 GitHub Actions 的 “Node.js 20 actions are deprecated” 警告一直在，为什么 FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 消不掉它，以及如何一次找出并升级所有受影响的 action。
---
# 那条去不掉的 Node 20 警告

*2026-10-11*

从 2026 年 6 月 2 日起，GitHub 托管 runner 默认用 Node 24 运行 JavaScript action。只要 job 里还有 `action.yml` 写着 `using: node20` 的 action，结尾就会出现：

> Node.js 20 actions are deprecated. The following actions are running on Node.js 20 and may not work as expected: actions/checkout@v4.

大量仓库都在为它提 PR 和 issue，比如 [redis/redis#14938](https://github.com/redis/redis/pull/14938)、[actions/deploy-pages#410](https://github.com/actions/deploy-pages/issues/410)，还有第三方 action 仓库里数不清的 “Support Node.js 24”。

## 警告没告诉你的三件事

1. **在哪。** 它只说 `actions/checkout@v4`，不说是哪些 workflow 文件、哪一行。
2. **藏起来的 action。** 你调用的 composite action 内部可能用了 node20 action，警告里的名字在你的仓库里根本搜不到。
3. **升到哪个版本。** checkout 是 v5，upload-artifact 是 v6，有些第三方 action 至今没有 Node 24 版本。

设置 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` 能让它们跑在 Node 24 上，但警告照样出现（[actions/runner#4295](https://github.com/actions/runner/issues/4295)），而且 Node 20 从 runner 移除后这个开关也没用了。

## actnode 怎么做

对每一行 `uses:`，actnode 按你锁定的**确切 ref** 下载该 action 的 `action.yml`，读 `runs.using`；遇到 composite 就继续读里面的步骤。凡是低于 Node 24 的，列出它的 tag，从最新大版本往回找，给出**跨度最小**、且最新版跑在 Node 24 上的大版本。锁 SHA 的会拿回对应版本的 SHA。

```console
$ actnode --fix
[OLD] .github/workflows/ci.yml:7   node20  actions/checkout@v4   -> actions/checkout@v5
actnode: rewrote 1 line(s)
```

再在 CI 里加上 Action，防止回退：

```yaml
- uses: Blackman99/actnode@v0.1.0
```

源码与反馈：[github.com/Blackman99/actnode](https://github.com/Blackman99/actnode)。
