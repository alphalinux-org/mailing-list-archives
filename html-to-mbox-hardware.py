#!/usr/bin/env python3
"""Convert alphalinux.org Pipermail shtml files to per-month mbox files.

Usage: html-to-mbox-hardware.py [html-source-dir [mbox-output-dir]]
Defaults: axp-hardware  axp-hardware-mbox
"""

import re
import html
import sys
from pathlib import Path

BASE = Path(__file__).parent
HTML_BASE = BASE / (sys.argv[1] if len(sys.argv) > 1 else 'axp-hardware')
MBOX_DIR  = BASE / (sys.argv[2] if len(sys.argv) > 2 else (HTML_BASE.name + '-mbox'))

MONTH_NAMES = {
    'january': 'January', 'february': 'February', 'march': 'March',
    'april': 'April', 'may': 'May', 'june': 'June', 'july': 'July',
    'august': 'August', 'september': 'September', 'october': 'October',
    'november': 'November', 'december': 'December',
}
INDEX_FILES = {'date.shtml', 'thread.shtml', 'subject.shtml',
               'author.shtml', 'index.shtml'}

META_RE = re.compile(
    r'<!--\s*received="([^"]*)"[^>]*-->\s*'
    r'(?:<!--[^>]*-->\s*)*?'          # skip isoreceived etc.
    r'<!--\s*sent="([^"]*)"[^>]*-->\s*'
    r'(?:<!--[^>]*-->\s*)*?'
    r'<!--\s*name="([^"]*)"[^>]*-->\s*'
    r'(?:<!--[^>]*-->\s*)*?'
    r'<!--\s*email="([^"]*)"[^>]*-->\s*'
    r'(?:<!--[^>]*-->\s*)*?'
    r'<!--\s*subject="([^"]*)"[^>]*-->\s*'
    r'(?:<!--[^>]*-->\s*)*?'
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
    return '\n'.join(
        '>From ' + l[5:] if l.startswith('From ') else l
        for l in text.split('\n')
    )


def parse_shtml(path):
    try:
        text = path.read_text(encoding='latin-1')
    except Exception as e:
        print(f'  SKIP {path.name}: {e}', file=sys.stderr)
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
    from_addr = msg['email'] or 'unknown'
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


def parse_dir_name(name):
    """Parse 'Month{YEAR}' directory names, return (year, MonthName) or None."""
    m = re.match(r'^([A-Za-z]+)(\d{4})$', name)
    if not m:
        return None
    month_lower = m.group(1).lower()
    year = int(m.group(2))
    month = MONTH_NAMES.get(month_lower)
    if not month:
        return None
    return year, month


def main():
    MBOX_DIR.mkdir(exist_ok=True)
    total = 0

    dirs = []
    for d in HTML_BASE.iterdir():
        if not d.is_dir():
            continue
        parsed = parse_dir_name(d.name)
        if parsed:
            dirs.append((parsed, d))

    for (year, month), month_dir in sorted(dirs):
        shtml_files = sorted(
            [f for f in month_dir.glob('*.shtml') if f.name not in INDEX_FILES],
            key=lambda p: int(p.stem),
        )
        if not shtml_files:
            continue

        out_path = MBOX_DIR / f'{year}-{month}.mbox'
        count = 0
        with out_path.open('w', encoding='utf-8') as f:
            for sf in shtml_files:
                msg = parse_shtml(sf)
                if msg is None:
                    continue
                f.write(make_mbox_entry(msg))
                f.write('\n')
                count += 1

        print(f'{year}-{month}: {count} messages')
        total += count

    print(f'\nTotal: {total} messages')


if __name__ == '__main__':
    main()
