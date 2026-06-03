#!/usr/bin/env python3
"""Merge old mbox headers with clean bodies from git commit 507755a3.

Old mbox files (local MHonArc HTML): full headers (From with email,
In-Reply-To) but bodies have a blank line after every line.
New mbox files (lists.debian.org scrape): clean bodies but stripped
headers (no email addresses, no In-Reply-To).

Strategy: for each message in old file, find matching message in new
file by Message-ID, replace body with clean version. Keep old message
unchanged if no match found.
"""

import re
import subprocess
import sys
from pathlib import Path

NEW_COMMIT = '507755a3'
MBOX_DIR = Path(__file__).parent / 'debian-alpha-mbox'

MONTHS = [
    '1999-January', '1999-February', '1999-March', '1999-April',
    '1999-May', '1999-June', '1999-July', '1999-August',
    '1999-September', '1999-October', '1999-November', '1999-December',
    '2000-January', '2000-February', '2000-March', '2000-April',
    '2000-May', '2000-June', '2000-July', '2000-August',
    '2000-September', '2000-October', '2000-November', '2000-December',
    '2001-January', '2001-February', '2001-March', '2001-April',
    '2001-May', '2001-June', '2001-July', '2001-August',
    '2001-September',
]


def parse_mbox(text):
    """Parse mbox into list of (envelope, headers_text, body_text)."""
    messages = []
    # Split on mbox message separators
    # Each message starts with "From " at start of line
    parts = re.split(r'(?m)^(?=From )', text)
    for part in parts:
        if not part.strip():
            continue
        lines = part.split('\n')
        envelope = lines[0]
        # Find blank line separating headers from body
        sep = None
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                sep = i
                break
        if sep is None:
            # No blank line found — treat entire thing as headers, no body
            headers = '\n'.join(lines[1:])
            body = ''
        else:
            headers = '\n'.join(lines[1:sep])
            body = '\n'.join(lines[sep+1:])
        messages.append((envelope, headers, body))
    return messages


