#!/usr/bin/env python3
"""Scrape a NetBSD list from mail-index.netbsd.org into per-month mbox files.

mail-index is NetBSD's official archive and reaches back further than Gmane or
marc.info, but its message pages carry only Subject/To/From/Date: no
Message-ID, no In-Reply-To, no Received.  Use it only for months no
better-headered source covers.

Pages are cached under .mailindex-cache/<list>/ so the scrape can be resumed.

Usage: fetch-netbsd-mailindex.py <list> <out-dir> <first-ym> <last-ym>
  e.g. fetch-netbsd-mailindex.py port-alpha netbsd-port-alpha-mbox 199601 200112
"""

import html
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://mail-index.netbsd.org"
USER_AGENT = "alphalinux-list-archiver/1.0 (archival research)"
DELAY = 0.4

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

LINK_RE = re.compile(r'HREF="(\d\d/\d+\.html)"', re.IGNORECASE)
FIELD_RE = {
    name: re.compile(r"<B>" + name + r":</B>(.*?)(?:<BR>|\n)", re.IGNORECASE | re.DOTALL)
    for name in ("Subject", "To", "From", "Date")
}
BODY_RE = re.compile(r"<PRE>(.*?)</PRE>", re.IGNORECASE | re.DOTALL)


def get(url, cache_path):
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read().decode("utf-8", "replace")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == 4:
                raise
            time.sleep(5 * (2 ** attempt))
        except Exception:
            if attempt == 4:
                raise
            time.sleep(5 * (2 ** attempt))
    time.sleep(DELAY)
    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(data)
    return data.decode("utf-8", "replace")


def strip_tags(text):
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def field(page, name):
    m = FIELD_RE[name].search(page)
    return strip_tags(m.group(1)) if m else ""


def address(value):
    """'Real Name <addr@host>' from mail-index's 'Real Name <addr@host>' text."""
    m = re.search(r"<([^<>]+@[^<>]+)>", value)
    if not m:
        return value.strip(), ""
    return value[: m.start()].strip(), m.group(1).strip()


def mbox_date(value):
    """'01/02/2000 11:09:01' (UTC) -> RFC 2822 date, plus mbox 'From ' stamp."""
    m = re.match(r"(\d\d)/(\d\d)/(\d{4})\s+(\d\d):(\d\d):(\d\d)", value.strip())
    if not m:
        return None, None
    mon, day, year, hh, mm, ss = (int(x) for x in m.groups())
    import datetime
    try:
        dt = datetime.datetime(year, mon, day, hh, mm, ss, tzinfo=datetime.timezone.utc)
    except ValueError:
        return None, None
    return (
        dt.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        dt.strftime("%a %b %e %H:%M:%S %Y").replace("  ", " "),
    )


def quote_from_lines(text):
    return "\n".join(
        ">" + line if line.startswith("From ") else line for line in text.split("\n")
    )


def parse_message(page):
    date_hdr, stamp = mbox_date(field(page, "Date"))
    if date_hdr is None:
        return None
    name, addr = address(field(page, "From"))
    to_name, to_addr = address(field(page, "To"))
    body_m = BODY_RE.search(page)
    if not body_m:
        return None
    body = quote_from_lines(html.unescape(re.sub(r"<[^>]+>", "", body_m.group(1))).strip())

    from_hdr = f"{name} <{addr}>" if name and addr else (addr or name or "unknown")
    lines = [f"From {addr or 'unknown'}  {stamp}"]
    lines.append(f"From: {from_hdr}")
    if to_addr:
        lines.append(f"To: {to_addr}")
    lines.append(f"Date: {date_hdr}")
    lines.append(f"Subject: {field(page, 'Subject')}")
    lines.append("")
    lines.append(body)
    lines.append("")
    return "\n".join(lines) + "\n"


def months(first_ym, last_ym):
    year, mon = int(first_ym[:4]), int(first_ym[4:])
    while f"{year}{mon:02d}" <= last_ym:
        yield year, mon
        mon += 1
        if mon == 13:
            year, mon = year + 1, 1


def main():
    if len(sys.argv) != 5:
        raise SystemExit(f"usage: {os.path.basename(sys.argv[0])} <list> <out-dir> "
                         "<first-ym> <last-ym>")
    listname, out_dir, first_ym, last_ym = sys.argv[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(here, out_dir)
    cache_root = os.path.join(here, ".mailindex-cache", listname)
    os.makedirs(out_dir, exist_ok=True)

    total = 0
    for year, mon in months(first_ym, last_ym):
        stem = f"{year}-{MONTH_NAMES[mon]}"
        index_url = f"{BASE}/{listname}/{year}/{mon:02d}/index.html"
        index = get(index_url, os.path.join(cache_root, f"{year}-{mon:02d}-index.html"))
        if index is None:
            print(f"{stem}: no index")
            continue
        links = list(dict.fromkeys(LINK_RE.findall(index)))
        entries = []
        for link in links:
            page = get(f"{BASE}/{listname}/{year}/{mon:02d}/{link}",
                       os.path.join(cache_root, f"{year}-{mon:02d}", link.replace("/", "-")))
            if page is None:
                continue
            entry = parse_message(page)
            if entry:
                entries.append(entry)
        if entries:
            with open(os.path.join(out_dir, f"{stem}.mbox"), "w",
                      encoding="utf-8", errors="replace") as f:
                f.writelines(entries)
        total += len(entries)
        print(f"{stem}: {len(entries)}/{len(links)} messages")
    print(f"total: {total} messages")


if __name__ == "__main__":
    main()
