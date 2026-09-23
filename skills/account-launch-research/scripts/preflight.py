#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开工前自检：这台机器缺什么，缺的那样会挡住哪一步。

    python3 scripts/preflight.py

按「必需 / 可选」两档检查，并且**明确告诉你缺的东西会让哪个分析做不了**——
不是简单报一句 not found。退出码：必需项齐全为 0，否则为 1。
"""
import importlib.util, shutil, subprocess, sys

OK, NO = "  ✅", "  ❌"


def has_module(name):
    return importlib.util.find_spec(name) is not None


def main():
    problems, notes = [], []
    print("Account Launch Research · 环境自检\n")

    # ── 必需 ──────────────────────────────────────────────
    print("必需")
    v = sys.version_info
    if (v.major, v.minor) >= (3, 10):
        print(f"{OK} Python {v.major}.{v.minor}.{v.micro}")
    else:
        print(f"{NO} Python {v.major}.{v.minor} —— 需要 3.10+")
        problems.append("升级 Python 到 3.10 以上")
    print(f"{OK} 分析脚本只用标准库，无需 pip 安装")

    print("\n  数据入口（手动确认：已有导出、获授权 API、手工记录或浏览器）")
    print("     · Claude in Chrome 插件：https://claude.ai/chrome")
    print("     · 以当前客户端实际提供且获授权的能力为准")
    print("     本自检不验证浏览器访问或账号身份；不读取凭据。")

    # ── 可选：问题三（钩子与脚本结构） ─────────────────────
    print("\n可选 · 问题三（爆款的钩子与脚本结构）需要转写")
    if shutil.which("yt-dlp"):
        try:
            ver = subprocess.run(["yt-dlp", "--ignore-config", "--version"], capture_output=True, text=True,
                                 timeout=20).stdout.strip()
        except Exception:
            ver = "?"
        print(f"{OK} yt-dlp {ver}")
    else:
        print(f"{NO} yt-dlp —— 没有它就下载不了内容，问题三只能靠自己录屏或逐帧读画面")
        notes.append("pip install -U yt-dlp        # 或 brew install yt-dlp")

    engines = [("faster_whisper", "pip install faster-whisper"),
               ("whisper", "pip install openai-whisper")]
    if any(has_module(m) for m, _ in engines):
        got = [m for m, _ in engines if has_module(m)]
        print(f"{OK} 转写引擎：{', '.join(got)}")
    elif shutil.which("whisper-cpp"):
        print(f"{OK} 转写引擎：whisper.cpp（记得设 WHISPER_CPP_MODEL）")
    else:
        print(f"{NO} 转写引擎 —— 没有它就只能人工听写或读画面文字")
        notes.append("pip install faster-whisper   # CPU 友好，推荐")

    if shutil.which("ffmpeg"):
        print(f"{OK} ffmpeg")
    else:
        print(f"{NO} ffmpeg —— 下载音频转换、openai-whisper、whisper.cpp 路径需要；faster-whisper 解码不需系统 ffmpeg")
        notes.append("按平台官方指南安装 ffmpeg（仅在用户选择所需功能后）")

    # ── 可选：SortFeed 导出 ───────────────────────────────
    print("\n可选 · CSV 导出或可核验的文本 / 转写 / 画面文字")
    print("     核对实际字段覆盖，不保证第三方工具的当前能力。")
    print("     无文本/原内容时仅做指标分析，不猜选题。")

    # ── 结论 ──────────────────────────────────────────────
    print("\n" + "─" * 52)
    if problems:
        print("必需项缺失，先解决这些：")
        for p in problems:
            print("  ·", p)
    else:
        print("Python 检查通过：可运行离线计算；采集能力、权限与模型尚未验证。")
    if notes:
        print("以下仅是安装建议，不会自动执行。安装、下载模型可能联网并占用空间；先确认用户选择。")
        print("\n想跑问题三（钩子与脚本结构），再装这些：")
        for n in notes:
            print("  ", n)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
