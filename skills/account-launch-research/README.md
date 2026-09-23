# Account Launch Research｜跨平台对标账号调研工具包

让 Claude 或 Codex 装上这个 skill，输入对标账号主页链接，或者目标赛道名。AI 会跨平台调研竞品账号表现，
分析账号内容表现变化、爆款表现、跨平台内容表现差异，输出 HTML 报告，给到个性化的账号运营和内容策略。
覆盖 Instagram、TikTok、YouTube。

---

## 它能回答 3 个问题

**1.【平台选择】该做哪个平台？**
该做哪个平台流量效率最佳？赛道竞争情况如何？

**2.【账号定位】该做成什么样的账号？**
账号属性（娱乐or干货？）、人设和定位对标竞品进行分析

**3.【内容策略】该做什么内容？**
跨平台爆款共性和差异是什么？做什么内容能够跨平台通吃？什么选题应该避免？该平台起号的关键因素是什么？

## 流程

① 告诉 AI 你的需求  
② AI 定位目标赛道和账号  
③ 通过浏览器采集数据  
④ 转写和打标  
⑤ 数据分析  
⑥ 输出 HTML 报告

## 需要什么

| 依赖 | 为什么需要 | 可选？ |
| --- | --- | --- |
| **Claude 或 Codex** | 跑这个 skill | 必需 |
| **当前 AI 工具可用的浏览器** | 在线查看公开账号；已有导出数据时可跳过 | 可选 |
| **Python 3.10+** | 跑脚本，只用标准库 | 必需 |
| **[SortFeed](https://sortfeed.com) 一类的导出工具** | 导出播放、caption、时长等字段，覆盖范围以实际导出为准 | 可选 |
| **yt-dlp + faster-whisper** | 只有问题三（钩子与脚本结构）需要：下载内容并本地转写 | 可选 |

分析脚本在本地运行，无需额外 API key；交给 Claude 或 Codex 的材料按对应服务的数据政策处理。

## 安装

**Claude Code / Codex**：把下面这句话发给 AI，让它帮你安装并检查环境：

> 请从 https://github.com/heyrenee-ai/renee-ai-toolkit 安装 skills/account-launch-research 整个工具包到当前客户端的个人 Skill 目录，保留脚本、模板和示例，并检查运行环境。如果已安装同名 Skill，先告诉我差异。

**Cowork**：下载仓库，将 `skills/account-launch-research/` 整个文件夹打成 ZIP，在 Skills 中上传并启用。不要只上传 `SKILL.md`。

## 怎么用

安装后，直接告诉 Claude 或 Codex 你想解决的问题，不需要自己输入代码。

**已经有对标账号：**

> 帮我分析这几个账号：[粘贴账号主页链接]。我想知道先做哪个平台、账号怎么定位，以及第一批内容可以做什么。

**只有一个赛道想法：**

> 我想做面向 AI 新手的教程账号，先帮我找同赛道的对标账号，再比较平台、账号定位和内容方向。

AI 会按上面的六步推进：确认需求、寻找账号、采集内容、转写和打标、分析数据，最后交付一份可以打开阅读的 HTML 报告。已有导出或素材也可以直接交给 AI；需要你补充信息时，它会告诉你。

**想先看效果：**

> 用工具包自带的虚构示例生成一份报告给我看。

随包示例的账号、日期和指标均为人工构造，不对应真实账号。

## 包里有什么

```
skills/account-launch-research/        ← 装这一个目录就够，里面是自包含的
  SKILL.md                     方法本身：环境自检 → 定决策 → 找账号 → 采集 → 三类决策 → 出报告 → 交付前自查
  reference/
    metrics.md                 每个指标的定义，以及这套东西明确不测量什么
    browser-recipes.md         可用的采集代码片段、限流规律、各平台的坑
    sortfeed-import.md         导出字段格局；为什么 Instagram 要取并集而不是 join
    report-writing.md          怎么写成演示稿：分节模板、措辞规则、什么观点配什么图
    hook-analysis.md           内容 DNA：从爆款里抽什么，以及怎么不过度解读
    analysis-checklist.md      Agent 使用的交付前自查清单
  scripts/
    preflight.py               环境自检：缺什么、缺的那样会挡住哪一步
    sortfeed_etl.py            CSV 导出   → dataset.csv
    analyze.py                 dataset.csv → findings.json（基线、观测突破、发布频率、核验配对、选题/形式矩阵）
    grid_stats.py              浏览器采集 → 每个账号的流量水平与趋势
    label.py                   打两个标签：选题（关键词规则 + agent 补漏）与形式（agent 核对原内容）
    fetch_media.py             URL 清单   → 媒体文件（可选，封装 yt-dlp）
    transcribe.py              本地媒体   → 转写、钩子、CTA（可选，Whisper）
    render_report.py           report.json → 单文件 HTML
    charts.py, report.css      七类图表（含柱状图）与页面样式
  templates/
    report.skeleton.json       报告骨架，复制了改，不要从空文件开始
    topic-rules.example.json   选题关键词规则模板
  examples/
    synthetic-accounts.jsonl      4 个虚构账号的合成数据，仅用于演示
    report.example.json/.html  一份渲染好的示例报告
```

## 许可

MIT，见 [LICENSE](LICENSE)。
