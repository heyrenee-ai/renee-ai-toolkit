# Account Launch Research｜跨平台对标账号调研工具包

让 Claude 装上这个 skill，输入对标账号主页链接，或者目标赛道名。AI 会跨平台调研竞品账号表现，
分析账号成长曲线、爆款表现、跨平台内容表现差异，输出 HTML 报告，给到个性化的账号运营和内容策略。
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
| **Claude 能驱动的浏览器**——[Claude in Chrome 插件](https://claude.ai/chrome)，或 Claude 桌面版内置浏览器 | 三大平台都拒绝服务端抓取，浏览器是唯一入口，用的是你自己的登录态 | 必需 |
| **Python 3.10+** | 跑脚本，只用标准库 | 必需 |
| **[SortFeed](https://sortfeed.com) 一类的导出工具** | 拿到带 caption、时长的全量历史。没有也能跑——浏览器路径能拿到粉丝数、播放、趋势、形式，但拿不到 caption，选题分析做不了 | 可选 |
| **yt-dlp + faster-whisper** | 只有问题三（钩子与脚本结构）需要：下载内容并本地转写 | 可选 |

不需要 API key，不需要注册，没有服务端。所有脚本在本地跑，数据不出你的机器。

## 安装

**这是一个 skill，不是一个应用**——skill 目录是自包含的：方法、脚本、模板、示例都在里面，拷一个目录就能用。

```bash
git clone https://github.com/heyrenee-ai/renee-ai-toolkit
cd renee-ai-toolkit

# Claude Code：整个 skill 目录拷过去（脚本在目录内，不要只拷 SKILL.md）
mkdir -p ~/.claude/skills
# 若同名目录已存在，先比较和备份。
cp -r skills/account-launch-research ~/.claude/skills/

# 检查环境，缺什么它会告诉你
python3 ~/.claude/skills/account-launch-research/scripts/preflight.py
```

- **Cowork**：将 `skills/account-launch-research/` 整个目录打成 ZIP，在 Skills 中上传并启用；方法、脚本、模板、示例需一起保留。

## 怎么用

直接说人话，skill 自己判断走哪条路：

> 「帮我拆解这五个账号，告诉我主场该选哪个平台：@handle1、@handle2……」

> 「在 TikTok 和 Instagram 上找 15–20 个不露脸的 AI 工具账号，判断这个赛道还值不值得进。」

Claude 会先跟你确认要回答哪些决策，再采集、分析、出报告。底层大致是：

```bash
# 从仓库根目录执行；已经在本工具包目录时跳过下一行。
cd skills/account-launch-research

# 深度路径——有导出数据
python3 scripts/sortfeed_etl.py exports/ accounts.json dataset.csv
python3 scripts/analyze.py dataset.csv findings.json

# 浅路径——只有浏览器采集
python3 scripts/grid_stats.py captures.jsonl stats.json --window 36

# 两条路都要的最后一步（报告骨架在 templates/report.skeleton.json）
python3 scripts/render_report.py report.json report.html --standalone
```

用包里自带的真实采集数据试一下浅路径，两条命令就能看到成品：

```bash
# 从仓库根目录执行；已经在本工具包目录时跳过下一行。
cd skills/account-launch-research
python3 scripts/grid_stats.py examples/tiktok-ai-niche.jsonl /tmp/stats.json
python3 scripts/render_report.py examples/report.example.json /tmp/demo.html --standalone && open /tmp/demo.html
```

## 包里有什么

```
skills/account-launch-research/        ← 装这一个目录就够，里面是自包含的
  SKILL.md                     方法本身：环境自检 → 定决策 → 找账号 → 采集 → 四个问题 → 出报告 → 交付前自查
  reference/
    metrics.md                 每个指标的定义，以及这套东西明确不测量什么
    browser-recipes.md         可用的采集代码片段、限流规律、各平台的坑
    sortfeed-import.md         导出字段格局；为什么 Instagram 要取并集而不是 join
    report-writing.md          怎么写成演示稿：分节模板、措辞规则、什么观点配什么图
    hook-analysis.md           内容 DNA：从爆款里抽什么，以及怎么不过度解读
    analysis-checklist.md      交付前自查清单，每一条都来自一次真实的翻车
  scripts/
    preflight.py               环境自检：缺什么、缺的那样会挡住哪一步
    sortfeed_etl.py            CSV 导出   → dataset.csv
    analyze.py                 dataset.csv → findings.json（基线、破圈条、起号速度、跨平台孪生、选题/形式矩阵）
    grid_stats.py              浏览器采集 → 每个账号的流量水平与趋势
    label.py                   打两个标签：选题（关键词规则 + agent 补漏）与形式（agent 看缩略图打）
    fetch_media.py             URL 清单   → 媒体文件（可选，封装 yt-dlp）
    transcribe.py              本地媒体   → 转写、钩子、CTA（可选，Whisper）
    render_report.py           report.json → 单文件 HTML
    charts.py, report.css      六种图表（哑铃、占比条、象限、成对点、散点、堆叠条）与页面样式
  templates/
    report.skeleton.json       报告骨架，复制了改，不要从空文件开始
    topic-rules.example.json   选题关键词规则模板
  examples/
    tiktok-ai-niche.jsonl      13 个真实 TikTok 账号的公开主页采集数据
    report.example.json/.html  一份渲染好的示例报告
```

## 许可

MIT，见 [LICENSE](LICENSE)。
