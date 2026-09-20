#!/usr/bin/env python3
"""Convert downloaded alphant HTML (alphant/) to mbox.

Handles both archive formats found for this list:

  - Hypermail (1995Q4, 1996Q1, 1996Q2, current): metadata in
    <!-- received= sent= name= email= subject= id= inreplyto= --> comments,
    body between <!-- body="start" --> and <!-- body="end" -->.
  - MHonArc (YYYY-MM[-W] directories): metadata in <!--X-Subject:-->,
    <!--X-From:-->, <!--X-Date:-->, <!--X-Message-Id:--> comments, real
    headers in the <!--X-Head-of-Message--> <ul> block, body between
    <!--X-Body-of-Message--> and <!--X-Body-of-Message-End-->.

Directory names carry no reliable month for the Hypermail quarters, so every
message is bucketed by its Date header.  Output: alphant-mbox/YYYY-Month.mbox.
"""

import datetime
import email.utils
import html
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
HTML_BASE = BASE / 'alphant'
MBOX_DIR = BASE / 'alphant-mbox'

MONTH_ORDER = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

MSGID_RE = re.compile(r'^[^@\s]+@[^@\s]+$')

# Hypermail
HM_META_RE = re.compile(
    r'<!--\s*received="([^"]*)"[^>]*-->\s*'
    r'<!--\s*sent="([^"]*)"[^>]*-->\s*'
    r'<!--\s*name="([^"]*)"[^>]*-->\s*'
    r'<!--\s*email="([^"]*)"[^>]*-->\s*'
    r'<!--\s*subject="([^"]*)"[^>]*-->\s*'
    r'<!--\s*id="([^"]*)"[^>]*-->',
    re.DOTALL,
)
HM_INREPLYTO_RE = re.compile(r'<!--\s*inreplyto="([^"]*)"[^>]*-->')
HM_BODY_RE = re.compile(r'<!--\s*body="start"\s*-->(.*?)<!--\s*body="end"\s*-->', re.DOTALL)

# MHonArc
MA_FIELD_RE = re.compile(r'<!--X-([A-Za-z-]+):\s*(.*?)\s*-->', re.DOTALL)
MA_HEAD_RE = re.compile(
    r'<!--X-Head-of-Message-->(.*?)<!--X-Head-of-Message-End-->', re.DOTALL)
MA_BODY_RE = re.compile(
    r'<!--X-Body-of-Message-->(.*?)<!--X-Body-of-Message-End-->', re.DOTALL)
MA_HEADER_LI_RE = re.compile(
    r'<li>\s*<em>([^<]+)</em>\s*:\s*(.*?)\s*</li>', re.DOTALL | re.IGNORECASE)

# Headers kept from the MHonArc head-of-message block, in output order
KEEP_HEADERS = ['from', 'to', 'cc', 'subject', 'date', 'message-id',
                'in-reply-to', 'references', 'reply-to']


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


def parse_hypermail(text):
    m = HM_META_RE.search(text)
    if not m:
        return None
    received, sent, name, address, subject, msgid = [x.strip() for x in m.groups()]

    inreplyto = None
    im = HM_INREPLYTO_RE.search(text)
    if im and MSGID_RE.match(im.group(1).strip()):
        inreplyto = im.group(1).strip()

    body_m = HM_BODY_RE.search(text)
    if not body_m:
        return None

    from_hdr = name
    if address:
        from_hdr = f'{name} <{address}>' if name else address

    headers = []
    if sent:
        headers.append(('Date', sent))
    headers.append(('From', from_hdr))
    headers.append(('Subject', html.unescape(subject)))
    if inreplyto:
        headers.append(('In-Reply-To', f'<{inreplyto}>'))

    return {
        'envelope': address or 'unknown',
        'received': received,
        'date': sent,
        'msgid': msgid,
        'subject': subject,
        'headers': headers,
        'body': quote_from_lines(strip_html(body_m.group(1)).strip()),
    }


def parse_mhonarc(text):
    fields = {k.lower(): html.unescape(v) for k, v in MA_FIELD_RE.findall(text)}

    head = {}
    hm = MA_HEAD_RE.search(text)
    if hm:
        for key, value in MA_HEADER_LI_RE.findall(hm.group(1)):
            head[key.strip().lower()] = html.unescape(strip_html(value)).strip()

    body_m = MA_BODY_RE.search(text)
    if not body_m:
        return None

    date = head.get('date') or fields.get('date', '')
    subject = head.get('subject') or fields.get('subject', '')
    from_hdr = head.get('from') or fields.get('from', '')
    msgid = head.get('message-id') or fields.get('message-id', '')
    msgid = msgid.strip('<>')

    headers = []
    if date:
        headers.append(('Date', date))
    if from_hdr:
        headers.append(('From', from_hdr))
    headers.append(('Subject', subject))
    for key in KEEP_HEADERS:
        if key in ('from', 'subject', 'date', 'message-id'):
            continue
        if key in head:
            headers.append((key.title(), head[key]))

    address = ''
    am = re.search(r'<([^<>@\s]+@[^<>@\s]+)>', from_hdr) or \
        re.search(r'([^<>@\s]+@[^<>@\s]+)', from_hdr)
    if am:
        address = am.group(1)

    return {
        'envelope': address or 'unknown',
        'received': date,
        'date': date,
        'msgid': msgid,
        'subject': subject,
        'headers': headers,
        'body': quote_from_lines(strip_html(body_m.group(1)).strip()),
    }


