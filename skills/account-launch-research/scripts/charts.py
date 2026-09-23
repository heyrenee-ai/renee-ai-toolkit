# -*- coding: utf-8 -*-
"""Small dependency-free SVG chart helpers for the research report renderer."""
from html import escape

def _fmt(n):
    return f"{n:,.0f}" if n >= 100 else (f"{n:g}")

def grouped_bars(rows, series, width=760, row_h=34, label_w=150, pad_r=58,
                 fmt=lambda v: f"{v:g}", title=""):
    """rows: [(label, [v1, v2, ...])]; series: [(name, cssvar)]"""
    h_head = 26
    height = h_head + len(rows) * row_h + 8
    plot_w = width - label_w - pad_r
    vmax = max(max(vs) for _, vs in rows) or 1
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    # legend
    lx = label_w
    for name, var in series:
        out.append(f'<rect x="{lx}" y="6" width="10" height="10" rx="2" fill="var({var})"/>')
        out.append(f'<text x="{lx+15}" y="15" class="lg">{escape(name)}</text>')
        lx += 22 + len(name) * 12
    k = len(series)
    bh = min(9, (row_h - 10) / k)
    for i, (label, vs) in enumerate(rows):
        y0 = h_head + i * row_h
        out.append(f'<text x="0" y="{y0 + row_h/2 + 4:.0f}" class="ax">{escape(label)}</text>')
        for j, v in enumerate(vs):
            w = plot_w * (v / vmax)
            y = y0 + (row_h - k * bh - (k - 1) * 2) / 2 + j * (bh + 2)
            out.append(f'<rect x="{label_w}" y="{y:.1f}" width="{w:.1f}" height="{bh:.1f}" rx="1.5" fill="var({series[j][1]})"/>')
            out.append(f'<text x="{label_w + max(w,1) + 5:.1f}" y="{y + bh - 0.5:.1f}" class="vl">{escape(fmt(v))}</text>')
    out.append('</svg>')
    return "\n".join(out)

def lift_chart(rows, width=760, row_h=40, label_w=150, pad_r=96, title=""):
    """rows: [(label, before, after, lift_text)] — log-ish paired dots with a connector."""
    import math
    height = 24 + len(rows) * row_h + 8
    plot_w = width - label_w - pad_r
    vals = [v for _, b, a, _ in rows for v in (b, a)]
    lo, hi = min(vals), max(vals)
    lg = lambda v: (math.log1p(v) - math.log1p(lo)) / (math.log1p(hi) - math.log1p(lo) or 1) * plot_w + label_w
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    out.append(f'<text x="{label_w}" y="14" class="lg">破圈前中位播放</text>'
               f'<text x="{label_w+120}" y="14" class="lg">→ 破圈后中位播放</text>')
    for i, (label, b, a, lift) in enumerate(rows):
        y = 24 + i * row_h + row_h / 2
        x1, x2 = lg(b), lg(a)
        out.append(f'<text x="0" y="{y+4:.0f}" class="ax">{escape(label)}</text>')
        out.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="var(--line-2)" stroke-width="2"/>')
        out.append(f'<circle cx="{x1:.1f}" cy="{y:.1f}" r="4.5" fill="var(--muted)"/>')
        out.append(f'<circle cx="{x2:.1f}" cy="{y:.1f}" r="5.5" fill="var(--accent)"/>')
        out.append(f'<text x="{x1:.1f}" y="{y-9:.1f}" class="vl" text-anchor="middle">{_fmt(b)}</text>')
        out.append(f'<text x="{x2:.1f}" y="{y-9:.1f}" class="vl" text-anchor="middle">{_fmt(a)}</text>')
        out.append(f'<text x="{width-pad_r+10}" y="{y+4:.0f}" class="lift">{escape(lift)}</text>')
    out.append('</svg>')
    return "\n".join(out)

