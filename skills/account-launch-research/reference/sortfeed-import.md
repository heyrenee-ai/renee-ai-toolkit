# 导入 CSV

本脚本兼容一组常见导出字段，不保证任何第三方工具的当前付费计划、导出完整性或字段能力。先检查实际表头、缺失和时间范围，不自动安装插件或购买服务。选题文本也可来自用户提供的转写和画面文字，不以某个工具订阅为前提。

```json
{
  "creator-slug": {
    "instagram_reels": ["reels.csv"],
    "instagram_posts": ["posts.csv"],
    "tiktok": ["tiktok.csv"],
    "youtube": ["youtube.csv"]
  }
}
```

```bash
python3 scripts/sortfeed_etl.py exports/ accounts.json dataset.csv
```

命令从 Skill 根目录执行。支持的精确列别名见 scripts/sortfeed_etl.py 的 ALIASES；未知表头先显式映射，不猜相似列。数值允许千位逗号与 K/M/B；时长可用秒或 mm:ss / hh:mm:ss；日期必须 ISO YYYY-MM-DD 或带时间后缀（截为来源所示日期，不做时区转换）。

IG reels/posts 按创作者+平台+shortcode 取并集，缺失字段互补；其他平台也去重。同一字段出现两个非空且不同的值就停止，先确认采集时间与字段含义。不能预设两种导出的覆盖关系或把冲突零值当缺失。

输出 creator_id、platform（IG/TT/YT）、url、shortcode、date、views、likes、comments、shares、saves、duration_s、title、text。缺文件、非法数值和日期应修正后再跑，不能把部分导入当全量。

核验 YouTube 样本是 Shorts、长视频还是混合；分别取数和分析，不从时长或工具名自动推断完整历史。分析前保留来源导出、查证时间与筛选规则。
