#!/usr/bin/env python3
"""Scrape axp-redhat from marc.info into per-month mbox files.

Fetches months 199511–199802 (pre-dating our Wayback coverage).
Respects marc.info's requested 1-2s delay between requests.
"""

import os
import re
import time
import urllib.request

BASE = "https://marc.info/"
LIST = "axp-redhat"
OUT_DIR = os.path.join(os.path.dirname(__file__), "axp-list-mbox")

# Months to fetch: 199511 through 199802 inclusive
# (1998-03 onwards covered by Wayback)
NEED_MONTHS = []
for y in range(1995, 1999):
    for m in range(1, 13):
        ym = f"{y}{m:02d}"
        if ym < "199511":
            continue
        if ym >= "199803":
            break
        NEED_MONTHS.append(ym)

MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May",     "06": "June",     "07": "July",  "08": "August",
    "09": "September","10": "October", "11": "November","12": "December",
}


def get(url, delay=1.5):
    req = urllib.request.Request(url, headers={"User-Agent": "axp-list-archiver/1.0 (archival research)"})
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
    """Return all message IDs for a month, handling pagination."""
    ids = []
    page = 1
    while True:
        url = f"{BASE}?l={LIST}&r={page}&b={ym}&w=2"
        html = get(url)
        found = re.findall(r'\?l=' + LIST + r'&m=(\d+)', html)
        found = list(dict.fromkeys(found))  # dedupe, preserve order
        if not found:
            break
        ids.extend(found)
        # Check if there's a next page link
        if f"r={page + 1}" not in html:
            break
        page += 1
    return list(dict.fromkeys(ids))


def get_message_mbox(msg_id):
    """Fetch one message in mbox format."""
    url = f"{BASE}?l={LIST}&m={msg_id}&q=mbox"
    return get(url)


def ym_to_stem(ym):
    year, mon = ym[:4], ym[4:]
    return f"{year}-{MONTH_NAMES[mon]}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for ym in NEED_MONTHS:
        stem = ym_to_stem(ym)
        mbox_path = os.path.join(OUT_DIR, stem + ".mbox")

        if os.path.exists(mbox_path):
            print(f"skip {stem} (exists)")
            continue

        print(f"{stem} — collecting message IDs...")
        ids = get_message_ids(ym)
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
        print(f"  done: {size:,} bytes")

    print("Done.")


if __name__ == "__main__":
    main()
