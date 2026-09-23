# 内容共性：先看内容，再归类

可用已获授权的媒体、caption、完整转写或逐帧画面文字。网格封面只支持封面分析，不能代替脚本。

所有命令从 Skill 根目录执行：

```bash
python3 scripts/fetch_media.py urls.txt media/ --audio
python3 scripts/transcribe.py media/ transcripts.json --model small --lang en
```

下载只访问直接公开帖子 URL，不使用 Cookie 或身份文件，失败停止整批。音频提取需要 ffmpeg。转写按 faster-whisper、openai-whisper、whisper.cpp 尝试已安装引擎；已选引擎运行失败时不自动换引擎重试。命名模型首次使用可能联网下载权重，提前说明资源与网络需求。

记录全文、时间段、source_url、前约12秒、推断句式及疑似 CTA。机器转写和正则匹配不是确认，必须核对原内容；未找到不等于没有。无音轨时读取画面文字并注明 source: on-screen text。

同时观察高低表现样本，描述共性和反例。不规定应找到几种句式，不复制历史样本的 CTA 公式，不写“用此开头就会爆”。比较封面承诺、标题范围、内容兑现、CTA位置和样本覆盖。

本地脚本不主动上传媒体，但把转写、画面或文本交给云模型仍涉及该服务的数据处理。不要将未授权第三方全文或媒体公开附在报告里。
