#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把浏览器采集到的主页网格变成可比较的账号级指标。

输入：JSONL，一行一个账号，用 reference/browser-recipes.md 里的片段采集：

    {"handle":"smart.easy","platform":"tiktok","face":"不露脸",
     "form":"图文卡片","followers":"892.9K","pinned":3,
     "items":"7663878944277499143:1.9M;7546704462451166472:554.1K"}   # id:播放
    {"handle":"uncover.ai","platform":"instagram","followers":"787K",
     "items":"260921:12200;260920:21600"}                            # yymmdd:播放

`items` 两种写法都认。TikTok 的 id 和 Instagram 的 shortcode 都会被换算成发布日期，
ID 日期为启发式推断，须与页面时间核对；输出窗口长度帮助发现不可比性。

输出：一个 JSON 列表，逐账号给出中位播放、播放/粉丝、窗口内近/中/早三段的中位、
近÷早、窗口覆盖天数，以及最高的那一条。

    python3 grid_stats.py accounts.jsonl stats.json [--window 36]
"""
import argparse, json, re, signal, statistics, sys
from data_utils import number
from datetime import datetime, timezone, timedelta

try:                       # 允许 `... | head` 这类管道提前关闭，不抛 BrokenPipeError
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

IG_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
IG_EPOCH_MS = 1314220021721  # Instagram's media-id epoch


def num(s):
    """K/M/B are approximate display counts; never imply exact precision."""
    n = number(s)
    return round(n) if n is not None else None


def tiktok_date(vid):
    """TikTok video id carries the publish time in its high 32 bits."""
    return datetime.fromtimestamp(int(vid) >> 32, timezone.utc).date()


def instagram_date(shortcode):
    """Instagram shortcode -> media id -> publish time."""
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', shortcode):
        raise ValueError('Unsupported Instagram shortcode; supply an explicit date')
    n = 0
    for ch in shortcode[:11]:
        n = n * 64 + IG_ALPHABET.index(ch)
    return (datetime(1970, 1, 1, tzinfo=timezone.utc)
            + timedelta(milliseconds=(n >> 23) + IG_EPOCH_MS)).date()


def parse_key(key, platform):
    if re.fullmatch(r"\d{6}", key):                       # yymmdd
        return datetime.strptime(key, "%y%m%d").date()
    if platform.startswith('tik') and re.fullmatch(r"\d{15,}", key):
        return tiktok_date(key)
    if platform.startswith("ins"):
        return instagram_date(key)
    raise ValueError(f"cannot read a date out of {key!r}")


def account_stats(rec, window=36):
    if window < 6:
        raise ValueError('window must be at least 6')
    platform = rec.get("platform", "tiktok")
    items = []
    chunks = [c.strip() for c in rec['items'].split(';') if c.strip()]
    if rec.get('pinned_leading'):
        count = rec.get('pinned', 0)
        if not isinstance(count, int) or not 0 <= count <= len(chunks):
            raise ValueError('Invalid pinned count')
        chunks = chunks[count:]
    seen = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        key, views = chunk.rsplit(":", 1)
        v = num(views)
        # A six-digit date is not a post ID: multiple posts can share that date.
        if not re.fullmatch(r'\d{6}', key):
            if key in seen:
                if seen[key] != v:
                    raise ValueError('Conflicting duplicate post: ' + key)
                continue
            seen[key] = v
        items.append({"key": key, "date": parse_key(key, platform).isoformat(), "views": v})
    items.sort(key=lambda it: it["date"], reverse=True)
    # 采集片段已经跳过了置顶内容（rec["pinned"] 只是个计数）。如果你的采集把置顶也收了进来，
    # 它们会排在最前且与日期无关——先在采集侧剔掉，别在这里按位置猜。
    items = items[:window]
    if any(it['views'] is None for it in items):
        raise ValueError('Selected chronological window contains unknown views; do not substitute older posts. Resolve missing counts before segmentation.')
    if len(items) < 6:
        raise ValueError(f"{rec['handle']}: only {len(items)} posts — too few to segment")
    vs = [it["views"] for it in items]
    boundaries = [i * len(items) // 3 for i in range(4)]
    seg = [statistics.median(vs[boundaries[i]:boundaries[i+1]]) for i in range(3)]
    followers = num(rec.get("followers"))
    best = max(items, key=lambda it: it["views"])
    return {
        "handle": rec["handle"], "platform": platform,
        "face": rec.get("face"), "form": rec.get("form"),
        "followers": followers, "n": len(items),
        "segment_n": [boundaries[i+1]-boundaries[i] for i in range(3)],
        "date_basis": "explicit YYMMDD or inferred from ID; verify on page",
        "counts_approximate": True,
        "evidence_scope": "supplied snapshot; unequal content age, not causal growth",
        "median_views": statistics.median(vs),
        "views_per_follower": round(statistics.median(vs) / followers, 4) if followers else None,
        "recent": seg[0], "middle": seg[1], "oldest": seg[2],
        "recent_over_oldest": round(seg[0] / seg[2], 2) if seg[2] else None,
        "window_days": (max(it["date"] for it in items) != min(it["date"] for it in items)) and
                       (datetime.fromisoformat(max(it["date"] for it in items))
                        - datetime.fromisoformat(min(it["date"] for it in items))).days or 0,
        "first": min(it["date"] for it in items), "last": max(it["date"] for it in items),
        "best_views": best["views"], "best_key": best["key"],
        "best_url": post_url(rec["handle"], platform, best["key"]),
        "best_url_inferred": True,
    }


def post_url(handle, platform, key):
    if platform.startswith("tik") and re.fullmatch(r"\d{15,}", key):
        return f"https://www.tiktok.com/@{handle}/video/{key}"
    if platform.startswith("ins") and re.fullmatch(r"[A-Za-z0-9_-]{11}", key):
        return f"https://www.instagram.com/reel/{key}/"
    return None


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("\n用法：python3 grid_stats.py accounts.jsonl stats.json [--window 36]")
    raise SystemExit(2)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('src'); p.add_argument('out', nargs='?', default='stats.json')
    p.add_argument('--window', type=int, default=36)
    a = p.parse_args()
    if a.window < 6: p.error('window must be at least 6')
    window = a.window
    rows, problems = [], []
    for line in open(a.src, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        try:
            rows.append(account_stats(rec, window))
        except Exception as exc:          # keep going, report at the end
            problems.append(f"{rec.get('handle','?')}: {exc}")
    rows.sort(key=lambda r: -(r["followers"] or 0))
    out = a.out
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    head = f"{'handle':22s}{'form':10s}{'followers':>10s}{'n':>4s}{'days':>6s}{'recent':>9s}{'oldest':>9s}{'rec/old':>9s}{'v/f':>7s}"
    print(head); print("-" * len(head))
    for r in rows:
        print(f"{r['handle']:22s}{(r['form'] or '')[:9]:10s}{str(r['followers']):>10s}{r['n']:>4d}"
              f"{r['window_days']:>6d}{r['recent']:>9,.0f}{r['oldest']:>9,.0f}"
              f"{str(r['recent_over_oldest']):>9s}{str(r['views_per_follower']):>7s}")
    if problems:
        print("\nskipped:"); [print("  " + p) for p in problems]
    print(f"\nwrote {out}")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
