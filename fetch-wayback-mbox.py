#!/usr/bin/env python3
"""Download axp-list mbox files from Wayback Machine."""

import gzip
import os
import time
import urllib.request
import urllib.error

CDX_SOURCES = [
    # 2004-2022: listman.redhat.com (2023 crawl)
    (
        "https://web.archive.org/cdx/search/cdx"
        "?url=listman.redhat.com/archives/axp-list/"
        "&matchType=prefix&output=text&fl=timestamp,original"
        "&filter=original:.*\\.txt\\.gz&collapse=original"
    ),
    # 1998-2003 (and overlap): www.redhat.com (2019 crawl)
    (
        "https://web.archive.org/cdx/search/cdx"
        "?url=www.redhat.com/archives/axp-list/"
        "&matchType=prefix&output=text&fl=timestamp,original"
        "&filter=original:.*\\.txt\\.gz&collapse=original"
    ),
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "axp-list-mbox")


def fetch_cdx(url):
    with urllib.request.urlopen(url) as r:
        return [line.split() for line in r.read().decode().splitlines() if line.strip()]


def wayback_url(timestamp, original):
    # id_ returns raw stored bytes (if_ decodes Content-Encoding and truncates)
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "axp-list-archiver/1.0"})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Collect all entries from both sources; listman takes priority (listed first)
    seen = {}  # stem -> (timestamp, original)
    for cdx_url in CDX_SOURCES:
        print(f"Fetching CDX: {cdx_url.split('?')[0].split('/')[-3]}...")
        entries = fetch_cdx(cdx_url)
        print(f"  {len(entries)} entries")
        for timestamp, original in entries:
            filename = original.rsplit("/", 1)[-1]
            stem = filename[: -len(".txt.gz")]
            if stem not in seen:
                seen[stem] = (timestamp, original)

    print(f"\n{len(seen)} unique months total")

    for stem, (timestamp, original) in sorted(seen.items()):
        mbox_path = os.path.join(OUT_DIR, stem + ".mbox")

        if os.path.exists(mbox_path):
            print(f"  skip {stem} (exists)")
            continue

        url = wayback_url(timestamp, original)
        gz_path = mbox_path + ".gz"

        print(f"  {stem} ... ", end="", flush=True)
        delay = 3
        for attempt in range(6):
            try:
                download(url, gz_path)
                with open(gz_path, "rb") as f:
                    magic = f.read(2)
                if magic == b"\x1f\x8b":
                    with gzip.open(gz_path, "rb") as gz, open(mbox_path, "wb") as out:
                        out.write(gz.read())
                else:
                    # Wayback served it already decompressed
                    os.rename(gz_path, mbox_path)
                    gz_path = None
                if gz_path and os.path.exists(gz_path):
                    os.unlink(gz_path)
                size = os.path.getsize(mbox_path)
                print(f"{size:,} bytes")
                break
            except Exception as e:
                if gz_path and os.path.exists(gz_path):
                    os.unlink(gz_path)
                if os.path.exists(mbox_path):
                    os.unlink(mbox_path)
                if attempt == 5:
                    print(f"FAILED: {e}")
                else:
                    print(f"retry({attempt+1}) after {delay}s ... ", end="", flush=True)
                    time.sleep(delay)
                    delay *= 2

        time.sleep(2)

    print("Done.")


if __name__ == "__main__":
    main()
