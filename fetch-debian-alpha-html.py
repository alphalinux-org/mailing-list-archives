#!/usr/bin/env python3
"""Scrape missing debian-alpha months from lists.debian.org.

Covers: 1995-11 – 1998-12 and 2001-10 – 2002-02
(1999-01 – 2001-09 covered by local HTML; 2002-03+ covered by Gmane)
"""

import re
import html as html_mod
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

BASE_URL = 'https://lists.debian.org/debian-alpha'
MBOX_DIR = Path(__file__).parent / 'debian-alpha-mbox'

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

# Months we need: before 1999-01, after 2001-09 and before 2002-03
# Build from the live index so we only request months that exist.
NEED = set()
for y in range(1995, 1999):
    for m in range(1, 13):
        NEED.add((y, m))
for m in range(10, 13):
    NEED.add((2001, m))
for m in range(1, 3):
    NEED.add((2002, m))


META_RE = re.compile(
    r'<!--\s*received="([^"]*)"[^>]*-->'
    r'(?:\s*<!--[^>]*-->)*\s*'
    r'<!--\s*sent="([^"]*)"[^>]*-->'
    r'(?:\s*<!--[^>]*-->)*\s*'
    r'<!--\s*name="([^"]*)"[^>]*-->\s*'
    r'(?:<!--\s*email="([^"]*)"[^>]*-->\s*)?'
    r'<!--\s*subject="([^"]*)"[^>]*-->\s*'
    r'<!--\s*id="([^"]*)"[^>]*-->',
    re.DOTALL,
)
INREPLYTO_RE = re.compile(r'<!--\s*inreplyto="([^"]*)"[^>]*-->')
BODY_RE = re.compile(r'<!--\s*body="start"\s*-->(.*?)<!--\s*body="end"\s*-->', re.DOTALL)
MSGID_RE = re.compile(r'^[^@\s]+@[^@\s]+$')
MSG_LINK_RE = re.compile(r'href="(msg\d+\.html)"', re.IGNORECASE)


