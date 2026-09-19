#!/usr/bin/env python3
"""Fetch a Usenet group from the Internet Archive's usenet-<hierarchy>
collections (Google Groups/Deja News mbox dumps) and split it into per-month
mbox files.

Source: https://archive.org/download/usenet-<hierarchy>/<group>.mbox.zip
where <hierarchy> is the group's first component (comp, biz, ...).

These dumps use "From <deja-id>" separator lines rather than a real
sender+date, so the Date: header is used for bucketing instead. Date formats
vary wildly (RFC822 variants, bare "YYYY/MM/DD", even prose dates); anything
unparseable is dumped in an "undated" bucket for manual triage.

Usage: fetch-usenet-archive-mbox.py <group> <out-dir>
"""
import datetime
import email.utils
import os
import re
import sys
import urllib.request
import zipfile

ARCHIVE_URL = "https://archive.org/download/usenet-{hierarchy}/{group}.mbox.zip"

MIN_YEAR = 1990
MAX_YEAR = datetime.date.today().year + 1

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

PLAIN_DATE_RE = re.compile(rb"^Date:\s*(\d{4})/(\d{2})/(\d{2})", re.M)


def header(chunk, name):
    want = name.lower().encode()
    head, _, _ = chunk.partition(b"\n\n")
    lines = head.split(b"\n")
    for i, line in enumerate(lines):
        key, _, value = line.partition(b":")
        if key.strip().lower() != want:
            continue
        for cont in lines[i + 1:]:
            if cont[:1] not in (b" ", b"\t"):
                break
            value += b" " + cont.strip()
        return value.decode("utf-8", "replace").strip()
    return None


def message_date(chunk):
    value = header(chunk, "Date")
    if value:
        try:
            date = email.utils.parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=datetime.timezone.utc)
            if MIN_YEAR <= date.year <= MAX_YEAR:
                return date
        except (TypeError, ValueError):
            pass
    match = PLAIN_DATE_RE.search(chunk.partition(b"\n\n")[0])
    if match:
        year, month, day = (int(x) for x in match.groups())
        if MIN_YEAR <= year <= MAX_YEAR:
            try:
                return datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)
            except ValueError:
                pass
    return None


def download(group, dest):
    url = ARCHIVE_URL.format(hierarchy=group.split(".")[0], group=group)
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, dest)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {os.path.basename(sys.argv[0])} <group> <out-dir>")
    group, out_dir = sys.argv[1], sys.argv[2]
    out_dir = out_dir if os.path.isabs(out_dir) else os.path.join(os.path.dirname(__file__), out_dir)
    os.makedirs(out_dir, exist_ok=True)

    cache_dir = os.path.join(os.path.dirname(__file__), ".usenet-archive-cache")
    os.makedirs(cache_dir, exist_ok=True)
    zip_path = os.path.join(cache_dir, f"{group}.mbox.zip")
    if not os.path.exists(zip_path):
        download(group, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.endswith(".mbox")]
        if len(names) != 1:
            raise SystemExit(f"expected exactly one .mbox in {zip_path}, got {names}")
        data = zf.read(names[0])

    # Real separator lines are "From <deja-id>" (deja-id is a bare, possibly
    # negative integer). Plain "From " body text is common in these dumps and
    # must not be mistaken for a separator, or messages get split mid-body.
    chunks = re.split(rb"(?=^From -?\d+\r?\n)", data, flags=re.M)
    chunks = [c for c in chunks if c.strip()]
    print(f"{group}: {len(chunks)} messages")

    months = {}
    undated = []
    for chunk in chunks:
        date = message_date(chunk)
        if date is None:
            undated.append(chunk)
            continue
        months.setdefault((date.year, date.month), []).append(chunk)

    total = 0
    for (year, month), messages in sorted(months.items()):
        path = os.path.join(out_dir, f"googlegroups-{year}-{MONTH_NAMES[month]}.mbox")
        with open(path, "wb") as f:
            f.write(b"".join(messages))
        total += len(messages)
        print(f"  {os.path.basename(path)}: {len(messages)} messages")
    print(f"{total} messages written")

    if undated:
        path = os.path.join(out_dir, "googlegroups-undated.mbox")
        with open(path, "wb") as f:
            f.write(b"".join(undated))
        print(f"{len(undated)} undated messages written to {os.path.basename(path)}")


if __name__ == "__main__":
    main()
