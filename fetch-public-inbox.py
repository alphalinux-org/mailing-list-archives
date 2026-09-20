#!/usr/bin/env python3
"""Mirror a public-inbox archive and split it into monthly mbox files.

Usage: fetch-public-inbox.py <inbox-url> <out-dir> [cache-dir]

A public-inbox v2 archive is served as one or more git repositories ("epochs")
numbered 0, 1, ... under the inbox URL. Every commit adds one blob named `m`
holding the raw RFC 822 message. This mirrors each epoch that exists and writes
`YYYY-Month.mbox` files keyed off each message's Date: header.
"""

import email.utils
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def epoch_exists(base, n):
    url = f"{base}/{n}/info/refs?service=git-upload-pack"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False


def mirror(base, n, cache_dir):
    repo = os.path.join(cache_dir, f"{n}.git")
    if os.path.exists(repo):
        subprocess.run(["git", "--git-dir", repo, "fetch", "-q", "--all"],
                       check=True)
    else:
        subprocess.run(["git", "clone", "--mirror", "-q", f"{base}/{n}", repo],
                       check=True)
    return repo


def messages(repo):
    """Yield the raw message blob of every commit in the repo."""
    revs = subprocess.run(["git", "--git-dir", repo, "rev-list", "--all"],
                          check=True, capture_output=True).stdout.split()
    for rev in revs:
        rev = rev.decode()
        blob = subprocess.run(["git", "--git-dir", repo, "cat-file", "blob",
                               f"{rev}:m"], capture_output=True)
        if blob.returncode == 0 and blob.stdout:
            yield blob.stdout


def message_date(raw):
    for line in raw.split(b"\n"):
        if not line.strip():
            break
        if line[:5].lower() == b"date:":
            try:
                d = email.utils.parsedate_to_datetime(
                    line[5:].decode("utf-8", "replace").strip())
            except (TypeError, ValueError):
                return None
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d.astimezone(timezone.utc)
    return None


def envelope(raw, date):
    sender = "nobody"
    for line in raw.split(b"\n"):
        if not line.strip():
            break
        if line[:5].lower() == b"from:":
            addr = email.utils.parseaddr(
                line[5:].decode("utf-8", "replace"))[1]
            if addr:
                sender = addr
            break
    stamp = date.strftime("%a %b %e %H:%M:%S %Y")
    return f"From {sender} {stamp}\n".encode()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    base = sys.argv[1].rstrip("/")
    out_dir = sys.argv[2]
    cache_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".public-inbox-cache",
        os.path.basename(base))

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    by_month = defaultdict(list)
    undated = 0
    total = 0
    n = 0
    while epoch_exists(base, n):
        repo = mirror(base, n, cache_dir)
        count = 0
        for raw in messages(repo):
            total += 1
            count += 1
            date = message_date(raw)
            if date is None:
                undated += 1
                continue
            if not raw.endswith(b"\n"):
                raw += b"\n"
            body = raw.replace(b"\nFrom ", b"\n>From ")
            by_month[(date.year, date.month)].append(
                (date, envelope(raw, date) + body))
        print(f"epoch {n}: {count} messages")
        n += 1

    if n == 0:
        sys.exit(f"no epochs found under {base}")

    for (year, month), msgs in sorted(by_month.items()):
        msgs.sort(key=lambda m: m[0])
        path = os.path.join(out_dir, f"{year}-{MONTHS[month - 1]}.mbox")
        with open(path, "wb") as f:
            for _, raw in msgs:
                f.write(raw)
                if not raw.endswith(b"\n\n"):
                    f.write(b"\n")
        print(f"  {os.path.basename(path)}: {len(msgs)} messages")

    print(f"{total} messages, {len(by_month)} months, {undated} undated "
          f"(skipped)")


if __name__ == "__main__":
    main()
