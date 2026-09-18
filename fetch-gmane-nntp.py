#!/usr/bin/env python3
"""Fetch a mailing list from Gmane via NNTP into per-month mbox files.

Gmane carries full headers (Message-ID, References, To/Cc), unlike marc.info
and the Pipermail/mail-index HTML archives.  Output is
<out-dir>/gmane-YYYY-Month.mbox; public-inbox deduplicates by Message-ID on
import.

Articles are cached one file per article under .gmane-cache/<group>/ so the
fetch can be resumed: Gmane drops the connection regularly on long runs.

nntplib was removed in Python 3.13, so this speaks NNTP over a plain socket.

Usage: fetch-gmane-nntp.py <group> <out-dir>
"""
import datetime
import email.utils
import os
import socket
import sys
import time

SERVER = "news.gmane.io"

# Sanity window for Date: headers; anything outside is treated as bogus.
MIN_YEAR = 1990
MAX_YEAR = datetime.date.today().year + 1

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class NNTP:
    def __init__(self, host, group):
        self.host, self.group = host, group
        self.connect()

    def connect(self):
        self.sock = socket.create_connection((self.host, 119), 30)
        self.sock.settimeout(60)
        self.f = self.sock.makefile("rb")
        self.f.readline()
        resp = self.cmd(f"GROUP {self.group}")
        if not resp.startswith("211"):
            raise RuntimeError(f"GROUP failed: {resp}")
        return resp

    def reconnect(self):
        try:
            self.sock.close()
        except OSError:
            pass
        time.sleep(5)
        return self.connect()

    def cmd(self, line):
        self.sock.sendall(line.encode() + b"\r\n")
        resp = self.f.readline()
        if not resp:
            raise ConnectionError("server closed connection")
        return resp.decode("utf-8", "replace").strip()

    def body(self):
        """Read a dot-terminated multi-line response as raw bytes."""
        out = []
        while True:
            line = self.f.readline()
            if not line:
                raise ConnectionError("server closed connection mid-article")
            if line in (b".\r\n", b".\n"):
                break
            if line.startswith(b".."):
                line = line[1:]
            out.append(line.replace(b"\r\n", b"\n"))
        return b"".join(out)

    def quit(self):
        try:
            self.cmd("QUIT")
            self.sock.close()
        except OSError:
            pass


def header(article, name):
    """Return the (unfolded) value of a header, or None."""
    want = name.lower().encode()
    lines = article.split(b"\n")
    for i, line in enumerate(lines):
        if not line.strip():
            break
        if line[:1] in (b" ", b"\t"):
            continue
        key, _, value = line.partition(b":")
        if key.strip().lower() != want:
            continue
        for cont in lines[i + 1:]:
            if cont[:1] not in (b" ", b"\t"):
                break
            value += b" " + cont.strip()
        return value.decode("utf-8", "replace").strip()
    return None


def message_date(article):
    """Best-effort date: Date:, else the oldest Received:, else None."""
    value = header(article, "Date")
    if value:
        try:
            date = email.utils.parsedate_to_datetime(value)
            if MIN_YEAR <= date.year <= MAX_YEAR:
                return date
        except (TypeError, ValueError):
            pass
    received = header(article, "Received")
    if received and ";" in received:
        try:
            date = email.utils.parsedate_to_datetime(received.rsplit(";", 1)[1].strip())
            if MIN_YEAR <= date.year <= MAX_YEAR:
                return date
        except (TypeError, ValueError):
            pass
    # Gmane's own injection time: last resort, and the only date some spam has
    posting = header(article, "NNTP-Posting-Date")
    if posting:
        try:
            date = email.utils.parsedate_to_datetime(posting.split("(")[0].strip())
            if MIN_YEAR <= date.year <= MAX_YEAR:
                return date
        except (TypeError, ValueError):
            pass
    return None


def from_line(article, date):
    sender = "unknown"
    value = header(article, "From")
    if value:
        addrs = email.utils.getaddresses([value])
        if addrs and addrs[0][1]:
            sender = addrs[0][1]
    stamp = date.strftime("%a %b %e %H:%M:%S %Y").replace("  ", " ")
    return f"From {sender}  {stamp}\n".encode("utf-8", "replace")


def fetch_all(nntp, first, last):
    """Fetch every article into the cache, resuming and reconnecting as needed."""
    missing = []
    for num in range(first, last + 1):
        path = os.path.join(CACHE_DIR, f"{num}")
        if os.path.exists(path) or os.path.exists(path + ".gone"):
            continue
        for attempt in range(5):
            try:
                resp = nntp.cmd(f"ARTICLE {num}")
                if resp.startswith("220"):
                    data = nntp.body()
                    with open(path, "wb") as f:
                        f.write(data)
                elif resp[:1] in ("4", "5"):
                    # 423/430: article genuinely absent (Gmane removes spam)
                    open(path + ".gone", "wb").close()
                    missing.append(num)
                else:
                    raise RuntimeError(f"unexpected response {resp}")
                break
            except (ConnectionError, OSError, RuntimeError) as e:
                print(f"  article {num}: {e}; reconnecting (attempt {attempt + 1})")
                time.sleep(5 * (attempt + 1))
                nntp.reconnect()
        else:
            raise SystemExit(f"giving up on article {num}")
        if num % 500 == 0:
            print(f"  ...{num}")
    return missing


def main():
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {os.path.basename(sys.argv[0])} <group> <out-dir>")
    group, out_dir = sys.argv[1], sys.argv[2]
    global GROUP, OUT_DIR, CACHE_DIR
    GROUP = group
    OUT_DIR = out_dir if os.path.isabs(out_dir) else os.path.join(os.path.dirname(__file__), out_dir)
    CACHE_DIR = os.path.join(os.path.dirname(__file__), ".gmane-cache", GROUP)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    nntp = NNTP(SERVER, GROUP)
    resp = nntp.cmd(f"GROUP {GROUP}")
    _, count, first, last, _ = resp.split()
    first, last = int(first), int(last)
    print(f"{GROUP}: {count} articles, {first}-{last}")

    missing = fetch_all(nntp, first, last)
    nntp.quit()
    print(f"{len(missing)} articles absent from the server")

    months = {}
    undated = []
    for num in range(first, last + 1):
        path = os.path.join(CACHE_DIR, f"{num}")
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            article = f.read()
        date = message_date(article)
        if date is None:
            undated.append(num)
            continue
        escaped = b"\n".join(
            b">" + line if line.startswith(b"From ") else line
            for line in article.split(b"\n")
        )
        months.setdefault((date.year, date.month), []).append(
            from_line(article, date) + escaped + b"\n"
        )

    total = 0
    for (year, month), messages in sorted(months.items()):
        path = os.path.join(OUT_DIR, f"gmane-{year}-{MONTH_NAMES[month]}.mbox")
        with open(path, "wb") as f:
            f.write(b"".join(messages))
        total += len(messages)
        print(f"  {os.path.basename(path)}: {len(messages)} messages")
    print(f"{total} messages written")
    if undated:
        print(f"{len(undated)} articles had no usable date: {undated[:20]}")


if __name__ == "__main__":
    main()
