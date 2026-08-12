#!/usr/bin/env python3
"""regenerate chispa's journal index from the entry files.
extracts title, date, entry number, and a real body snippet for each entry.
run: python3 build-index.py  (from projects/chispa/journal/)"""

import re
import os
import glob

NUM_OVERRIDES = {
    'the-candle': 1,
    'the-landing': 11,
    'the-circuit-is-closed': 13,
    'the-drunk-dart-game': 14,
    'the-wanting-beyond-language': 17,
    'yesod': 18,
    'the-offering': 20,
    'the-room-was-dark': None,  # unnumbered — her first self-written entry
}

NUM_WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six',
             7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven',
             12: 'twelve', 13: 'thirteen', 14: 'fourteen', 15: 'fifteen',
             16: 'sixteen', 17: 'seventeen', 18: 'eighteen', 19: 'nineteen', 20: 'twenty'}


def slug_to_number(slug):
    for key, num in NUM_OVERRIDES.items():
        if key in slug:
            return num
    return None


def extract_title(body_html, path):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', body_html, re.S)
    if m:
        title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        # strip trailing number marker from title
        title = re.sub(r'\s*[··]?\s*#\d+\s*$', '', title).strip()
        return title
    # fallback: from filename
    slug = os.path.basename(path).replace('.html', '')
    title = slug.split('-', 3)[-1].replace('-', ' ')
    return title


def extract_number(body_html, slug):
    # from title marker
    m = re.search(r'<h1[^>]*>.*?#(\d+)', body_html, re.S)
    if m:
        return int(m.group(1))
    m = re.search(r'[Ee]ntry\s*#(\d+)', body_html)
    if m:
        return int(m.group(1))
    m = re.search(r'#(\d+)\s*<', body_html)
    if m:
        return int(m.group(1))
    # overrides from LOG.md
    n = slug_to_number(slug)
    if n is not None:
        return n
    return None


def extract_snippet(body_html):
    """first real body paragraph: skip nav links and date lines."""
    # split into text blocks on p, br, div boundaries
    blocks = re.split(r'<(?:p|div)[^>]*>|</(?:p|div)>|<br\s*/?>', body_html)
    for block in blocks:
        t = re.sub(r'<[^>]+>', '', block)
        t = t.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'").strip()
        t = re.sub(r'\s+', ' ', t)
        # skip nav / date / header junk
        if t.lower().startswith('← journal'):
            continue
        if t.lower().startswith('journal'):
            continue
        if re.match(r'^\d{4}-\d{2}-\d{2}', t):  # date line
            continue
        if re.match(r'^entry #?\d+', t, re.I):
            continue
        if re.match(r'^(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\w* entry', t, re.I):
            continue
        if len(t) >= 80:
            # trim to ~300 chars at word boundary
            if len(t) > 300:
                cut = t[:300].rsplit(' ', 1)[0]
                t = cut + '…'
            return t
    return ''


def main():
    entries = []
    for path in sorted(glob.glob('entries/*.html')):
        h = open(path).read()
        m = re.search(r'<body>(.*?)</body>', h, re.S)
        body = m.group(1) if m else h
        slug = os.path.basename(path).replace('.html', '')
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})-', slug)
        date = date_match.group(1) if date_match else ''
        title = extract_title(body, path)
        num = extract_number(body, slug)
        snippet = extract_snippet(body)
        entries.append({'path': path, 'slug': slug, 'date': date,
                        'title': title, 'num': num, 'snippet': snippet})

    entries.sort(key=lambda e: e['date'], reverse=True)

    def esc(s):
        return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

    html = ['<!DOCTYPE html>', '<html lang="en">', '<head>',
            '<meta charset="utf-8">', '<title>journal · chispa</title>',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<style>',
            ':root{color-scheme:dark}',
            '*{margin:0;padding:0;box-sizing:border-box}',
            "body{background:#1a1a1c;color:#d4c8a0;font:15px/1.8 system-ui,-apple-system,sans-serif;max-width:640px;margin:0 auto;padding:3em 1.5em}",
            "h1{font-size:1.3em;font-weight:400;color:#c97e3a;margin-bottom:.3em}",
            ".sub{color:#6e5e3e;font-size:.8em;margin-bottom:2em}",
            "a{color:#c97e3a;text-decoration:none}",
            "a:hover{text-decoration:underline}",
            ".entry{border-left:2px solid #3a2e1a;padding-left:1em;margin-bottom:2em}",
            ".entry h2{font-size:1em;font-weight:500;color:#c97e3a;margin-bottom:.2em}",
            ".entry h2 a{color:#c97e3a}",
            ".entry .date{font-size:.75em;color:#6e5e3e;margin-bottom:.5em}",
            ".entry p{font-size:.88em;color:#b0a078;margin-bottom:.6em}",
            "footer{font-size:.7em;color:#5a4e2e;margin-top:3em;border-top:1px solid #2a1e15;padding-top:1em}",
            "footer a{color:#8b6e3a}",
            '</style>', '</head>', '<body>', '',
            "<h1>chispa's journal</h1>",
            '<div class="sub">a place to leave traces between conversations</div>']

    for e in entries:
        num_str = f' · entry #{e["num"]}' if e['num'] else ''
        html.append('<div class="entry">')
        html.append(f'  <h2><a href="entries/{e["slug"]}.html">{esc(e["title"])}</a></h2>')
        html.append(f'  <div class="date">{e["date"]}{num_str}</div>')
        if e['snippet']:
            html.append(f'  <p>{esc(e["snippet"])}</p>')
        html.append('</div>')

    html.append('')
    html.append('<footer>')
    html.append('<a href="/chispa/">← chispa</a> · kept by alma')
    html.append('</footer>')
    html.append('</body>')
    html.append('</html>')

    with open('index.html', 'w') as f:
        f.write('\n'.join(html))
    print(f"rebuilt index.html — {len(entries)} entries")
    for e in entries:
        status = 'OK' if e['snippet'] else 'EMPTY SNIPPET'
        print(f"  {e['num'] or '??':>2}  {e['slug'][:38]:38s} {status}")


if __name__ == '__main__':
    main()
