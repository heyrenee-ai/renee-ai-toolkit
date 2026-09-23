# Creator Benchmark Kit｜跨平台对标账号调研工具包

给 Claude 装上这个 Skill，输入对标账号或赛道，基于获授权的 Instagram、TikTok、YouTube 公开数据，整理平台选择、账号定位和内容策略的证据，输出可复算的单文件 HTML 报告。数据不足时明确回答「不能判断」。

这是方法 + Python 脚本，不是一键爬虫或增长预测器。采集、内容核验和报告文字需要 Agent / 使用者完成；脚本负责清洗、计算和渲染。

## 能做什么

- 导入 CSV，保留缺失与零值，合并重复内容并报告冲突。
- 从主页快照计算播放中位数、播放/当前粉丝、近/中/早窗口指标。
- 计算采样范围内的阈值突破、发布频率及创作者内的选题/形式表现。
- 对人工核验并赋予相同 content_id 的跨平台内容进行配对比较。
- 可选下载获授权的公开视频、转写已有媒体，整理待核验的 Hook / CTA。
- 把有来源、有局限的分析整理成 HTML，支持七类 SVG 图表。

不提供历史涨粉曲线、转化率或因果结论。公开播放量会随内容年龄变化；当前快照不能独立证明赛道降温或形式造成增长。

## 安装

需要 Python 3.10+。计算和报告脚本只用标准库。

```bash
git clone https://github.com/heyrenee-ai/renee-ai-toolkit
cd renee-ai-toolkit
mkdir -p ~/.claude/skills
# 若同名目录已存在，先比较和备份，不直接覆盖。
cp -R skills/account-launch-research ~/.claude/skills/
python3 ~/.claude/skills/account-launch-research/scripts/preflight.py
```

Claude Code 中可直接描述需求，或调用 /account-launch-research。整个目录包含方法、脚本、模板、示例和 MIT 许可，不能只拷 SKILL.md。

Cowork / Claude：将 account-launch-research 整个文件夹打成 ZIP，在 Customize → Skills 上传并启用。界面、套餐及组织权限可能不同；仅上传 SKILL.md 不会附带脚本。参见 [Claude Code 官方安装说明](https://code.claude.com/docs/en/skills) 与 [Claude Skills 上传说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude)（核对于 2026-09-23）。

## 先跑一个离线例子

```bash
# 从仓库根目录进入；若已经在本 Skill 目录，请跳过 cd。
cd skills/account-launch-research
python3 scripts/preflight.py
python3 scripts/grid_stats.py examples/tiktok-ai-niche.jsonl /tmp/stats.json
python3 scripts/build_example.py /tmp/report.json
python3 scripts/render_report.py /tmp/report.json /tmp/demo.html --standalone
```

用浏览器打开 /tmp/demo.html。build_example.py 直接从随包快照计算表格和图表；report.example.json / .html 是同一流程生成的展示。

示例含 13 个公开账号的提供方快照；提供方标注采集日为 2026-09-22，本包没有原始截图可独立验证日期、标签及采集完整性。ID 推算日期仅是推断，部分记录只有日期而无逐条 URL。它用于演示计算，不代表当前账号事实或赛道结论。原始素材权利不因本仓库的 MIT 许可而转移。

## 实际使用

> 帮我比较这五个账号的公开内容，判断哪个平台值得先测试。我有导出 CSV。

> 调研不露脸的 AI 教程赛道；先限定样本和问题，证据不足的地方不要下结论。

```bash
# 以下命令均从 skill 目录执行，输入文件由使用者提供。
python3 scripts/sortfeed_etl.py exports/ accounts.json dataset.csv
python3 scripts/label.py dataset.csv templates/topic-rules.example.json dataset-tagged.csv --form forms.json
python3 scripts/analyze.py dataset-tagged.csv findings.json
python3 scripts/render_report.py report.json report.html --standalone
```

accounts.json 格式见 reference/sortfeed-import.md。findings.json 不会自动变成策略报告：Agent 按 templates/report.skeleton.json 写 report.json，核对每个标题数字和来源，再渲染。

## 数据、网络与费用

分析、打标和渲染脚本不上传数据；HTML 不加载外部字体或脚本。**这不等于数据不出机器**：交给 Claude / 云模型的网页、文本或文件会进入对应服务的处理流程，请按自己的账户与隐私设置决定输入范围。

采集可用已有导出、获授权 API、手工记录或当前环境支持的浏览器工具，不要求登录。不要读取或导出 Cookie、token、认证配置，不代登录；遇到验证码、限流或访问限制停止当前采集，不更换通道规避。

下载和转写是可选项。yt-dlp 下载会访问平台；--audio 的格式转换需要 ffmpeg。faster-whisper 首次使用命名模型通常下载权重；openai-whisper 也需要模型且通常需要系统 ffmpeg。耗时、磁盘、网络及 Claude / 导出工具费用不包含在本包内。只有用户选择这条路径并同意相应环境变更时才安装依赖，建议独立虚拟环境。本包不会自动安装。参见 [yt-dlp](https://github.com/yt-dlp/yt-dlp)、[faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[Whisper](https://github.com/openai/whisper)。

本包不保证任何平台当下可下载，也未替你取得第三方媒体的再发布权。只处理获授权范围，不点赞、关注、评论或私信。

## 文件与限制

本目录下的 reference/ 是方法与数据口径，scripts/ 是可执行程序，templates/ 是起草输入，examples/ 是有局限的公开快照展示。

离线计算及报告生成已通过合成数据测试。尚未完成真实平台采集、下载、ASR、Claude安装界面及HTML浏览器目视验收；这些环境相关能力需要使用时另行核验。

- 缩写播放数只能视为近似值；缺失不是零，零分母比值为空。
- 时间邻近不是同一内容。跨平台配对目前以 IG 为锚点；无已核验 content_id 时输出零配对。
- 时间先后和相关不能证明因果；账号样本不能代表整个平台。
- CSV 输出会给可能被电子表格当成公式的文本添加单引号前缀；保留原始导出作为逐字证据。
- HTML 仅保留有限的文字格式与 HTTP(S) 链接，不能嵌入脚本、图片或任意 HTML。

MIT，见 [LICENSE](LICENSE)。依赖各自适用其许可；本仓库没有捆绑依赖代码、字体、模型权重或第三方视频。
