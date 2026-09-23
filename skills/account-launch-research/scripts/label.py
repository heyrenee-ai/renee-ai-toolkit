#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给数据集打两个标签：这条在讲什么（topic）、它是什么形式（form）。

    python3 label.py dataset.csv rules.json dataset-tagged.csv [--form forms.json]

默认打这两个标签；其他维度仅在实际问题和样本支持时添加。

topic —— 关键词规则先跑一遍，剩下的交给 agent
------------------------------------------------
rules.json 一个选题一组关键词（大小写不敏感，支持正则）：

    {
      "T1 AI 工具实操": ["chatgpt", "claude", "\\bai tool", "prompt"],
      "T4 搞钱/变现":   ["make money", "side hustle", "\\$\\d", "income"]
    }

规则命中多条时按 rules.json 里的顺序取第一条，并在 `topic_src` 记 `rule`。
没命中的留空、记 `topic_src=unmatched`，脚本会把它们单独导出成 `*-unmatched.csv`，
让 agent 逐条读 caption / transcript 补上——**这一步 agent 自己能做，不用外包**。
补完的文件用 `--merge` 再跑一次即可合并回来。

form —— agent 核对原片后打，脚本只负责合并
------------------------------------------------
forms.json 是 `{"<shortcode 或 video id>": "P"}`，取值：
P 真人出镜｜S 实景画面｜A AI 生成｜T 纯文字/录屏｜R 搬运他人素材。
逐条打，不要按账号打；封面判断会高估 P，所以脚本会打印 P 的占比提醒你核对。

输出：原表 + `topic` / `topic_src` / `form` 三列，可直接喂给 analyze.py。
"""
import argparse, csv, json, re, sys
from data_utils import csv_safe
from collections import Counter

FORM_NAMES = {"P": "真人出镜", "S": "实景画面", "A": "AI 生成", "T": "纯文字/录屏", "R": "搬运"}


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("\n用法：python3 label.py dataset.csv rules.json dataset-tagged.csv [--form forms.json] [--merge 补好的-unmatched.csv]")
    raise SystemExit(2)


def compile_rules(path):
    raw = json.load(open(path, encoding="utf-8"))
    out = []
    for topic, pats in raw.items():
        if topic.startswith("_"):            # 以 _ 开头的是注释键，跳过
            continue
        if isinstance(pats, str):            # 写成字符串会被逐字符编译，直接拦下来
            raise SystemExit(f"规则 {topic!r} 的值要是一个列表，不是字符串")
        out.append((topic, [re.compile(p, re.I) for p in pats]))
    if not out:
        raise SystemExit("规则文件里没有可用的规则（以 _ 开头的键会被忽略）")
    return out


def main():
    p = argparse.ArgumentParser(description='打选题和形式标签；用法：输入 CSV、规则 JSON、输出 CSV')
    p.add_argument('src'); p.add_argument('rules'); p.add_argument('out')
    p.add_argument('--form'); p.add_argument('--merge')
    a = p.parse_args()
    opt = {k: v for k, v in [('--form', a.form), ('--merge', a.merge)] if v}
    src, rules_path, out = a.src, a.rules, a.out

    rules = compile_rules(rules_path)
    forms = json.load(open(opt["--form"], encoding="utf-8")) if "--form" in opt else {}
    if any(v not in FORM_NAMES for v in forms.values()):
        raise ValueError('Unknown form code; use P/S/A/T/R')
    merged = {}
    if "--merge" in opt:                       # agent 补完的 unmatched 表
        for r in csv.DictReader(open(opt["--merge"], encoding="utf-8")):
            if r.get("topic"):
                merged[r.get("url") or r.get("shortcode")] = r["topic"]

    reader = csv.DictReader(open(src, encoding="utf-8"))
    fields = list(reader.fieldnames or [])
    rows = list(reader)
    id_counts = Counter(r.get('shortcode') for r in rows)
    for extra in ("topic", "topic_src", "form"):
        if extra not in fields:
            fields.append(extra)

    unmatched, counts, src_counts = [], Counter(), Counter()
    for r in rows:
        key = r.get("url") or r.get("shortcode")
        text = " ".join(filter(None, [r.get("text"), r.get("title"), r.get("transcript")]))
        if key in merged:                                  # agent 补的最优先
            r["topic"], r["topic_src"] = merged[key], "agent"
        elif not text.strip():
            r["topic"], r["topic_src"] = "", "no-text"     # 没文本就打不了，别硬猜
        else:
            for topic, pats in rules:
                if any(p.search(text) for p in pats):
                    r["topic"], r["topic_src"] = topic, "rule"
                    break
            else:
                r["topic"], r["topic_src"] = "", "unmatched"
                unmatched.append(r)
        sc = r.get("shortcode") or ""
        if sc in forms and id_counts[sc] > 1:
            raise ValueError('Ambiguous shortcode label; use full URL: ' + sc)
        r["form"] = forms.get(key) or forms.get(sc) or r.get("form") or ""
        if r['form'] and r['form'] not in FORM_NAMES:
            raise ValueError('Unknown form in input')
        counts[r["topic"] or "（未标）"] += 1
        src_counts[r["topic_src"]] += 1

    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(csv_safe(r) for r in rows)

    print(f"{len(rows)} 条 → {out}\n")
    print("选题分布")
    for topic, n in counts.most_common():
        print(f"  {topic:26s} {n:5d}  {n/len(rows):5.1%}")
    print("\n标签来源：" + "  ".join(f"{k}={v}" for k, v in src_counts.most_common()))

    if unmatched:
        un_path = out.rsplit(".", 1)[0] + "-unmatched.csv"
        with open(un_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(csv_safe(r) for r in unmatched)
        print(f"\n{len(unmatched)} 条没命中规则 → {un_path}")
        print("  agent 逐条读 text 填 topic 列，然后：python3 label.py ... --merge 这个文件")

    no_text = src_counts.get("no-text", 0)
    if no_text:
        print(f"\n⚠️ {no_text} 条没有任何文本（{no_text/len(rows):.0%}），选题结论只能建立在有文本的那部分上，报告里要写明。")

    if forms:
        fc = Counter(r["form"] for r in rows if r["form"])
        print("\n形式分布：" + "  ".join(f"{FORM_NAMES.get(k,k)}={v}" for k, v in fc.most_common()))
        p_share = fc.get("P", 0) / max(sum(fc.values()), 1)
        if p_share > 0.5:
            print(f"  ⚠️ 真人出镜占 {p_share:.0%}——按封面打标会高估这一类，"
                  f"抽 15 条点开正片核对一致率，把这个比例写进报告。")
    else:
        print("\n形式标签：先核对原片证据，未知留空；仅看缩略图的推断不能确认AI或来源性质。存成 "
              "{\"shortcode\": \"P\"} 再用 --form 合并。")


if __name__ == "__main__":
    main()
