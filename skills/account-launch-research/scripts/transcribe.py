#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转写你已经拿到的媒体文件，并从每条里抽出开头句。

    python3 transcribe.py media/ transcripts.json [--model small] [--lang en]

这是可选的问题三路径（爆款内容有什么共性）。它只处理**你磁盘上已有的文件**——
`fetch_media.py` 抓下来的，或你自己的录屏。

引擎按这个顺序尝试：

  1. faster-whisper   pip install faster-whisper      （CPU 友好，推荐）
  2. openai-whisper   pip install openai-whisper
  3. whisper.cpp      brew install whisper-cpp        （需设 WHISPER_CPP_MODEL）

每个文件输出：全文、前约 12 秒作为钩子、钩子句式的猜测，以及疑似 CTA 的句子。
句式猜测只是你自己判读的起点，字段标了 `inferred`，这个限定词要一路带进报告。

**完全没有音轨不是失败**（设计类、教程类很常见）：这类内容本来就没有口播脚本，
画面文字就是脚本。自己逐帧读下来，记成 `source: "on-screen text"`。
"""
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path

HOOK_PATTERNS = [
    ("problem_then_fix", r"^(it|this|that)\s+(looks|feels|sounds)\s+\w+[.,]"),
    ("if_you", r"^if\s+you('|’)?(re|ve)?\b"),
    ("numbered_list", r"^here\s+(are|is)\s+\d+|^\d+\s+\w+\s+(you|that|to)\b"),
    ("result_first", r"^(we|i)\s+(got|made|built|scored|earned|turned)\b"),
    ("question", r"^(what|why|how|who)\b.*\?|^what\s+if\b"),
    ("news_hook", r"\b(just\s+(dropped|released|launched)|recently\s+dropped)\b"),
    ("callout", r"^(if\s+you'?re\s+a|attention|to\s+every)\b"),
]
CTA = re.compile(r"\b(comment|dm|drop\s+a|link\s+in\s+bio|save\s+this|follow\s+(for|along)|"
                 r"check\s+out|search\s+for)\b", re.I)


def classify(hook):
    h = hook.strip().lower()
    for name, pat in HOOK_PATTERNS:
        if re.search(pat, h):
            return name
    return "other"


def with_faster_whisper(path, model, lang):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(path, language=lang, vad_filter=True)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs]


def with_openai_whisper(path, model, lang):
    import whisper
    out = whisper.load_model(model).transcribe(path, language=lang)
    return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in out["segments"]]


def with_whisper_cpp(path, model, lang):
    mp = os.environ.get("WHISPER_CPP_MODEL")
    if not mp:
        raise RuntimeError("set WHISPER_CPP_MODEL to a ggml model path")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, 'audio.wav')
        prefix = os.path.join(tmp, 'transcript')
        subprocess.run(["ffmpeg", "-i", path, "-ar", "16000", "-ac", "1", wav],
                       check=True, capture_output=True)
        subprocess.run(["whisper-cpp", "-m", mp, "-f", wav, "-l", lang, "-oj", "-of", prefix],
                       check=True, capture_output=True)
        data = json.load(open(prefix + '.json', encoding='utf-8'))
    return [{"start": s["offsets"]["from"] / 1000, "end": s["offsets"]["to"] / 1000,
             "text": s["text"].strip()} for s in data["transcription"]]


ENGINES = [("faster-whisper", with_faster_whisper),
           ("openai-whisper", with_openai_whisper),
           ("whisper.cpp", with_whisper_cpp)]


def transcribe(path, model, lang):
    errors = []
    for name, fn in ENGINES:
        try:
            return name, fn(path, model, lang)
        except ImportError:
            errors.append(f"{name}: not installed")
        except Exception as exc:
            raise RuntimeError(f'{name} failed; no automatic engine fallback') from exc
    raise RuntimeError("no engine worked -> " + " | ".join(errors))


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("\n用法：python3 transcribe.py media/ transcripts.json [--model small] [--lang en]")
    raise SystemExit(2)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('src'); p.add_argument('out', nargs='?', default='transcripts.json')
    p.add_argument('--model', default='small'); p.add_argument('--lang', default='en')
    a = p.parse_args()
    src, out, model, lang = a.src, a.out, a.model, a.lang
    mp = os.path.join(src if os.path.isdir(src) else os.path.dirname(src), 'manifest.json')
    manifest = json.loads(Path(mp).read_text(encoding='utf-8')) if os.path.exists(mp) else {}
    sources = {v['file']: v.get('url') for v in manifest.values() if v.get('file')}
    files = ([src] if os.path.isfile(src) else
             [os.path.join(src, f) for f in sorted(os.listdir(src))
              if f.lower().endswith((".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm"))])
    rows = []
    for path in files:
        try:
            engine, segs = transcribe(path, model, lang)
        except Exception as exc:
            rows.append({"file": os.path.basename(path), "error": str(exc)})
            print(f"  ! {os.path.basename(path)}: {exc}")
            continue
        text = " ".join(s["text"] for s in segs).strip()
        hook = " ".join(s["text"] for s in segs if s["start"] < 12).strip()
        ctas = [s["text"] for s in segs if CTA.search(s["text"])]
        rows.append({
            "file": os.path.basename(path), "engine": engine, "text": text,
            "source_url": sources.get(os.path.basename(path)), "segments": segs,
            "hook": hook, "hook_pattern": classify(hook), "hook_pattern_inferred": True,
            "spoken_cta": ctas[-1] if ctas else None,
            "cta_confirmed": False, "cta_candidate_inferred": bool(ctas),
            "words": len(text.split()),
        })
        print(f"  {os.path.basename(path):40s} {rows[-1]['words']:5d} words  "
              f"[{rows[-1]['hook_pattern']}]")
    Path(out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    ok = [r for r in rows if "text" in r]
    print(f"\n{len(ok)}/{len(rows)} transcribed -> {out}")
    if len(ok) != len(rows):
        raise SystemExit(1)
    if ok:
        from collections import Counter
        print("hook patterns:", dict(Counter(r["hook_pattern"] for r in ok)))
        print("Remember: an empty spoken_cta means UNCONFIRMED, not 'no CTA'.")


if __name__ == "__main__":
    main()