def get(url, delay=1.0):
    req = urllib.request.Request(url, headers={'User-Agent': 'debian-alpha-archiver/1.0'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            time.sleep(delay)
            return data.decode('latin-1')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            wait = 5 * (2 ** attempt)
            print(f'    HTTP {e.code}, retry after {wait}s', file=sys.stderr)
            time.sleep(wait)
        except Exception as e:
            wait = 5 * (2 ** attempt)
            print(f'    {e}, retry after {wait}s', file=sys.stderr)
            time.sleep(wait)
    return None


def strip_html(text):
    text = re.sub(r'<br\s*/?>\n?', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p\s*/?>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?pre[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def quote_from_lines(text):
    return '\n'.join('>From ' + l[5:] if l.startswith('From ') else l
                     for l in text.split('\n'))


# --- Old Pipermail format (pre-2000 local files) ---
def parse_msg_old(text):
    m = META_RE.search(text)
    if not m:
        return None
    received, sent, name, email, subject, msgid = [
        x.strip() if x else '' for x in m.groups()
    ]
    inreplyto = None
    im = INREPLYTO_RE.search(text)
    if im:
        irt = im.group(1).strip()
        if MSGID_RE.match(irt):
            inreplyto = irt
    body_m = BODY_RE.search(text)
    if not body_m:
        return None
    body = quote_from_lines(strip_html(body_m.group(1)).strip())
    return dict(received=received, sent=sent, name=name, email=email,
                subject=subject, msgid=msgid, inreplyto=inreplyto, body=body)


# --- New MHonArc X-header format (live site) ---
X_SUBJECT_RE = re.compile(r'<!--X-Subject:\s*(.*?)\s*-->')
X_DATE_RE    = re.compile(r'<!--X-Date:\s*(.*?)\s*-->')
X_MSGID_RE   = re.compile(r'<!--X-Message-Id:\s*(.*?)\s*-->')
HEAD_RE      = re.compile(
    r'<!--X-Head-of-Message-->(.*?)<!--X-Head-of-Message-End-->',
    re.DOTALL,
)
BODY_X_RE    = re.compile(
    r'<!--X-Body-of-Message-->(.*?)<!--X-Body-of-Message-End-->',
    re.DOTALL,
)
FROM_LI_RE   = re.compile(r'<em>From</em>\s*:\s*(.*?)</li>', re.DOTALL | re.IGNORECASE)
IRT_LI_RE    = re.compile(r'<em>In-reply-to</em>\s*:\s*(.*?)</li>', re.DOTALL | re.IGNORECASE)
MAILTO_RE    = re.compile(r'href="mailto:([^"%]+)"')


def parse_msg_new(text):
    sm = X_SUBJECT_RE.search(text)
    dm = X_DATE_RE.search(text)
    im = X_MSGID_RE.search(text)
    if not (sm and dm):
        return None

    subject = html_mod.unescape(sm.group(1).strip())
    date_str = html_mod.unescape(dm.group(1).strip())
    msgid = html_mod.unescape(im.group(1).strip()) if im else ''

    head_m = HEAD_RE.search(text)
    name = email = ''
    inreplyto = None
    if head_m:
        head = head_m.group(1)
        fm = FROM_LI_RE.search(head)
        if fm:
            from_raw = fm.group(1)
            ml = MAILTO_RE.search(from_raw)
            if ml:
                email = urllib.parse.unquote(ml.group(1))
            name = strip_html(from_raw).strip().split('<')[0].strip()
        irt_m = IRT_LI_RE.search(head)
        if irt_m:
            irt_raw = strip_html(irt_m.group(1)).strip()
            irt_raw = irt_raw.strip('<>').strip()
            if MSGID_RE.match(irt_raw):
                inreplyto = irt_raw

    body_m = BODY_X_RE.search(text)
    if not body_m:
        return None
    body = quote_from_lines(strip_html(body_m.group(1)).strip())

    return dict(received=date_str, sent=date_str, name=name, email=email,
                subject=subject, msgid=msgid, inreplyto=inreplyto, body=body)


def parse_msg(text):
    # Try old format first, then new X-header format
    result = parse_msg_old(text)
    if result is None:
        result = parse_msg_new(text)
    return result


def make_entry(msg):
    from_addr = msg['email'] or 'unknown'
    lines = [f"From {from_addr} {msg['received'].strip()}"]
    if msg['msgid']:
        lines.append(f"Message-ID: <{msg['msgid']}>")
    if msg['sent']:
        lines.append(f"Date: {msg['sent']}")
    from_hdr = msg['name']
    if msg['email']:
        from_hdr += (f" <{msg['email']}>" if msg['name'] else msg['email'])
    lines.append(f"From: {from_hdr}")
    lines.append(f"Subject: {msg['subject']}")
    if msg['inreplyto']:
        lines.append(f"In-Reply-To: <{msg['inreplyto']}>")
    lines += ['', msg['body'], '']
    return '\n'.join(lines)


def fetch_month(year, month):
    stem = f'{year}-{MONTH_NAMES[month]}'
    out_path = MBOX_DIR / f'{stem}.mbox'
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f'  skip {stem} (exists)')
        return

    # Try new-style URL first, then old-style
    dir_url = f'{BASE_URL}/{year}/{month:02d}'
    index_html = get(f'{dir_url}/maillist.html')
    if index_html is None:
        dir_url = f'{BASE_URL}/{year}/debian-alpha-{year}{month:02d}'
        index_html = get(f'{dir_url}/maillist.html')
    if index_html is None:
        print(f'  {stem}: not found')
        return

    # Dedupe preserving order
    msg_files = list(dict.fromkeys(MSG_LINK_RE.findall(index_html)))
    print(f'  {stem}: {len(msg_files)} messages...', end=' ', flush=True)

    entries = []
    for mf in msg_files:
        text = get(f'{dir_url}/{mf}', delay=0.5)
        if text is None:
            continue
        msg = parse_msg(text)
        if msg is None:
            print(f'(SKIP {mf})', end=' ', flush=True)
            continue
        entries.append(make_entry(msg))

    with out_path.open('w', encoding='utf-8') as f:
        for e in entries:
            f.write(e)
            f.write('\n')

    print(f'{len(entries)} written')


def get_available_months():
    """Fetch index and return set of (year, month) tuples available online."""
    index = get(f'{BASE_URL}/')
    if not index:
        return set()
    pairs = set()
    for m in re.finditer(r'href="(\d{4})/[^"]*threads\.html"', index):
        year = int(m.group(1))
        # extract month from the dir name or URL path
        dm = re.search(r'(\d{4})/(?:debian-alpha-\d{4}(\d{2})|(\d{2}))/threads\.html',
                       m.group(0))
        if dm:
            mon = int(dm.group(2) or dm.group(3))
            pairs.add((year, mon))
    return pairs


def main():
    MBOX_DIR.mkdir(exist_ok=True)
    available = get_available_months()
    targets = sorted(NEED & available)
    missing_from_site = NEED - available
    if missing_from_site:
        print(f'Not on site: {sorted(missing_from_site)}')

    print(f'{len(targets)} months to fetch')
    for year, month in targets:
        fetch_month(year, month)

    print('Done.')


if __name__ == '__main__':
    main()