def extract_msgid(headers):
    m = re.search(r'^Message-ID:\s*<([^>]+)>', headers, re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None


def read_git_file(commit, rel_path):
    result = subprocess.run(
        ['git', 'show', f'{commit}:{rel_path}'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode != 0:
        return None
    return result.stdout


def build_index(msgs):
    """Return dict of Message-ID -> clean body for a list of parsed messages."""
    index = {}
    for env, hdrs, body in msgs:
        mid = extract_msgid(hdrs)
        if mid:
            index[mid] = body.rstrip('\n')
    return index


def merge_month(month_name):
    rel_path = f'debian-alpha-mbox/{month_name}.mbox'
    local_path = MBOX_DIR / f'{month_name}.mbox'

    old_text = local_path.read_text(encoding='utf-8', errors='replace')
    new_text = read_git_file(NEW_COMMIT, rel_path)

    old_msgs = parse_mbox(old_text)

    if new_text is None:
        print(f'  {month_name}: no new version in git, keeping old unchanged')
        return len(old_msgs), 0

    new_by_msgid = build_index(parse_mbox(new_text))

    merged = []
    matched = 0
    for env, hdrs, body in old_msgs:
        mid = extract_msgid(hdrs)
        if mid and mid in new_by_msgid:
            clean_body = new_by_msgid[mid]
            merged.append(f'{env}\n{hdrs}\n\n{clean_body}\n')
            matched += 1
        else:
            merged.append(f'{env}\n{hdrs}\n\n{body.rstrip(chr(10))}\n')

    with local_path.open('w', encoding='utf-8') as f:
        for entry in merged:
            f.write(entry)
            f.write('\n')

    return len(old_msgs), matched


def split_jan_feb_2001():
    """2001-January in old data contains both Jan and Feb messages.
    Correct split: Jan messages stay, Feb messages move to new file."""
    jan_path = MBOX_DIR / '2001-January.mbox'
    feb_path = MBOX_DIR / '2001-February.mbox'

    old_jan = parse_mbox(jan_path.read_text(encoding='utf-8', errors='replace'))

    new_jan_text = read_git_file(NEW_COMMIT, 'debian-alpha-mbox/2001-January.mbox')
    new_feb_text = read_git_file(NEW_COMMIT, 'debian-alpha-mbox/2001-February.mbox')

    new_jan_ids = set(build_index(parse_mbox(new_jan_text)).keys()) if new_jan_text else set()
    new_feb_by_id = build_index(parse_mbox(new_feb_text)) if new_feb_text else {}

    jan_msgs, feb_msgs = [], []
    for env, hdrs, body in old_jan:
        mid = extract_msgid(hdrs)
        if mid and mid in new_feb_by_id:
            clean_body = new_feb_by_id[mid]
            feb_msgs.append(f'{env}\n{hdrs}\n\n{clean_body}\n')
        else:
            # Stays in January (already has correct body from merge_month pass)
            jan_msgs.append(f'{env}\n{hdrs}\n\n{body.rstrip(chr(10))}\n')

    # Rewrite January without the February messages
    with jan_path.open('w', encoding='utf-8') as f:
        for entry in jan_msgs:
            f.write(entry)
            f.write('\n')

    # Write February
    with feb_path.open('w', encoding='utf-8') as f:
        for entry in feb_msgs:
            f.write(entry)
            f.write('\n')

    print(f'2001-January/February split: {len(jan_msgs)} Jan, {len(feb_msgs)} Feb')


def second_pass():
    """For still-unmatched messages, check adjacent months in git for clean body."""
    # Load all new-month indexes into memory
    new_cache = {}
    for month in MONTHS:
        txt = read_git_file(NEW_COMMIT, f'debian-alpha-mbox/{month}.mbox')
        if txt:
            new_cache[month] = build_index(parse_mbox(txt))

    total_fixed = 0
    total_still_missing = 0

    for i, month in enumerate(MONTHS):
        path = MBOX_DIR / f'{month}.mbox'
        if not path.exists():
            continue

        msgs = parse_mbox(path.read_text(encoding='utf-8', errors='replace'))
        same_month_ids = new_cache.get(month, {})

        fixed = 0
        updated = []
        for env, hdrs, body in msgs:
            mid = extract_msgid(hdrs)
            if mid and mid not in same_month_ids:
                # Search adjacent months
                clean_body = None
                for j in [i+1, i-1, i+2, i-2]:
                    if 0 <= j < len(MONTHS):
                        nb = new_cache.get(MONTHS[j], {}).get(mid)
                        if nb is not None:
                            clean_body = nb
                            break
                if clean_body is not None:
                    updated.append(f'{env}\n{hdrs}\n\n{clean_body}\n')
                    fixed += 1
                else:
                    updated.append(f'{env}\n{hdrs}\n\n{body.rstrip(chr(10))}\n')
                    total_still_missing += 1
            else:
                updated.append(f'{env}\n{hdrs}\n\n{body.rstrip(chr(10))}\n')

        if fixed:
            with path.open('w', encoding='utf-8') as f:
                for entry in updated:
                    f.write(entry)
                    f.write('\n')
            print(f'{month}: fixed {fixed} adjacent-month bodies')
        total_fixed += fixed

    print(f'\nSecond pass: {total_fixed} bodies fixed, {total_still_missing} truly unresolvable')


def main():
    total_msgs = 0
    total_matched = 0
    for month in MONTHS:
        if month == '2001-February':
            continue  # handled by split_jan_feb_2001
        path = MBOX_DIR / f'{month}.mbox'
        if not path.exists():
            continue
        n, matched = merge_month(month)
        print(f'{month}: {matched}/{n} bodies replaced')
        total_msgs += n
        total_matched += matched

    split_jan_feb_2001()
    second_pass()

    print(f'\nTotal first pass: {total_matched}/{total_msgs} messages had bodies replaced')


if __name__ == '__main__':
    main()
