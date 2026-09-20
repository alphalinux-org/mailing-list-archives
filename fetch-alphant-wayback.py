#!/usr/bin/env python3
"""Download alphant (AlphaNT mail list) message HTML from the Wayback Machine.

Two eras, two archive software packages:

  1. Hypermail at dutlbcz.lr.tudelft.nl/alphant/maillist/archives/{1995Q4,
     1996Q1,1996Q2,current}/NNNN.html -- the original 1995-1996 archive,
     mirrored at TU Delft.
  2. MHonArc at www.alphant.com/archives/alphant/YYYY-MM[-W]/msgNNNNN.html --
     the Lizon Corporation era, October 1998 through November 2000. Most of
     this was never crawled before the site died; only a few hundred
     messages survive.

Output: alphant/<era-dir>/<file>.html, one directory per archive period.
"""

import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "alphant")

CDX = "https://web.archive.org/cdx/search/cdx"

SOURCES = [
    # (label, CDX url prefix, regex over the original URL -> (dir, file))
    (
        "hypermail",
        "dutlbcz.lr.tudelft.nl/alphant/maillist/archives/",
        re.compile(r"/archives/([^/]+)/(\d+\.html)$", re.IGNORECASE),
    ),
    (
        "mhonarc",
        "www.alphant.com/archives/alphant/",
        re.compile(r"/alphant/([\d-]+)/(msg\d+\.html)$", re.IGNORECASE),
    ),
]

USER_AGENT = "alphant-archiver/1.0"


def fetch_cdx(prefix):
    url = (
        f"{CDX}?url={urllib.parse.quote(prefix)}&matchType=prefix"
        "&filter=statuscode:200&fl=timestamp,original&output=text"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                lines = r.read().decode().splitlines()
            if lines:
                return [l.split() for l in lines if l.strip()]
        except Exception as e:
            print(f"  CDX retry({attempt + 1}): {e}", file=sys.stderr)
        time.sleep(5 * (attempt + 1))
    return []


def download(timestamp, original, dest):
    # id_ returns the raw stored bytes (if_ rewrites links and injects a banner)
    url = f"https://web.archive.org/web/{timestamp}id_/{original}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # url path -> (timestamp, original). Later captures win: the archive was
    # static, and a later capture is more likely to be complete.
    wanted = {}
    for label, prefix, pat in SOURCES:
        print(f"CDX: {label} ...", flush=True)
        rows = fetch_cdx(prefix)
        print(f"  {len(rows)} captures")
        for timestamp, original in rows:
            m = pat.search(original)
            if not m:
                continue
            # The Delft site served both /alphant/ and /AlphaNT/; fold case so
            # the two spellings do not produce duplicate files.
            key = (m.group(1).lower(), m.group(2).lower())
            prev = wanted.get(key)
            if prev is None or timestamp > prev[0]:
                wanted[key] = (timestamp, original)

    print(f"\n{len(wanted)} unique messages")

    done = failed = 0
    for (subdir, name), (timestamp, original) in sorted(wanted.items()):
        dest_dir = os.path.join(OUT_DIR, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, name)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            done += 1
            continue

        delay = 3
        for attempt in range(5):
            try:
                size = download(timestamp, original, dest)
                print(f"  {subdir}/{name} {size:,} bytes", flush=True)
                done += 1
                break
            except Exception as e:
                if os.path.exists(dest):
                    os.unlink(dest)
                if attempt == 4:
                    print(f"  {subdir}/{name} FAILED: {e}", file=sys.stderr)
                    failed += 1
                else:
                    time.sleep(delay)
                    delay *= 2
        time.sleep(0.5)

    print(f"\nDone: {done} files, {failed} failed")


if __name__ == "__main__":
    main()