def scatter(points, width=760, height=320, pad=58, xlab="", ylab="", title=""):
    """points: [(x, y, label, flag)] — labels are nudged apart when dots collide."""
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    def nice(v, n=4):
        import math
        step = (v or 1) / n
        mag = 10 ** math.floor(math.log10(step))
        for m in (1, 2, 2.5, 5, 10):
            if step <= m * mag:
                return m * mag
        return 10 * mag
    xstep = nice(max(xs) * 1.12); ystep = nice(max(ys) * 1.15)
    xmax = xstep * 4; ymax = ystep * 4
    px = lambda v: pad + (v / xmax) * (width - pad - 26)
    py = lambda v: height - pad + 6 - (v / ymax) * (height - pad - 22)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    for t in range(5):
        y = py(ystep * t)
        out.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{width-16}" y2="{y:.1f}" stroke="var(--line)" stroke-width="1"/>')
        out.append(f'<text x="{pad-8}" y="{y+4:.1f}" class="ax" text-anchor="end">{_fmt(ystep*t)}</text>')
        x = px(xstep * t)
        out.append(f'<text x="{x:.1f}" y="{height-pad+26:.1f}" class="ax" text-anchor="middle">{_fmt(xstep*t)}</text>')
    placed = []
    for x, y, label, flag in sorted(points, key=lambda p: -p[1]):
        cx, cy = px(x), py(y)
        fill = "var(--warn)" if flag else "var(--accent)"
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{fill}" fill-opacity="0.85"/>')
        anchor = "end" if cx > width - 130 else "start"
        dx = -16 if anchor == "end" else 16
        ly = cy + 4
        while any(abs(ly - q[1]) < 15 and abs(cx + dx - q[0]) < 120 for q in placed):
            ly += 15
        placed.append((cx + dx, ly))
        out.append(f'<text x="{cx+dx:.1f}" y="{ly:.1f}" class="vl" text-anchor="{anchor}">{escape(label)}</text>')
    out.append(f'<text x="{(width+pad)/2:.0f}" y="{height-8}" class="ax" text-anchor="middle">{escape(xlab)}</text>')
    out.append(f'<text x="8" y="16" class="ax">{escape(ylab)}</text>')
    out.append('</svg>')
    return "\n".join(out)


def share_bars(rows, width=760, row_h=46, label_w=150, pad_r=20, title="",
               base_label="", note_fmt="{:.0%}"):
    """One bar per row, drawn as a share of a 100% reference track.

    rows: [(label, share_0_to_1, right_caption)] — reads as "B reaches N% of A",
    which is what a ratio like 8.7x actually means to a reader.
    """
    height = 22 + len(rows) * row_h + 6
    track = width - label_w - pad_r - 96
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    if base_label:
        out.append(f'<text x="{label_w}" y="12" class="lg">{escape(base_label)}</text>')
    for i, (label, share, caption) in enumerate(rows):
        y = 22 + i * row_h
        out.append(f'<text x="0" y="{y + 20:.0f}" class="ax">{escape(label)}</text>')
        out.append(f'<rect x="{label_w}" y="{y + 6:.0f}" width="{track}" height="18" rx="2" '
                   f'fill="var(--line)"/>')
        w = track * share
        out.append(f'<rect x="{label_w}" y="{y + 6:.0f}" width="{w:.1f}" height="18" rx="2" '
                   f'fill="var(--accent)"/>')
        out.append(f'<text x="{label_w + track + 12}" y="{y + 20:.0f}" class="vl">{escape(caption)}</text>')
    out.append('</svg>')
    return "\n".join(out)


