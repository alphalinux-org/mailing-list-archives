#!/usr/bin/env python3
"""Convert local debian-alpha HTML files to mbox (1999–2001)."""

import re
import os
import html
import sys
from pathlib import Path

BASE = Path(__file__).parent
HTML_BASE = BASE / 'debian-alpha'
MBOX_DIR = BASE / 'debian-alpha-mbox'

MONTH_ORDER = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]
MONTH_IDX = {m: i for i, m in enumerate(MONTH_ORDER)}

META_RE = re.compile(
    r'<!--\s*received="([^"]*)"[^>]*-->'
    r'(?:\s*<!--[^>]*-->)*\s*'           # skip optional comments (isoreceived etc.)
    r'<!--\s*sent="([^"]*)"[^>]*-->'
    r'(?:\s*<!--[^>]*-->)*\s*'
    r'<!--\s*name="([^"]*)"[^>]*-->\s*'
    r'(?:<!--\s*email="([^"]*)"[^>]*-->\s*)?'  # email is sometimes absent
    r'<!--\s*subject="([^"]*)"[^>]*-->\s*'
    r'<!--\s*id="([^"]*)"[^>]*-->',
    re.DOTALL,
)
INREPLYTO_RE = re.compile(r'<!--\s*inreplyto="([^"]*)"[^>]*-->')
BODY_RE = re.compile(r'<!--\s*body="start"\s*-->(.*?)<!--\s*body="end"\s*-->', re.DOTALL)
MSGID_RE = re.compile(r'^[^@\s]+@[^@\s]+$')


def strip_html(text):
    text = re.sub(r'<br\s*/?>\n?', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p\s*/?>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?pre[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def quote_from_lines(text):
    lines = text.split('\n')
    return '\n'.join('>From ' + l[5:] if l.startswith('From ') else l for l in lines)


def parse_html(path):
    try:
        text = path.read_text(encoding='latin-1')
    except Exception as e:
        print(f'  SKIP {path.name}: {e}', file=sys.stderr)
        return None

    m = META_RE.search(text)
    if not m:
        print(f'  SKIP {path.name}: missing metadata', file=sys.stderr)
        return None

    received, sent, name, email, subject, msgid = [x.strip() if x else '' for x in m.groups()]

    inreplyto = None
    im = INREPLYTO_RE.search(text)
    if im:
        irt = im.group(1).strip()
        if MSGID_RE.match(irt):
            inreplyto = irt

    body_m = BODY_RE.search(text)
    if not body_m:
        print(f'  SKIP {path.name}: no body', file=sys.stderr)
        return None

    body = strip_html(body_m.group(1)).strip()
    body = quote_from_lines(body)

    return {
        'received': received, 'sent': sent, 'name': name,
        'email': email, 'subject': subject, 'msgid': msgid,
        'inreplyto': inreplyto, 'body': body,
    }


def make_mbox_entry(msg):
    from_addr = msg['email'] if msg['email'] else 'unknown'
    lines = [f"From {from_addr} {msg['received'].strip()}"]
    if msg['msgid']:
        lines.append(f"Message-ID: <{msg['msgid']}>")
    if msg['sent']:
        lines.append(f"Date: {msg['sent']}")
    from_hdr = msg['name']
    if msg['email']:
        from_hdr += f" <{msg['email']}>" if msg['name'] else msg['email']
    lines.append(f"From: {from_hdr}")
    lines.append(f"Subject: {msg['subject']}")
    if msg['inreplyto']:
        lines.append(f"In-Reply-To: <{msg['inreplyto']}>")
    lines.append('')
    lines.append(msg['body'])
    lines.append('')
    return '\n'.join(lines)


def discover_months():
    """Return sorted list of (year, month_name, dir_path) from HTML_BASE."""
    months = []
    for d in HTML_BASE.iterdir():
        if not d.is_dir():
            continue
        name = d.name
        for month in MONTH_ORDER:
            if name.startswith(month):
                try:
                    year = int(name[len(month):])
                    months.append((year, month, d))
                    break
                except ValueError:
                    pass
    months.sort(key=lambda x: (x[0], MONTH_IDX[x[1]]))
    return months


def convert_month(year, month, month_dir):
    html_files = sorted(month_dir.glob('[0-9]*.html'), key=lambda p: int(p.stem))
    if not html_files:
        print(f'  No HTML files in {month_dir}', file=sys.stderr)
        return 0

    out_path = MBOX_DIR / f'{year}-{month}.mbox'
    count = 0
    with out_path.open('w', encoding='utf-8') as f:
        for hf in html_files:
            msg = parse_html(hf)
            if msg is None:
                continue
            f.write(make_mbox_entry(msg))
            f.write('\n')
            count += 1
    return count


def main():
    MBOX_DIR.mkdir(exist_ok=True)
    months = discover_months()
    total = 0
    for year, month, month_dir in months:
        print(f'{year}-{month}...', end=' ', flush=True)
        n = convert_month(year, month, month_dir)
        print(f'{n} messages')
        total += n
    print(f'\nTotal: {total} messages')


if __name__ == '__main__':
    main()
