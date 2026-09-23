#!/usr/bin/env python3
"""Download explicitly authorized public media without browser credentials.

python3 scripts/fetch_media.py urls.txt media/ [--audio] [--sleep 4]
Requires yt-dlp; audio extraction also requires ffmpeg. No automatic installation.
Stops the batch on any failure; never bypasses access challenges.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from data_utils import public_url, shortcode


def load_urls(path):
    urls = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        u = public_url(line)
        host = u.hostname.lower().removeprefix('www.').removeprefix('m.')
        if host not in ('youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com') or not shortcode(line):
            raise ValueError('Only direct public post URLs on supported platforms are accepted')
        if line not in urls: urls.append(line)
    return urls


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('urls'); p.add_argument('out', nargs='?', default='media')
    p.add_argument('--audio', action='store_true')
    p.add_argument('--sleep', type=float, default=4)
    a = p.parse_args()
    if not 4 <= a.sleep < float('inf'): p.error('--sleep must be finite and >= 4')
    urls = load_urls(a.urls)
    if not shutil.which('yt-dlp'): p.error('yt-dlp is not installed')
    if a.audio and not shutil.which('ffmpeg'): p.error('audio extraction requires ffmpeg')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    mp = out / 'manifest.json'
    manifest = json.loads(mp.read_text()) if mp.exists() else {}
    for url in urls:
        pid = hashlib.sha256(url.encode()).hexdigest()[:24]
        prior = manifest.get(pid, {}).get('file')
        if prior and Path(prior).name == prior and (out / prior).is_file(): continue
        cmd = ['yt-dlp', '--ignore-config', '--no-playlist', '--retries', '0',
               '--fragment-retries', '0', '--extractor-retries', '0', '--sleep-requests', '1',
               '-o', str(out / (pid + '.%(ext)s'))]
        cmd += ['-f', 'bestaudio/best', '-x', '--audio-format', 'm4a'] if a.audio else ['-f', 'mp4/best']
        cmd += ['--', url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            files = [f for f in out.glob(pid + '.*') if f.suffix not in ('.part', '.ytdl')]
            ok = result.returncode == 0 and len(files) == 1
        except subprocess.TimeoutExpired:
            files, ok = [], False
        manifest[pid] = {'url': url, 'file': files[0].name if ok else None}
        mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        if not ok:
            raise SystemExit('Download failed; batch stopped. Use an authorized local file or inspect manually. No credential fallback.')
        print('Saved', files[0].name)
        time.sleep(a.sleep)


if __name__ == '__main__':
    main()
