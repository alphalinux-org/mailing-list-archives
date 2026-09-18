#!/usr/bin/env python3
"""Scrape a list from marc.info into per-month mbox files.

marc.info reconstructs headers: no Message-ID, no In-Reply-To, and addresses
are obfuscated ("user () host ! com").  Use it only where no better-headered
source (Gmane, Pipermail) covers the months in question.
Respects marc.info's requested 1-2s delay between requests.

Usage: fetch-marc-list.py <list> <out-dir> <first-ym> <last-ym>
  e.g. fetch-marc-list.py openbsd-alpha openbsd-alpha-mbox 200109 202602
"""
import os
import re
import sys
import time
import urllib.request

BASE = "https://marc.info/"

MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May",     "06": "June",     "07": "July",  "08": "August",
    "09": "September","10": "October", "11": "November","12": "December",
}


def get(url, delay=1.5):
    req = urllib.request.Request(url, headers={"User-Agent": "alphalinux-list-archiver/1.0 (archival research)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            time.sleep(delay)
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == 4:
                raise
            wait = 5 * (2 ** attempt)
            print(f"    retry after {wait}s ({e})")
            time.sleep(wait)


def get_message_ids(ym):
    """Return all message IDs for a month.

    A month listing shows thread heads only ("[39] Alpha port.."), so each
    thread has to be expanded; both the listing and the thread views paginate
    30 rows at a time.
    """
    ids = []
    threads = []
    page = 1
    while True:
        html = get(f"{BASE}?l={LIST}&r={page}&b={ym}&w=2")
        found = re.findall(r"\?l=" + LIST + r"&m=(\d+)", html)
        threads += re.findall(r"\?t=(\d+)&r=1&w=2", html)
        if not found:
            break
        ids += found
        if f"r={page + 1}&b={ym}" not in html:
            break
        page += 1

    for tid in dict.fromkeys(threads):
        page = 1
        while True:
            html = get(f"{BASE}?t={tid}&r={page}&w=2")
            found = re.findall(r"\?l=" + LIST + r"&m=(\d+)", html)
            if not found:
                break
            before = len(dict.fromkeys(ids))
            ids += found
            if len(dict.fromkeys(ids)) == before:
                break  # nothing new: past the end of the thread
            page += 1

    return list(dict.fromkeys(ids))


def get_message_mbox(msg_id):
    """Fetch one message in mbox format."""
    url = f"{BASE}?l={LIST}&m={msg_id}&q=mbox"
    return get(url)


def ym_to_stem(ym):
    year, mon = ym[:4], ym[4:]
    return f"{year}-{MONTH_NAMES[mon]}"


def months(first_ym, last_ym):
    year, mon = int(first_ym[:4]), int(first_ym[4:])
    out = []
    while f"{year}{mon:02d}" <= last_ym:
        out.append(f"{year}{mon:02d}")
        mon += 1
        if mon == 13:
            year, mon = year + 1, 1
    return out


def main():
    global LIST, OUT_DIR
    if len(sys.argv) != 5:
        raise SystemExit(f"usage: {os.path.basename(sys.argv[0])} <list> <out-dir> "
                         "<first-ym> <last-ym>")
    LIST, out_dir, first_ym, last_ym = sys.argv[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    OUT_DIR = out_dir if os.path.isabs(out_dir) else os.path.join(here, out_dir)
    os.makedirs(OUT_DIR, exist_ok=True)

    # Threads are expanded per month, so a thread spanning a month boundary
    # would otherwise yield the same message twice.
    seen = set()

    for ym in months(first_ym, last_ym):
        stem = ym_to_stem(ym)
        mbox_path = os.path.join(OUT_DIR, stem + ".mbox")

        if os.path.exists(mbox_path):
            print(f"skip {stem} (exists)")
            continue

        print(f"{stem} — collecting message IDs...")
        ids = [i for i in get_message_ids(ym) if i not in seen]
        seen.update(ids)
        print(f"  {len(ids)} messages, fetching...")

        with open(mbox_path, "w", encoding="utf-8", errors="replace") as f:
            for i, msg_id in enumerate(ids, 1):
                if i % 50 == 0:
                    print(f"  {i}/{len(ids)}...")
                msg = get_message_mbox(msg_id)
                f.write(msg)
                if not msg.endswith("\n\n"):
                    f.write("\n")

        size = os.path.getsize(mbox_path)
        if size == 0:
            os.remove(mbox_path)  # month with no messages
        print(f"  done: {size:,} bytes")

    print("Done.")


if __name__ == "__main__":
    main()
