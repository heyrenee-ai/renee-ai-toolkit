# Account Launch Research｜跨平台对标账号调研工具包

让 Claude 装上这个 skill，输入对标账号主页链接，或者目标赛道名。AI 会跨平台调研竞品账号表现，
分析账号成长曲线、爆款表现、跨平台内容表现差异，输出 HTML 报告，给到个性化的账号运营和内容策略。
覆盖 Instagram、TikTok、YouTube。

---

## 它能回答 3 个问题

**1.【平台选择】该做哪个平台？**
同一条内容在三个平台的真实播放差多少、哪个平台的单位粉丝触达效率最高、这个赛道现在挤不挤、还在涨还是在退。

**2.【账号定位】该做成什么样的账号？**
露脸还是不露脸、口播还是录屏还是图文、对标账号靠什么起来的（持续输出还是一条爆款）、
哪些对标账号其实不值得学——比如粉丝靠别处导流、或者某个平台其实是空号。

**3.【内容策略】该做什么内容？**
跨平台爆款的共性和差异、哪些选题能跨平台通吃、哪些只在单一平台成立、哪些该避开，
以及起号的关键因素（转折点、发布量门槛）。

## 流程

① 告诉 AI 你的需求
② AI 定位目标赛道和账号
③ 通过浏览器采集数据
④ 转写和打标
⑤ 数据分析
⑥ 输出 HTML 报告

15–20 个账号大约半天，其中第 ③ 步最慢——按真人速度一个主页一个主页开。

## 两个和「让 AI 总结一下竞品」的区别

- **每条结论都挂着可点开的原视频链接**，结论能核对。
- **播放数跟这个账号自己的中位数比**，不看绝对值——所以 8,000 粉的账号和 90 万粉的账号能放进同一张表。

## 一个真实的输出

`examples/report.example.html` 是渲染好的例子（13 个 TikTok 账号的不露脸赛道评估）。
两条命令重新生成：

```bash
# 从仓库根目录执行；已经在本工具包目录时跳过下一行。
cd skills/account-launch-research
python3 scripts/grid_stats.py examples/tiktok-ai-niche.jsonl /tmp/stats.json
python3 scripts/render_report.py examples/report.example.json /tmp/demo.html --standalone
```

---

## 需要什么

| 依赖 | 为什么需要 | 可选？ |
| --- | --- | --- |
| **Claude Code 或 Cowork 模式的 Claude** | 跑这个 skill | 必需 |
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

## 方法的六条硬规则

1. **先定决策，再取数。** 不回答具体决策的对标调研只是一份清单。
2. **每条内容跟自己账号的中位比**，不用分母看不见的第三方评分——这才让 8,000 粉和 90 万粉的账号能放进同一张表。
3. **必须有对照组。** 「不露脸在衰退」如果不拿同赛道的露脸账号对照，就分不清是形式问题还是整个赛道在降温（我们这轮的结论是后者，假设没成立）。
4. **逐条打标签，不要账号级标签。** 12 个账号里我们打错了 3 个；跨平台最稳的那个创作者同时在用五种形式。
5. **每条结论挂可点开的链接。**
6. **交付前重算一遍。** 这条自查在我们自己身上生效过：一个已经发出去的跨平台比值，重算后发现差了 17 倍。

## 一开始就要说清的局限

- 主页网格和导出看到的都是创作者**留下来的**内容，幸存者偏差在每个数字里。
- 固定 N 条的窗口对不同账号覆盖的时间差异极大，趋势必须带窗口天数一起报。
- **转化率这套数据测不了。** 文案里的引流钩子不是转化证据——同一句 CTA 经常在视频里口播，而 caption 里什么都没有。
- 时间上的先后不是因果，报告里该这么写就这么写。

## 使用规范

只读浏览，速度接近真人，用你自己的登录态。不点赞、不关注、不评论、不私信。只看公开主页数据，
不要去拼凑账号背后那个人的私人信息。不要把凭证交给 agent，也不要试图绕过验证码或限流——平台说不行就停。
遵守各平台的服务条款，怎么用由你负责。

## 许可

MIT，见 [LICENSE](LICENSE)。

## 当前发布版补充说明

以上保留原版介绍与使用思路。当前脚本不提供历史涨粉曲线，也不能仅凭公开快照证明导流、赛道涨退或起号的因果门槛；原文中的研究经历和耗时不作为本次验证结果。示例现为 13 个账号的提供方快照数值演示，采集日期与完整性未独立验证，不是已确认的赛道评估。每条结论应附可核验来源，缺失时明确标注。

浏览器不是唯一数据入口，也不要求登录；可使用已有导出、获授权 API 或手工记录。选题分析需要文本或原内容证据，不限于 caption；形式标签需核对原内容，不能仅凭缩略图。分析与渲染脚本本地运行，但交给 Claude 的数据会进入对应服务，不能保证数据不出机器。媒体下载与模型下载可能联网，下载和转写均为可选。

HTML 浏览器目视、真实平台采集、下载、ASR 和 Claude 安装界面尚未验证；离线计算与报告生成测试已通过。
