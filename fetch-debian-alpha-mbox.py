#!/usr/bin/env python3
"""Fetch debian-alpha from Gmane (gmane.linux.debian.ports.alpha) via NNTP."""

import sys
import time
import warnings
import email.utils
from pathlib import Path
from datetime import datetime, timezone

warnings.filterwarnings('ignore', category=DeprecationWarning)
import nntplib

SERVER = 'news.gmane.io'
GROUP = 'gmane.linux.debian.ports.alpha'
MBOX_DIR = Path(__file__).parent / 'debian-alpha-mbox'

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


def from_line_date(date_str):
    try:
        ts = email.utils.parsedate_to_datetime(date_str)
        return ts.strftime('%a %b %e %H:%M:%S %Y').replace('  ', ' ')
    except Exception:
        return 'Thu Jan  1 00:00:00 1970'


def get_sender(from_hdr):
    addrs = email.utils.getaddresses([from_hdr])
    if addrs:
        return addrs[0][1] or 'unknown'
    return 'unknown'


def main():
    MBOX_DIR.mkdir(exist_ok=True)

    s = nntplib.NNTP(SERVER, timeout=60)
    print(f'Connected: {s.getwelcome().strip()}')

    resp, count, first, last, name = s.group(GROUP)
    first, last = int(first), int(last)
    print(f'{GROUP}: articles {first}–{last} ({count} total)')

    buckets = {}  # (year, month_name) → list of mbox entries

    for artnum in range(first, last + 1):
        try:
            resp, info = s.article(artnum)
        except nntplib.NNTPTemporaryError as e:
            print(f'  SKIP {artnum}: {e}', file=sys.stderr)
            continue

        msg_date = ''
        msg_from = 'unknown'
        for line in info.lines:
            decoded = line.decode('latin-1')
            if decoded.lower().startswith('date:'):
                msg_date = decoded[5:].strip()
            elif decoded.lower().startswith('from:'):
                msg_from = get_sender(decoded[5:].strip())
            if msg_date and msg_from != 'unknown':
                break

        from_line = f'From {msg_from} {from_line_date(msg_date)}'

        body_lines = []
        in_headers = True
        for line in info.lines:
            decoded = line.decode('latin-1')
            if in_headers and decoded == '':
                in_headers = False
            if not in_headers and decoded.startswith('From '):
                decoded = '>' + decoded
            body_lines.append(decoded)

        entry = from_line + '\n' + '\n'.join(body_lines) + '\n\n'

        try:
            ts = email.utils.parsedate_to_datetime(msg_date)
            key = (ts.year, MONTH_NAMES[ts.month])
        except Exception:
            key = (0, 'Unknown')

        buckets.setdefault(key, []).append(entry)

        if artnum % 100 == 0:
            print(f'  {artnum}/{last} ({artnum - first + 1} fetched)', end='\r', flush=True)

        time.sleep(0.1)

    s.quit()
    print()

    for (year, month), entries in sorted(buckets.items()):
        out = MBOX_DIR / f'{year}-{month}.mbox'
        with out.open('w', encoding='utf-8') as f:
            for entry in entries:
                f.write(entry)
        print(f'  {year}-{month}: {len(entries)} messages → {out.name}')

    total = sum(len(v) for v in buckets.values())
    print(f'\nTotal: {total} messages')


if __name__ == '__main__':
    main()