def parse_file(path):
    try:
        text = path.read_text(encoding='latin-1')
    except Exception as e:
        print(f'  SKIP {path}: {e}', file=sys.stderr)
        return None

    msg = parse_mhonarc(text) if 'MHonArc' in text[:200] else parse_hypermail(text)
    if msg is None:
        print(f'  SKIP {path}: unparseable', file=sys.stderr)
    return msg


def parse_date(value):
    """Parse an RFC 822 date, or Hypermail's ctime-style received line."""
    if not value:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        dt = None
    if dt is None:
        # Hypermail received= looks like "Mon Sep 18 17:14:26 1995 CDT";
        # drop the trailing timezone name, which strptime cannot read.
        m = re.match(r'([A-Z][a-z]{2} [A-Z][a-z]{2} +\d+ \d+:\d+:\d+ \d{4})', value.strip())
        if m:
            try:
                dt = datetime.datetime.strptime(m.group(1), '%a %b %d %H:%M:%S %Y')
            except ValueError:
                dt = None
    if dt is None or not (1990 <= dt.year <= 2005):
        return None
    return dt


def bucket(msg):
    """Return (year, month_name), preferring the Date header.

    A few senders had badly set clocks (one message dated 1990 was really
    March 1996).  When the archive's own received time disagrees with the
    Date header by more than half a year, trust the received time.
    """
    sent = parse_date(msg['date'])
    received = parse_date(msg['received'])
    dt = sent or received
    if dt is None:
        return None
    if sent and received and abs((sent - received.replace(tzinfo=sent.tzinfo)).days) > 180:
        dt = received
    return dt.year, MONTH_ORDER[dt.month - 1]


def fix_duplicate_msgids(messages):
    """Replace Message-IDs the archive assigned to more than one message.

    The Hypermail archive is buggy: 262 IDs are shared by up to 11 distinct
    messages (different sender, subject and date).  Leaving them as-is would
    make an importer such as public-inbox deduplicate real messages away, so
    every member of an ambiguous group gets a synthetic ID derived from its
    archive path, with the archive's claim kept in a X-Archive-Original-
    Message-ID header.  Groups where every copy agrees on sender, subject and
    date are genuine duplicates of one message and are left alone.
    """
    groups = {}
    for msg in messages:
        if msg['msgid']:
            groups.setdefault(msg['msgid'], []).append(msg)

    fixed = 0
    for msgid, group in groups.items():
        if len(group) < 2:
            continue
        identity = {(m['envelope'], m['subject'], m['date']) for m in group}
        if len(identity) == 1:
            continue
        for msg in group:
            path = msg['path']
            msg['original_msgid'] = msgid
            msg['msgid'] = f'{path.parent.name}-{path.stem}.alphant@archive.invalid'
            fixed += 1
    return fixed


def make_mbox_entry(msg):
    lines = [f"From {msg['envelope']} {msg['received'].strip()}"]
    if msg['msgid']:
        lines.append(f"Message-ID: <{msg['msgid']}>")
    if msg.get('original_msgid'):
        lines.append(f"X-Archive-Original-Message-ID: <{msg['original_msgid']}>")
    lines += [f'{k}: {v}' for k, v in msg['headers']]
    lines.append('')
    lines.append(msg['body'])
    lines.append('')
    return '\n'.join(lines)


def main():
    MBOX_DIR.mkdir(exist_ok=True)

    parsed = []
    files = sorted(HTML_BASE.glob('*/*.html'))
    for path in files:
        msg = parse_file(path)
        if msg is None:
            continue
        msg['path'] = path
        parsed.append(msg)

    fixed = fix_duplicate_msgids(parsed)
    if fixed:
        print(f'{fixed} messages given synthetic Message-IDs '
              f'(the archive reused one ID across different messages)\n')

    buckets = {}
    undated = []
    for msg in parsed:
        key = bucket(msg)
        if key is None:
            undated.append(msg)
        else:
            buckets.setdefault(key, []).append(msg)

    total = 0
    for (year, month), msgs in sorted(buckets.items(),
                                      key=lambda kv: (kv[0][0], MONTH_ORDER.index(kv[0][1]))):
        out = MBOX_DIR / f'{year}-{month}.mbox'
        with out.open('w', encoding='utf-8') as f:
            for msg in msgs:
                f.write(make_mbox_entry(msg))
                f.write('\n')
        print(f'{year}-{month}: {len(msgs)} messages')
        total += len(msgs)

    if undated:
        out = MBOX_DIR / 'undated.mbox'
        with out.open('w', encoding='utf-8') as f:
            for msg in undated:
                f.write(make_mbox_entry(msg))
                f.write('\n')
        print(f'undated: {len(undated)} messages')
        total += len(undated)

    print(f'\nTotal: {total} messages from {len(files)} files')


if __name__ == '__main__':
    main()
