#!/usr/bin/env python3
"""Rebuild the numerical example from bundled source data, without strategy claims."""
import argparse
import json
from pathlib import Path
from html import escape
from grid_stats import account_stats


def build():
    source = Path(__file__).resolve().parents[1] / 'examples/synthetic-accounts.jsonl'
    records = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    if not records or any(r.get("synthetic") is not True or not r.get("handle", "").startswith("fictional_demo_") or r.get("source_url") for r in records):
        raise ValueError("Bundled demo requires explicitly synthetic fixtures without source URLs")
    stats = [account_stats(r) for r in records]
    def show(v): return 'unknown' if v is None else f'{v:,.2f}'.rstrip('0').rstrip('.')
    rows = []
    for r in stats:
        rows.append([escape(r['handle']),
                     r['n'], '/'.join(map(str, r['segment_n'])), show(r['median_views']),
                     show(r['recent']), show(r['oldest']), show(r['recent_over_oldest']),
                     r['window_days']])
    return {'title': 'Account Launch Research — synthetic demo', 'lang': 'en',
            'eyebrow': 'Synthetic demonstration · no real accounts',
            'subtitle': 'All accounts, dates and metrics are fictional. This example demonstrates calculation and layout only.',
            'facts': [['Accounts', len(stats)], ['Window', 'Up to 36 posts'], ['Data', 'Entirely synthetic']],
            'sections': [
                {'id': 'limits', 'title': 'Read the limits first', 'blocks': [
                    {'type': 'callout', 'h': 'Source and scope', 'p': [
                        'Four fictional accounts are constructed with simple arithmetic values. No third-party account data is bundled.',
                        'Names are demo labels, not social handles. Dates are explicit fictional dates. There are no source URLs or real post IDs.',
                        'Do not use these invented numbers as evidence for any platform, account positioning or content strategy.']} ]},
                {'id': 'level', 'title': 'Median views in the supplied windows', 'blocks': [
                    {'type': 'chart', 'kind': 'bars', 'title': 'Snapshot median views',
                     'rows': [[r['handle'], [r['median_views']]] for r in stats],
                     'series': [['Median views', '--accent']]},
                    {'type': 'fine', 'html': 'Values are recalculated, not copied from an earlier narrative. No group comparison is asserted.'}]},
                {'id': 'table', 'title': 'Calculated inputs for review', 'class': 'appendix', 'blocks': [
                    {'type': 'table', 'head': ['Profile', 'N', 'Segment N', 'Median', 'Recent', 'Oldest', 'Recent/oldest', 'Days'], 'rows': rows},
                    {'type': 'details', 'summary': 'Reproduce this example', 'blocks': [
                        {'type': 'p', 'html': '<code>python3 scripts/build_example.py /tmp/report.json</code> then <code>python3 scripts/render_report.py /tmp/report.json /tmp/demo.html --standalone</code>, from the installed skill directory.'}]}]}],
            'footer': ['Synthetic fixture only. All values and labels are fictional, with no third-party account links.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out')
    a = p.parse_args()
    Path(a.out).write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding='utf-8')
