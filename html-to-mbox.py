#!/usr/bin/env python3
"""Convert Pipermail HTML files to mbox for axp-list 1995-Nov through 1998-Feb."""

import re
import os
import html
import sys
from pathlib import Path

BASE = Path(__file__).parent
HTML_BASE = BASE / 'axp-list'
MBOX_DIR = BASE / 'axp-list-mbox'

ALL_MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

# Months to convert: 1995-Nov through 1998-Feb
TARGETS = (
    [(1995, m) for m in ('November', 'December')] +
    [(1996, m) for m in ALL_MONTHS] +
    [(1997, m) for m in ALL_MONTHS] +
    [(1998, m) for m in ('January', 'February')]
)

META_RE = re.compile(
    r'<!--\s*received="([^"]*)"[^>]*-->\s*'
    r'<!--\s*sent="([^"]*)"[^>]*-->\s*'
    r'<!--\s*name="([^"]*)"[^>]*-->\s*'
    r'<!--\s*email="([^"]*)"[^>]*-->\s*'
    r'<!--\s*subject="([^"]*)"[^>]*-->\s*'
    r'<!--\s*id="([^"]*)"[^>]*-->',
    re.DOTALL,
)
INREPLYTO_RE = re.compile(r'<!--\s*inreplyto="([^"]*)"[^>]*-->')
BODY_RE = re.compile(r'<!--\s*body="start"\s*-->(.*?)<!--\s*body="end"\s*-->', re.DOTALL)
MSGID_RE = re.compile(r'^[^@\s]+@[^@\s]+$')


def strip_html(text):
    # <br> variants → newline (consume trailing raw newline in HTML source)
    text = re.sub(r'<br\s*/?>\n?', '\n', text, flags=re.IGNORECASE)
    # <p> → blank line
    text = re.sub(r'<p\s*/?>',   '\n\n', text, flags=re.IGNORECASE)
    # strip pre tags but keep content
    text = re.sub(r'</?pre[^>]*>', '', text, flags=re.IGNORECASE)
    # strip all remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # unescape HTML entities
    text = html.unescape(text)
    # collapse runs of 3+ newlines (from <br>\n<p> combos) to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def quote_from_lines(text):
    lines = text.split('\n')
    return '\n'.join('>From ' + l[5:] if l.startswith('From ') else l for l in lines)


def parse_html(path):
    try:
        text = path.read_text(encoding='latin-1')
    except Exception as e:
        print(f'  SKIP {path.name}: read error: {e}', file=sys.stderr)
        return None

    m = META_RE.search(text)
    if not m:
        print(f'  SKIP {path.name}: missing metadata', file=sys.stderr)
        return None

    received, sent, name, email, subject, msgid = [x.strip() for x in m.groups()]

    inreplyto = None
    im = INREPLYTO_RE.search(text)
    if im:
        irt = im.group(1).strip()
        # validate: must look like a message-id (token@domain, no spaces)
        if MSGID_RE.match(irt):
            inreplyto = irt

    body_m = BODY_RE.search(text)
    if not body_m:
        print(f'  SKIP {path.name}: no body', file=sys.stderr)
        return None

    body = strip_html(body_m.group(1))
    body = body.strip()
    body = quote_from_lines(body)

    return {
        'received': received,
        'sent': sent,
        'name': name,
        'email': email,
        'subject': subject,
        'msgid': msgid,
        'inreplyto': inreplyto,
        'body': body,
    }


def make_mbox_entry(msg):
    from_addr = msg['email'] if msg['email'] else 'unknown'
    received = msg['received'].strip()

    lines = [f"From {from_addr} {received}"]

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

    lines.append('')  # blank line before body
    lines.append(msg['body'])
    lines.append('')  # trailing blank line

    return '\n'.join(lines)


def convert_month(year, month):
    # Try canonical capitalization, then lowercase
    dir_name = f'{month}{year}'
    month_dir = HTML_BASE / str(year) / dir_name
    if not month_dir.exists():
        month_dir = HTML_BASE / str(year) / dir_name.lower()
    if not month_dir.exists():
        print(f'  MISSING: {year}/{dir_name}', file=sys.stderr)
        return 0

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
    total = 0
    for year, month in TARGETS:
        print(f'{year}-{month}...', end=' ', flush=True)
        n = convert_month(year, month)
        print(f'{n} messages')
        total += n
    print(f'\nTotal: {total} messages')


if __name__ == '__main__':
    main()