def quadrant(points, width=760, height=430, pad=64, xlab="", ylab="", title="",
             unit="%", diagonal=True):
    """Two platforms on two axes; the diagonal is "does equally well on both".

    points: [(x, y, label, emphasis)] — emphasis 1 draws the point in the warn colour.
    Off-diagonal points are the whole story: they are platform-bound topics.
    """
    xs = [p[0] for p in points] + [0]; ys = [p[1] for p in points] + [0]
    hi = max(max(xs), max(ys), 1) * 1.18
    step = 10 if hi <= 45 else 20
    px = lambda v: pad + (v / hi) * (width - pad - 26)
    py = lambda v: height - pad - (v / hi) * (height - pad - 26)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    t = 0
    while t <= hi:
        out.append(f'<line x1="{px(t):.1f}" y1="{py(0):.1f}" x2="{px(t):.1f}" y2="{py(hi):.1f}" stroke="var(--line)"/>')
        out.append(f'<line x1="{px(0):.1f}" y1="{py(t):.1f}" x2="{px(hi):.1f}" y2="{py(t):.1f}" stroke="var(--line)"/>')
        out.append(f'<text x="{px(t):.1f}" y="{py(0)+20:.1f}" class="ax" text-anchor="middle">{t:g}{unit}</text>')
        out.append(f'<text x="{pad-10}" y="{py(t)+4:.1f}" class="ax" text-anchor="end">{t:g}{unit}</text>')
        t += step
    if diagonal:
        out.append(f'<line x1="{px(0):.1f}" y1="{py(0):.1f}" x2="{px(hi):.1f}" y2="{py(hi):.1f}" '
                   f'stroke="var(--line-2)" stroke-width="1.5" stroke-dasharray="5 4"/>')
    placed = []
    for x, y, label, emph in points:
        cx, cy = px(x), py(y)
        fill = "var(--warn)" if emph else "var(--accent)"
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{8 if emph else 6}" fill="{fill}" fill-opacity="0.9"/>')
        ly, anchor, dx = cy - 14, "middle", 0
        if cx > width - 150:
            anchor, dx, ly = "end", -14, cy + 4
        while any(abs(ly - q[1]) < 17 and abs(cx + dx - q[0]) < 115 for q in placed):
            ly -= 17
        placed.append((cx + dx, ly))
        cls = "vl em" if emph else "vl"
        out.append(f'<text x="{cx+dx:.1f}" y="{ly:.1f}" class="{cls}" text-anchor="{anchor}">{escape(label)}</text>')
    out.append(f'<text x="{(width+pad)/2:.0f}" y="{height-10}" class="ax" text-anchor="middle">{escape(xlab)}</text>')
    out.append(f'<text x="6" y="16" class="ax">{escape(ylab)}</text>')
    out.append('</svg>')
    return "\n".join(out)


def paired(rows, series, width=760, row_h=54, label_w=110, title="", fmt=lambda v: f"{v:,.2f}".rstrip('0').rstrip('.')):
    """Two values per row, drawn as two dots on one track — a slope you can read at a glance.

    rows: [(label, [a, b])]; series: [(name, cssvar), (name, cssvar)]
    """
    height = 26 + len(rows) * row_h
    track = width - label_w - 130
    vals = [v for _, vs in rows for v in vs]
    lo, hi = min(vals) * 0.9, max(vals) * 1.08
    pos = lambda v: label_w + (v - lo) / (hi - lo or 1) * track
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    lx = label_w
    for name, var in series:
        out.append(f'<circle cx="{lx+5}" cy="12" r="5" fill="var({var})"/>')
        out.append(f'<text x="{lx+15}" y="16" class="lg">{escape(name)}</text>')
        lx += 30 + len(name) * 13
    for i, (label, vs) in enumerate(rows):
        y = 26 + i * row_h + row_h / 2 - 6
        out.append(f'<text x="0" y="{y+4:.0f}" class="ax">{escape(label)}</text>')
        out.append(f'<line x1="{pos(vs[0]):.1f}" y1="{y:.1f}" x2="{pos(vs[1]):.1f}" y2="{y:.1f}" '
                   f'stroke="var(--line-2)" stroke-width="2"/>')
        for v, (_, var) in zip(vs, series):
            out.append(f'<circle cx="{pos(v):.1f}" cy="{y:.1f}" r="7" fill="var({var})"/>')
            out.append(f'<text x="{pos(v):.1f}" y="{y-13:.1f}" class="vl" text-anchor="middle">{escape(fmt(v))}</text>')
    out.append('</svg>')
    return "\n".join(out)


def stacked_bar(parts, width=760, height=96, title=""):
    """parts: [(label, share_0_to_1, cssvar)] — one bar, for a mix or a budget."""
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" class="chart">']
    x = 0
    for label, share, var in parts:
        w = width * share
        out.append(f'<rect x="{x:.1f}" y="26" width="{max(w-3,0):.1f}" height="34" rx="2" fill="var({var})"/>')
        out.append(f'<text x="{x:.1f}" y="18" class="vl em">{escape(f"{share:.0%}")}</text>')
        out.append(f'<text x="{x:.1f}" y="78" class="ax">{escape(label)}</text>')
        x += w
    out.append('</svg>')
    return "\n".join(out)
