"""Shared strict parsing and spreadsheet-safe CSV output (standard library)."""
import math
import re
from datetime import date
from urllib.parse import urlsplit, parse_qs


def number(value):
    if value is None or str(value).strip().lower() in ('', '-', 'n/a', 'null', 'none'):
        return None
    s = str(value).strip().replace(',', '')
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([kKmMbB]?)', s)
    if not m:
        raise ValueError('Expected a non-negative finite number: ' + repr(value))
    n = float(m[1]) * {'': 1, 'k': 1e3, 'm': 1e6, 'b': 1e9}[m[2].lower()]
    if not math.isfinite(n):
        raise ValueError('Non-finite number')
    return n


def iso_date(value):
    if not value:
        return None
    s = str(value).strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:[T ].*)?', s):
        raise ValueError('Use ISO date YYYY-MM-DD: ' + repr(value))
    return date.fromisoformat(s[:10]).isoformat()


def public_url(value):
    u = urlsplit(value or '')
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password:
        raise ValueError('Expected public HTTP(S) URL without credentials')
    return u


def shortcode(url):
    if not url:
        return None
    u = public_url(url)
    host = u.hostname.lower().removeprefix('www.').removeprefix('m.')
    patterns = {'instagram.com': r'/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)',
                'tiktok.com': r'/@[^/]+/(?:video|photo)/(\d+)',
                'youtube.com': r'/(?:shorts|embed)/([A-Za-z0-9_-]{11})(?:/|$)',
                'youtu.be': r'/([A-Za-z0-9_-]{11})(?:/|$)'}
    m = re.match(patterns.get(host, r'(?!)'), u.path)
    if m:
        return m[1]
    if host == 'youtube.com' and u.path == '/watch':
        v = parse_qs(u.query).get('v', [''])[0]
        return v if re.fullmatch(r'[A-Za-z0-9_-]{11}', v) else None
    return None


def csv_safe(row):
    # Preserve numeric cells; mark potentially executable text as literal text.
    return {k: "'" + v if isinstance(v, str) and
            (v.lstrip().startswith(('=', '+', '-', '@')) or v.startswith(('\t', '\r', '\n')))
            else v for k, v in row.items()}
