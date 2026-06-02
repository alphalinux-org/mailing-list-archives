#!/usr/bin/env python3
"""Re-download every mbox from Wayback, decompress, compare SHA256 to stored."""

import gzip, hashlib, os, time, urllib.request

CDX_SOURCES = [
    (
        "https://web.archive.org/cdx/search/cdx"
        "?url=listman.redhat.com/archives/axp-list/"
        "&matchType=prefix&output=text&fl=timestamp,original"
        "&filter=original:.*\\.txt\\.gz&collapse=original"
    ),
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


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_decompress(timestamp, original):
    url = f"https://web.archive.org/web/{timestamp}id_/{original}"
    req = urllib.request.Request(url, headers={"User-Agent": "axp-list-verifier/1.0"})
    delay = 3
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if data[:2] == b"\x1f\x8b":
                return gzip.decompress(data)
            return data
        except Exception as e:
            if attempt == 5:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def main():
    seen = {}
    for cdx_url in CDX_SOURCES:
        for timestamp, original in fetch_cdx(cdx_url):
            stem = original.rsplit("/", 1)[-1][: -len(".txt.gz")]
            if stem not in seen:
                seen[stem] = (timestamp, original)

    ok = fail = missing = 0
    for stem, (timestamp, original) in sorted(seen.items()):
        mbox_path = os.path.join(OUT_DIR, stem + ".mbox")
        if not os.path.exists(mbox_path):
            print(f"MISSING  {stem}")
            missing += 1
            continue

        stored_hash = sha256(mbox_path)
        stored_size = os.path.getsize(mbox_path)

        print(f"  {stem} ... ", end="", flush=True)
        try:
            fresh = download_decompress(timestamp, original)
            fresh_hash = hashlib.sha256(fresh).hexdigest()
            if fresh_hash == stored_hash:
                print(f"OK ({stored_size:,} bytes)")
                ok += 1
            else:
                print(f"MISMATCH stored={stored_size:,} fresh={len(fresh):,}")
                print(f"    stored: {stored_hash}")
                print(f"    fresh:  {fresh_hash}")
                fail += 1
        except Exception as e:
            print(f"DOWNLOAD ERROR: {e}")
            fail += 1

        time.sleep(2)

    print(f"\n{ok} OK  {fail} FAIL  {missing} MISSING  (of {len(seen)} total)")


if __name__ == "__main__":
    main()
