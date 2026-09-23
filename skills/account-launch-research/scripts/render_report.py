#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把声明式的 report.json 渲染成一个单文件 HTML 页面。

    python3 render_report.py report.json out.html [--standalone]

agent 写 report.json（结论文字 + 它核对过的数字），这个脚本只负责排版——
渲染不验证数据和推断是否真实；必须先复算并核对证据。

结构
----
{
  "title": "...", "subtitle": "...", "eyebrow": "...", "lang": "zh",
  "facts": [["标签","值"], ...],
  "footer": ["一段 html", ...],
  "sections": [
    {"id":"breakout","kicker":"结论 01","title":"...","class":"","blocks":[ <block>, ... ]}
  ]
}

block 类型
----------
{"type":"headline","html":"..."}                    一节的大标题：结论本身
{"type":"sub","html":"..."}                         大标题下面小一号的解释
{"type":"so_what","html":"..."}                     「行动」块：这条结论意味着做什么
{"type":"fine","html":"..."}                        小字：方法、样本量、局限
{"type":"takeaways","items":[{"n":"01","h":"...","p":"..."}]}
{"type":"p","html":"..."} / {"type":"h3","text":"..."} / {"type":"list","items":[...]}
{"type":"cards","items":[{"h":"...","p":"..."}]}
{"type":"callout","h":"...","p":["...","..."]}       修订 / 降级的结论
{"type":"box","h":"...","p":["..."]}
{"type":"details","summary":"展开：...","blocks":[ ... ]}    附录里的折叠块
{"type":"table","head":[...],"rows":[[...]],"note":"..."}
{"type":"chart","kind":"lift","rows":[[标签,前,后,"17.5×"]]}
{"type":"chart","kind":"share","rows":[[标签,0.35,"35% · 说明"]],"base_label":"..."}
{"type":"chart","kind":"quadrant","points":[[x,y,"标签",是否强调]],"xlab":"...","ylab":"..."}
{"type":"chart","kind":"paired","rows":[[标签,[a,b]]],"series":[["名","--yt"],["名","--tt"]]}
{"type":"chart","kind":"bars","rows":[[标签,[v1,v2,v3]]],"series":[...],"unit":"%"}
{"type":"chart","kind":"scatter","points":[[x,y,"标签",是否强调]],"xlab":"...","ylab":"..."}
{"type":"chart","kind":"mix","parts":[["标签",0.6,"--accent"]]}
"""
import json, os, sys, re, math
from pathlib import Path
from report_safety import safe_doc
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import charts

PALETTE = [("--ig", "Instagram"), ("--tt", "TikTok"), ("--yt", "YouTube")]


def table(b):
    head = "".join(f"<th>{c}</th>" for c in b["head"])
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in b["rows"])
    note = f'<p class="note">{b["note"]}</p>' if b.get("note") else ""
    return f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>{note}'


def chart(b):
    kind = b["kind"]
    values = b.get('rows', b.get('points', b.get('parts', [])))
    if not values:
        return '<p class="fine">No chart data / 无可绘制数据</p>'
    def validate(x):
        if isinstance(x, (int, float)) and (not math.isfinite(x) or x < 0):
            raise ValueError('Charts require finite non-negative values')
        if isinstance(x, list):
            for v in x: validate(v)
    validate(values)
    for _, var in b.get('series', []):
        if not re.fullmatch(r'--[a-z][a-z0-9-]*', var): raise ValueError('Invalid chart color')
    if kind in ('bars', 'paired'):
        count = len(b.get('series', []))
        if not count or (kind == 'paired' and count != 2) or any(len(row[1]) != count for row in values):
            raise ValueError('Chart values must match the series count; paired requires two')
    if kind == 'mix':
        for _, share, var in values:
            if not re.fullmatch(r'--[a-z][a-z0-9-]*', var): raise ValueError('Invalid chart color')
        if not math.isclose(sum(x[1] for x in values), 1, abs_tol=0.001):
            raise ValueError('Mix shares must sum to one')
    if kind == 'share' and any(not 0 <= r[1] <= 1 for r in values):
        raise ValueError('Share chart accepts only ratios from zero to one')
    if kind == "lift":
        return charts.lift_chart([tuple(r) for r in b["rows"]], title=b.get("title", ""))
    if kind == "bars":
        unit = b.get("unit", "")
        fmt = (lambda v: f"{v:g}{unit}") if unit else (lambda v: f"{v:,.0f}")
        return charts.grouped_bars([(r[0], r[1]) for r in b["rows"]],
                                   [tuple(s) for s in b["series"]], fmt=fmt,
                                   title=b.get("title", ""))
    if kind == "scatter":
        return charts.scatter([tuple(p) for p in b["points"]],
                              xlab=b.get("xlab", ""), ylab=b.get("ylab", ""),
                              title=b.get("title", ""))
    if kind == "share":
        return charts.share_bars([tuple(r) for r in b["rows"]], title=b.get("title", ""),
                                 base_label=b.get("base_label", ""))
    if kind == "quadrant":
        return charts.quadrant([tuple(p) for p in b["points"]], xlab=b.get("xlab", ""),
                               ylab=b.get("ylab", ""), unit=b.get("unit", "%"),
                               title=b.get("title", ""))
    if kind == "paired":
        unit = b.get('unit', '')
        return charts.paired([(r[0], r[1]) for r in b["rows"]], [tuple(x) for x in b["series"]],
                             title=b.get("title", ""), fmt=lambda v: f'{v:,.2f}'.rstrip('0').rstrip('.') + unit)
    if kind == "mix":
        return charts.stacked_bar([tuple(x) for x in b["parts"]], title=b.get("title", ""))
    raise ValueError(f"unknown chart kind: {kind}")


def block(b):
    t = b["type"]
    if t == "p":
        return f'<p>{b["html"]}</p>'
    if t == "claim":
        return f'<p class="claim">{b["html"]}</p>'
    if t == "list":
        return "<ul>" + "".join(f"<li>{i}</li>" for i in b["items"]) + "</ul>"
    if t == "cards":
        return '<div class="grid">' + "".join(
            f'<div class="card"><h3>{c["h"]}</h3><p>{c["p"]}</p></div>' for c in b["items"]) + "</div>"
    if t == "callout":
        ps = "".join(f"<p>{p}</p>" for p in b["p"])
        return f'<div class="callout"><h3>{b["h"]}</h3>{ps}</div>'
    if t == "box":
        ps = "".join(f"<p>{p}</p>" for p in b.get("p", []))
        return f'<div class="box"><h3 style="margin-top:0">{b.get("h","")}</h3>{ps}</div>'
    if t == "h3":
        return f'<h3>{b["text"]}</h3>'
    if t == "headline":                      # the finding itself, set large
        return f'<p class="headline">{b["html"]}</p>'
    if t == "sub":                           # the explanation under a headline, a size down
        return f'<p class="sub">{b["html"]}</p>'
    if t == "so_what":                       # what to do about it
        return f'<p class="sowhat"><span>行动</span>{b["html"]}</p>' if b.get("lang") != "en" \
               else f'<p class="sowhat"><span>So what</span>{b["html"]}</p>'
    if t == "fine":                          # method, caveats, sample size
        return f'<p class="fine">{b["html"]}</p>'
    if t == "takeaways":
        items = "".join(
            f'<li><span class="num">{i["n"]}</span><div><b>{i["h"]}</b>'
            + (f'<p>{i["p"]}</p>' if i.get("p") else "") + "</div></li>"
            for i in b["items"])
        return f'<ol class="takeaways">{items}</ol>'
    if t == "details":
        inner = "".join(block(x) for x in b["blocks"])
        return f'<details><summary>{b["summary"]}</summary><div class="det">{inner}</div></details>'
    if t == "table":
        return table(b)
    if t == "chart":
        return chart(b)
    raise ValueError(f"unknown block type: {t}")


def render(doc, standalone=False):
    for s in doc['sections']:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', s['id']): raise ValueError('Invalid section ID')
        if not re.fullmatch(r'[A-Za-z0-9 _-]*', s.get('class', '')): raise ValueError('Invalid class')
    if len({s['id'] for s in doc['sections']}) != len(doc['sections']): raise ValueError('Duplicate section IDs')
    if not re.fullmatch(r'[A-Za-z-]+', doc.get('lang', 'en')): raise ValueError('Invalid language')
    doc = safe_doc(doc)
    css = Path(HERE, 'report.css').read_text(encoding='utf-8')
    secs = doc["sections"]
    nav = "".join(f'<li><a href="#{s["id"]}">{s["title"]}</a></li>' for s in secs)
    body = "".join(
        f'<section id="{s["id"]}" class="{s.get("class","")}">'
        + (f'<span class="kicker">{s["kicker"]}</span>' if s.get("kicker") else "")
        + f'<h2>{s["title"]}</h2>'
        + "".join(block(b) for b in s["blocks"])
        + "</section>" for s in secs)
    facts = "".join(f'<span class="fact">{k} <b>{v}</b></span>' for k, v in doc.get("facts", []))
    foot = "".join(f"<p>{p}</p>" for p in doc.get("footer", []))
    fonts = ''  # Offline by default; use system fonts, no external requests.
    page = f"""<title>{doc['title']}</title>
{fonts}
<style>{css}</style>
<div class="wrap">
<header class="hero">
  {f'<p class="eyebrow">{doc["eyebrow"]}</p>' if doc.get('eyebrow') else ''}
  <h1>{doc['title']}</h1>
  {f'<p class="lede">{doc["subtitle"]}</p>' if doc.get('subtitle') else ''}
  <div class="facts">{facts}</div>
</header>
<nav class="toc" aria-label="sections"><ol>{nav}</ol></nav>
{body}
<footer>{foot}</footer>
</div>"""
    if standalone:
        head, rest = page.split('<div class="wrap">', 1)
        page = ('<!doctype html><html lang="%s"><head><meta charset="utf-8">'
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">%s</head>'
                '<body><div class="wrap">%s</body></html>' % (doc.get("lang", "en"), head, rest))
    return page


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("\n用法：python3 render_report.py report.json out.html [--standalone]")
    raise SystemExit(2)

if __name__ == "__main__":
    if len([a for a in sys.argv[1:] if not a.startswith("--")]) < 2:
        _usage()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    standalone = "--standalone" in sys.argv
    src, out = args[0], args[1]
    doc = json.load(open(src, encoding="utf-8"))
    html = render(doc, standalone)
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out} ({len(html)/1024:.0f} KB, {len(doc['sections'])} sections)")
