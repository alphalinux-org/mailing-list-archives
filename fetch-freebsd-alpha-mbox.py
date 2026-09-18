#!/usr/bin/env python3
"""Download freebsd-alpha monthly mbox files from lists.freebsd.org Pipermail."""

import gzip
import os
import re
import time
import urllib.request

INDEX_URL = "https://lists.freebsd.org/pipermail/freebsd-alpha/"
OUT_DIR = os.path.join(os.path.dirname(__file__), "freebsd-alpha-mbox")
USER_AGENT = "alphalinux-list-archiver/1.0"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as r:
        return r.read()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    index = fetch(INDEX_URL).decode("utf-8", "replace")
    stems = sorted(set(re.findall(r'href="(\d{4}-[A-Z][a-z]+)\.txt\.gz"', index)))
    print(f"{len(stems)} monthly archives listed")

    for stem in stems:
        dest = os.path.join(OUT_DIR, f"{stem}.mbox")
        if os.path.exists(dest):
            print(f"  {stem}: already present, skipping")
            continue
        url = f"{INDEX_URL}{stem}.txt.gz"
        data = gzip.decompress(fetch(url))
        with open(dest, "wb") as f:
            f.write(data)
        count = data.count(b"\nFrom ") + (1 if data.startswith(b"From ") else 0)
        print(f"  {stem}: {len(data)} bytes, {count} messages")
        time.sleep(1)


if __name__ == "__main__":
    main()
