#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把明确映射的 CSV 规范化成一张长表。

    python3 scripts/sortfeed_etl.py exports/ accounts.json dataset.csv

accounts.json 示例：
    {"creator-demo": {"instagram_reels": ["reels.csv"],
                      "instagram_posts": ["posts.csv"],
                      "tiktok": ["tiktok.csv"], "youtube": ["youtube.csv"]}}

按创作者、平台、内容 ID 合并互补字段，冲突时报错。表头用明确别名匹配。
未知表头先人工映射；不保证第三方导出完整性、帖子类型或当前产品能力。
CSV 的危险公式文本加单引号；保留原始输入用于逐字核验。
"""
import csv, json, os, re, sys
from data_utils import number, shortcode, iso_date, csv_safe

FIELDS = ["creator_id", "platform", "url", "shortcode", "date", "views", "likes",
          "comments", "shares", "saves", "duration_s", "title", "text"]

ALIASES = {
    "url": ["url", "post url", "link", "video url", "permalink"],
    "date": ["date", "post date", "published", "publish date", "created", "upload date", "time"],
    "views": ["views", "view count", "play count", "plays"],
    "likes": ["likes", "like count", "diggs", "hearts"],
    "comments": ["comments", "comment count"],
    "shares": ["shares", "share count"],
    "saves": ["saves", "save count", "collect count", "bookmarks"],
    "duration_s": ["duration", "length", "duration (s)", "seconds"],
    "title": ["title", "video title"],
    "text": ["caption", "description", "text", "post text", "content"],
}
PLATFORM = {"instagram_reels": "IG", "instagram_posts": "IG", "instagram": "IG",
            "tiktok": "TT", "youtube": "YT", "youtube_shorts": "YT"}


def pick(header):
    """header -> {canonical field: actual column name}"""
    low = {h.strip().lower(): h for h in header}
    out = {}
    for field, names in ALIASES.items():
        for n in names:
            if n in low:
                out[field] = low[n]
                break
    return out


def numeric(v):
    return number(v)


def duration(v):
    if v and ':' in str(v):
        parts = str(v).split(':')
        if len(parts) not in (2, 3) or any(not x.isdigit() for x in parts):
            raise ValueError('Invalid duration')
        if any(int(x) >= 60 for x in parts[1:]):
            raise ValueError('Invalid duration seconds/minutes')
        total = 0
        for x in parts: total = total * 60 + int(x)
        return total
    return number(v)


def read(path, creator, kind):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        cols = pick(rd.fieldnames or [])
        if 'url' not in cols:
            raise ValueError('No recognized URL column: ' + str(path))
        if 'views' not in cols:
            print('Warning: no recognized views column; values remain unknown')
        for raw in rd:
            row = {f: None for f in FIELDS}
            row["creator_id"] = creator
            row["platform"] = PLATFORM.get(kind, kind)
            for field, col in cols.items():
                val = raw.get(col)
                row[field] = duration(val) if field == "duration_s" else numeric(val) if field in (
                    "views", "likes", "comments", "shares", "saves", "duration_s") else (
                    (val or "").strip() or None)
            if row["date"]:
                row["date"] = iso_date(row["date"])
            row["shortcode"] = shortcode(row["url"])
            if not row['shortcode']:
                raise ValueError('Missing or unsupported direct post URL')
            rows.append(row)
    return rows


def merge_instagram(rows):
    """Union reels+posts on shortcode; a field wins if the other side is empty."""
    by_key, out = {}, []
    for r in rows:
        if not r["shortcode"]:
            out.append(r)
            continue
        key = (r["creator_id"], r["platform"], r["shortcode"])
        if key not in by_key:
            by_key[key] = r
            out.append(r)
        else:
            keep = by_key[key]
            for f in FIELDS:
                if f != 'url' and keep.get(f) not in (None, '') and r.get(f) not in (None, '') and keep[f] != r[f]:
                    raise ValueError(f'Conflicting duplicate {key}: {f}; resolve snapshots explicitly')
                if keep.get(f) in (None, "") and r.get(f) not in (None, ""):
                    keep[f] = r[f]
    return out


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("\n用法：python3 sortfeed_etl.py exports/ accounts.json dataset.csv")
    raise SystemExit(2)

def main():
    if len([a for a in sys.argv[1:] if not a.startswith("--")]) < 3:
        _usage()
    exports, mapping_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    mapping = json.load(open(mapping_path, encoding="utf-8"))
    rows = []
    for creator, kinds in mapping.items():
        for kind, files in kinds.items():
            for fn in files:
                path = os.path.join(exports, fn)
                if os.path.commonpath([os.path.realpath(exports), os.path.realpath(path)]) != os.path.realpath(exports):
                    raise ValueError('Mapped files must remain inside the exports directory')
                if not os.path.exists(path):
                    raise FileNotFoundError(fn)
                got = read(path, creator, kind)
                rows += got
                print(f"  {creator:24s} {kind:16s} {len(got):5d} rows  ({fn})")
    before = len(rows)
    rows = merge_instagram(rows)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(csv_safe(r) for r in rows)
    print(f"\n{before} rows in, {len(rows)} after the Instagram union -> {out_path}")


if __name__ == "__main__":
    main()
