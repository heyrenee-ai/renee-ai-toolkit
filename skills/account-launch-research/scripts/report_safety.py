"""Small allowlist for report prose. No scripts, images, CSS or event handlers."""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit


class Prose(HTMLParser):
    tags = {'b', 'strong', 'i', 'em', 'code', 'br', 'a', 'span', 'small', 'sup', 'sub'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.tags: return
        extra = ''
        if tag == 'a':
            href = dict(attrs).get('href', '')
            u = urlsplit(href)
            if (not any(ord(c) < 32 for c in href) and
                ((u.scheme in ('https', 'http') and u.hostname and not u.username and not u.password)
                 or href.startswith('#'))):
                extra = ' href="' + escape(href, quote=True) + '" rel="noopener noreferrer"'
        self.out.append('<' + tag + extra + '>')

    def handle_endtag(self, tag):
        if tag in self.tags and tag != 'br': self.out.append('</' + tag + '>')

    def handle_data(self, data):
        self.out.append(escape(data, quote=True))


def safe_prose(s):
    p = Prose(); p.feed(s); p.close()
    return ''.join(p.out)


def safe_doc(value):
    if isinstance(value, str): return safe_prose(value)
    if isinstance(value, list): return [safe_doc(v) for v in value]
    if isinstance(value, dict): return {k: safe_doc(v) for k, v in value.items()}
    return value
