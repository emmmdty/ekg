# DR-B 引用可移植化修复提示词

请在**生成 DR-B 的同一个网页版深度研究会话**中发送以下提示词；不要新开会话。

```text
你刚才生成的 B_datasets.md 内容已保存，但导出的 Markdown 保留了 140 个
`cite...` / `filecite...` 内部引用标记，离开当前 ChatGPT 会话后无法解析；
顶部 `sandbox:/mnt/data/B_datasets.md` 也不可用。请不要重新调研，不要新增结论，
只把同一份报告重新导出为“离线可审计 Markdown”。

硬性要求：
1. 删除顶部 sandbox 下载链接和所有 `cite...`、`filecite...` 标记。
2. 每个外部来源改为普通 Markdown 链接：`[来源名称](https://...)`。
3. 论文优先链接 ACL Anthology、会议官方页、DOI、arXiv 原文；数据/test/license/repo
   必须链接官方数据页、官方竞赛页或官方 GitHub，不能只链接搜索结果。
4. 本地附件引用改成普通文字路径：
   `docs/replan/EXPLORATION_PROMPT.md`、`docs/replan/LOCAL_ASSET_INVENTORY.md`。
5. 在全文末尾增加“离线来源注册表”，每行格式：
   `Sxx | 支持的结论 | 来源标题 | 论文ID/表号/章节 | 原始 https:// URL`。
6. 所有 URL 必须以明文 `https://` 实际写入下载文件；不要依赖 ChatGPT UI 的引用气泡。
7. 为防 UI 再次转换引用，另附一个 fenced code block，逐行列出全部原始 URL。
8. 保持现有事实、数字、“未取得/不可比”标记和表格不变；不要趁机补猜或改变结论。
9. 时区改为 Asia/Taipei。
10. 输出新的可下载文件，文件名仍为 `B_datasets.md`。输出前自检：
    - 字符串 `cite` 出现次数必须为 0；
    - 字符串 `filecite` 出现次数必须为 0；
    - 字符串 `sandbox:` 出现次数必须为 0；
    - 原始 `https://` URL 数量必须大于 0。

只做引用可移植化，不重新执行 DR-B。
```
