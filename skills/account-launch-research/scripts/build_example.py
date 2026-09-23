#!/usr/bin/env python3
"""Rebuild the numerical example from bundled source data, without strategy claims."""
import argparse
import json
from pathlib import Path
from html import escape
from grid_stats import account_stats


def build():
    source = Path(__file__).resolve().parents[1] / 'examples/tiktok-ai-niche.jsonl'
    records = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    stats = [account_stats(r) for r in records]
    def show(v): return 'unknown' if v is None else f'{v:,.2f}'.rstrip('0').rstrip('.')
    rows = []
    for r in stats:
        url = 'https://www.tiktok.com/@' + r['handle']
        rows.append([f'<a href="{escape(url, quote=True)}">{escape(r["handle"])}</a>',
                     r['n'], '/'.join(map(str, r['segment_n'])), show(r['median_views']),
                     show(r['recent']), show(r['oldest']), show(r['recent_over_oldest']),
                     r['window_days']])
    return {'title': 'Account Launch Research — snapshot demo', 'lang': 'en',
            'eyebrow': 'Recomputable example · historical provider-supplied snapshot',
            'subtitle': 'These numbers describe the supplied input only. They do not establish current account performance, a niche trend, or a causal effect.',
            'facts': [['Accounts', len(stats)], ['Window', 'Up to 36 posts'], ['Evidence', 'Unverified capture provenance']],
            'sections': [
                {'id': 'limits', 'title': 'Read the limits first', 'blocks': [
                    {'type': 'callout', 'h': 'Source and scope', 'p': [
                        'The provider described the capture as 2026-09-22. Original screenshots are not included, so capture time, inferred format labels and completeness cannot be independently verified here.',
                        'Some entries have dates only, not post URLs; ID-derived dates are heuristic. K/M values are approximate. Leading pins are removed only where explicitly marked in the input.',
                        'Recent posts have had less time to accumulate views. Windows differ across accounts. Do not infer niche cooling, automation, originality or format causation from this example.']} ]},
                {'id': 'level', 'title': 'Median views in the supplied windows', 'blocks': [
                    {'type': 'chart', 'kind': 'bars', 'title': 'Snapshot median views',
                     'rows': [[r['handle'], [r['median_views']]] for r in stats],
                     'series': [['Median views', '--accent']]},
                    {'type': 'fine', 'html': 'Values are recalculated, not copied from an earlier narrative. No group comparison is asserted.'}]},
                {'id': 'table', 'title': 'Calculated inputs for review', 'class': 'appendix', 'blocks': [
                    {'type': 'table', 'head': ['Profile', 'N', 'Segment N', 'Median', 'Recent', 'Oldest', 'Recent/oldest', 'Days'], 'rows': rows},
                    {'type': 'details', 'summary': 'Reproduce this example', 'blocks': [
                        {'type': 'p', 'html': '<code>python3 scripts/build_example.py /tmp/report.json</code> then <code>python3 scripts/render_report.py /tmp/report.json /tmp/demo.html --standalone</code>, from the installed skill directory.'}]}]}],
            'footer': ['Public metrics are supplied for computational demonstration; linked third-party content retains its own rights.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out')
    a = p.parse_args()
    Path(a.out).write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding='utf-8')
