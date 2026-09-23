#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""计算基线、采样阈值突破、观测发布频率、已核验配对与标签表现。

    python3 scripts/analyze.py dataset.csv findings.json [--breakout 100000] [--hit 3]

零值保留、未知为空，重复冲突拒绝。突破和频率按平台分别计算。
标签格按创作者×平台，默认至少20条，不跨创作者汇总为因果结论。
跨平台配对必须有人工核验的相同 content_id；以IG为锚点、日期±2天。
没有content_id时配对数为零，不用时间接近冒充同一内容。
launch_speed为历史兼容字段名，实际只是观测窗口发布频率，不计算涨粉。
"""
import argparse, csv, json, statistics, sys
from data_utils import number, iso_date
from collections import defaultdict
from datetime import date


def f(x):
    return number(x)


def load(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    seen, unique = {}, []
    for r in rows:
        if not r.get('creator_id') or r.get('platform') not in ('IG', 'TT', 'YT'):
            raise ValueError('Each row needs creator_id and platform IG/TT/YT')
        r['date'] = iso_date(r.get('date'))
        for k in ("views", "likes", "comments", "duration_s"):
            r[k] = f(r.get(k))
        key = (r['creator_id'], r['platform'], r.get('shortcode') or r.get('url'))
        if not key[2]:
            raise ValueError('Each row needs a content ID or URL')
        if key in seen:
            if r != seen[key]:
                raise ValueError('Conflicting duplicate content: ' + str(key))
            continue
        seen[key] = r
        unique.append(r)
    return unique


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def baselines(rows):
    out = {}
    for r in rows:
        out.setdefault((r["creator_id"], r["platform"]), []).append(r)
    table = {}
    for (c, p), sub in out.items():
        ds = sorted(x["date"] for x in sub if x.get("date"))
        table[f"{c}|{p}"] = {
            "creator": c, "platform": p, "n": len(sub),
            "n_views": sum(x['views'] is not None for x in sub),
            "median_views": med([x["views"] for x in sub]),
            "median_likes": med([x["likes"] for x in sub]),
            "first": ds[0] if ds else None, "last": ds[-1] if ds else None,
        }
    return table


def attach_multiples(rows, base):
    for r in rows:
        b = base.get(f"{r['creator_id']}|{r['platform']}", {})
        mv = b.get("median_views")
        r["mult"] = (r["views"] / mv) if (r["views"] is not None and mv) else None
    return rows


def breakout(rows, threshold=100000, platform="IG"):
    out = []
    by_creator = defaultdict(list)
    for r in rows:
        if r["platform"] == platform and r.get("date") and r["views"] is not None:
            by_creator[r["creator_id"]].append(r)
    for c, sub in by_creator.items():
        sub.sort(key=lambda r: r["date"])
        hit = next((i for i, r in enumerate(sub) if r["views"] >= threshold), None)
        if hit is None or hit < 5 or len(sub) - hit - 1 < 5:
            continue                      # too close to an edge to compare
        before = med([r["views"] for r in sub[:hit]])
        after = med([r["views"] for r in sub[hit + 1:]])
        out.append({"creator": c, "platform": platform, "scope": "first observed threshold crossing, not historical first", "n_before": hit, "n_after": len(sub)-hit-1, "index": hit + 1, "date": sub[hit]["date"],
                    "views": sub[hit]["views"], "url": sub[hit].get("url"),
                    "median_before": before, "median_after": after,
                    "lift": round(after / before, 1) if before else None})
    return sorted(out, key=lambda r: -(r["lift"] or 0))


def launch_speed(rows, platform="IG"):
    out = []
    by_creator = defaultdict(list)
    for r in rows:
        if r["platform"] == platform and r.get("date"):
            by_creator[r["creator_id"]].append(r["date"])
    for c, ds in by_creator.items():
        ds.sort()
        d0 = date.fromisoformat(ds[0]); d1 = date.fromisoformat(ds[-1])
        months = (d1 - d0).days / 30.44
        out.append({"creator": c, "first_post": ds[0], "months": round(months, 1),
                    "platform": platform, "scope": "observed publishing window; not account age or follower growth",
                    "posts": len(ds), "posts_per_month": round(len(ds) / months, 1) if months else None,
                    "followers": None, "followers_per_month": None})
    return sorted(out, key=lambda r: -(r["posts_per_month"] or 0))


def twins(rows, days=2):
    """Same creator, IG post <-> one post on another platform, published within `days`.

    Matching is greedy and one-to-one: each post is used at most once, closest
    date first. Pairing every nearby post with every other inflates the count
    (a creator who posts daily would produce thousands of "pairs").
    """
    pairs, by_creator = [], defaultdict(list)
    known = set()
    for r in rows:
        if r.get('content_id'):
            key = (r['creator_id'], r['platform'], r['content_id'])
            if key in known:
                raise ValueError('Ambiguous repeated content_id on one platform: ' + str(key))
            known.add(key)
        if r.get("date") and r["views"] is not None:
            by_creator[r["creator_id"]].append(r)
    for c, sub in by_creator.items():
        anchors = [r for r in sub if r["platform"] == "IG"]
        for plat in sorted({r["platform"] for r in sub if r["platform"] != "IG"}):
            others = [r for r in sub if r["platform"] == plat]
            cands = []
            for a in anchors:
                da = date.fromisoformat(a["date"])
                for o in others:
                    gap = abs((date.fromisoformat(o["date"]) - da).days)
                    # A shared content_id must be assigned after checking the actual content.
                    if gap <= days and a.get('content_id') and a.get('content_id') == o.get('content_id'):
                        cands.append((gap, id(a), id(o), a, o))
            cands.sort(key=lambda t: t[0])
            used_a, used_o = set(), set()
            for gap, ia, io, a, o in cands:
                if ia in used_a or io in used_o:
                    continue
                used_a.add(ia); used_o.add(io)
                pairs.append({"creator": c, "date": a["date"], "platform": plat, "gap_days": gap,
                              "ig_views": a["views"], "other_views": o["views"],
                              "ig_url": a.get("url"), "other_url": o.get("url")})
    per_creator = defaultdict(lambda: defaultdict(list))
    for p in pairs:
        per_creator[p["creator"]][p["platform"]].append((p["ig_views"], p["other_views"]))
    summary = []
    for c, plats in per_creator.items():
        row = {"creator": c, "pairs": sum(len(v) for v in plats.values())}
        ig_all = [ig for vs in plats.values() for ig, _ in vs]
        row["median_IG"] = med(ig_all)
        for plat, vs in plats.items():
            row[f'pairs_{plat}'] = len(vs)
            row[f'median_IG_for_{plat}'] = med([ig for ig, _ in vs])
            row[f"median_{plat}"] = med([o for _, o in vs])
            row[f"IG_over_{plat}"] = (round(med([ig for ig, _ in vs]) / row[f"median_{plat}"], 2)
                                      if row[f"median_{plat}"] else None)
        summary.append(row)
    return {"method": "IG-anchored, shared manually verified content_id, within 2 days; each post once per platform pair", "n_pairs": len(pairs), "pairs": pairs, "by_creator": sorted(summary, key=lambda r: -r["pairs"])}


def label_matrix(rows, column, hit=3.0, min_n=20):
    if not any(r.get(column) for r in rows):
        return None
    cells = defaultdict(list)
    for r in rows:
        if r.get(column) and r.get("mult") is not None:
            cells[(r['creator_id'], r[column], r["platform"])].append(r["mult"])
    out = []
    for (creator, label, plat), ms in sorted(cells.items()):
        if len(ms) < min_n:
            continue
        out.append({"creator": creator, column: label, "platform": plat, "n": len(ms),
                    "hit_rate_pct": round(100 * sum(1 for m in ms if m >= hit) / len(ms), 1),
                    "median_multiple": round(statistics.median(ms), 2)})
    return out


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("\n用法：python3 analyze.py dataset.csv findings.json [--breakout 100000] [--hit 3]")
    raise SystemExit(2)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('src'); p.add_argument('out')
    p.add_argument('--hit', type=float, default=3)
    p.add_argument('--breakout', type=float, default=100000)
    a = p.parse_args()
    src, out, hit, thr = a.src, a.out, a.hit, a.breakout
    if not (0 < hit < float('inf') and 0 < thr < float('inf')):
        p.error('thresholds must be positive and finite')
    rows = load(src)
    base = baselines(rows)
    rows = attach_multiples(rows, base)
    findings = {
        "rows": len(rows),
        "platforms": {p: sum(1 for r in rows if r["platform"] == p)
                      for p in sorted({r["platform"] for r in rows})},
        "text_coverage_pct": {p: round(100 * sum(1 for r in rows if r["platform"] == p and r.get("text"))
                                       / max(sum(1 for r in rows if r["platform"] == p), 1), 1)
                              for p in sorted({r["platform"] for r in rows})},
        "baselines": base,
        "breakout": [x for p in ('IG', 'TT', 'YT') for x in breakout(rows, thr, p)],
        "launch_speed": [x for p in ('IG', 'TT', 'YT') for x in launch_speed(rows, p)],
        "twins": twins(rows),
        "topics": label_matrix(rows, "topic", hit),
        "forms": label_matrix(rows, "form", hit),
    }
    json.dump(findings, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} rows · {findings['platforms']}")
    print(f"caption coverage: {findings['text_coverage_pct']}  <- anything far below 100 limits topic work")
    print(f"breakout posts: {len(findings['breakout'])} · twin pairs: {findings['twins']['n_pairs']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
