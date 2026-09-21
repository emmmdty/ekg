# MAVEN-FACT 官方 EFD 代码（vendored）

上游 `THU-KEG/MAVEN-FACT` commit `67544719c60c6eb7587ed00a3e59df83822f6847`。
逐文件的**原样** SHA-256 在 [`UPSTREAM.json`](UPSTREAM.json)，之后的每一处改动都以 git diff 的形式
留在本目录，并在 `UPSTREAM.json` 的 `patches` 里说明理由。

## 为什么放进仓库

`gpu-4090` 解析不了 `github.com`，而项目规矩是代码必须经 git 到达服务器。把这次实验要用的三个
文件 vendored 进来，之后每一处透明补丁都是可审阅的 diff，而不是服务器上的未追踪改动。

## 已知的两处上游事实（**任何重跑前必须披露**）

1. **`trainEFD/train.py` 在 test 上选 epoch。** 原实现每个 epoch 在 `--test_data` 上评测，
   并记录 `best_tst_macro_f1 = max(历轮 test macro-F1)`（保存 checkpoint 那行是注释掉的）。
   也就是说，它报的是**评测集上的逐轮最大值**，不是用开发集选出来的那一轮。
   我们的适配加 `--dev_data`，按 dev 选 epoch 并报该轮的 test 指标；
   为了可比，也同时报它原本那个「test 逐轮最大值」。
2. **官方数字所在的 test 划分拿不到**（只经 `drive.google.com` 分发，两台服务器都不通；
   HuggingFace 上唯一镜像只有 train + validation）。所以本项目对它的复现只能到
   FR-016 的 **(b) 透明适配**，不可能到 (a)。见 [`../../docs/BASELINE_ROSTER.md`](../../docs/BASELINE_ROSTER.md) §3。

## 不做的事

- 不调它的超参、不换它的映射、不为了让它好看或难看改任何默认值；
- 不把它的论文数字与我们 dev 选模的数字直接相减。
