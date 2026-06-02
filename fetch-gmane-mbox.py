#!/usr/bin/env python3
"""Fetch a Gmane newsgroup and write per-month mbox files."""

import re
import sys
import time
import warnings
import email.utils
from pathlib import Path
from datetime import datetime, timezone

warnings.filterwarnings('ignore', category=DeprecationWarning)
import nntplib

SERVER = 'news.gmane.io'
MBOX_DIR = Path(__file__).parent / 'axp-list-mbox'

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


def from_line_date(date_str):
    """Parse RFC 2822 date to ctime-style string for mbox From_ line."""
    try:
        ts = email.utils.parsedate_to_datetime(date_str)
        return ts.strftime('%a %b %e %H:%M:%S %Y').replace('  ', ' ')
    except Exception:
        return 'Thu Jan  1 00:00:00 1970'


def get_sender(from_hdr):
    """Extract email address from From header for mbox From_ line."""
    addrs = email.utils.getaddresses([from_hdr])
    if addrs:
        return addrs[0][1] or 'unknown'
    return 'unknown'


def fetch_group(group_name, output_prefix):
    """Fetch all articles in a group, write per-month mbox files."""
    s = nntplib.NNTP(SERVER, timeout=60)
    print(f'Connected: {s.getwelcome().strip()}')

    resp, count, first, last, name = s.group(group_name)
    first, last = int(first), int(last)
    print(f'{group_name}: articles {first}–{last} ({count} total)')

    # bucket messages by YYYY-Month
    buckets = {}  # key: (year, month_name) → list of mbox entries

    for artnum in range(first, last + 1):
        try:
            resp, info = s.article(artnum)
        except nntplib.NNTPTemporaryFailure as e:
            print(f'  SKIP {artnum}: {e}', file=sys.stderr)
            continue

        raw = b'\n'.join(info.lines).decode('latin-1')

        # parse headers for From_ line and bucketing
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

        # quote any From_ lines in body
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

        # determine bucket from date
        try:
            ts = email.utils.parsedate_to_datetime(msg_date)
            key = (ts.year, MONTH_NAMES[ts.month])
        except Exception:
            key = (0, 'Unknown')

        buckets.setdefault(key, []).append(entry)

        if artnum % 10 == 0:
            print(f'  {artnum}/{last}', end='\r', flush=True)

        time.sleep(0.1)

    s.quit()
    print()

    MBOX_DIR.mkdir(exist_ok=True)
    for (year, month), entries in sorted(buckets.items()):
        out = MBOX_DIR / f'{output_prefix}{year}-{month}.mbox'
        # append if file exists (may have data from another source)
        with out.open('a', encoding='utf-8') as f:
            for entry in entries:
                f.write(entry)
        print(f'  wrote {len(entries)} articles → {out.name}')


if __name__ == '__main__':
    fetch_group('gmane.linux.redhat.axp.kernel', 'axp-kernel-')
