# axp-list archive — data sources

## axp-list-mbox/ (assembled mbox archive)

### 1995-November through 1998-February (28 months, 18,335 messages)
**Source:** Pipermail HTML files in `axp-list/`  
**Script:** `html-to-mbox.py`  
**Quality:** Good — original Message-IDs preserved where present (some early
messages have empty `id` comment). In-Reply-To validated against
`token@domain` pattern; garbage values dropped.

### 1998-March through 2022-April (154 months)
**Source:** Wayback Machine  
**Script:** `fetch-wayback-mbox.py`  
**URLs:** Two crawls used:
- `listman.redhat.com` (2023 crawl) — primary
- `www.redhat.com` (2019 crawl) — fallback for months missing from primary  

**Quality:** Lossless — original mbox files as served by listman.redhat.com,
full headers intact. All 154 files SHA256-verified against fresh re-download.  
**Key detail:** Wayback `id_` modifier used (not `if_`) — `if_` decodes
Content-Encoding and truncates files.

### axp-kernel sub-list: April 2002 – September 2003 (15 months, 137 messages)
**Source:** Gmane (news.gmane.io), group `gmane.linux.redhat.axp.kernel`  
**Script:** `fetch-gmane-mbox.py`  
**Output:** `axp-list-mbox/axp-kernel-YYYY-Month.mbox`  
This kernel-specific sub-list is absent from all other sources.

## axp-list/ (pre-existing Pipermail HTML)
37,389 HTML files, 1995-November through 1999-November.  
Two directory layouts:
- `axp-list/{YEAR}/{Month}{YEAR}/NNNN.html` (1995–1998)
- `axp-list/{Month}{YEAR}/NNNN.html` (1999)

Each file contains original metadata in HTML comments: `received`, `sent`,
`name`, `email`, `subject`, `id` (Message-ID), `inreplyto`.  
The 1999 months overlap with Wayback mbox coverage; Wayback takes priority
(verified for 1998-March: Wayback is a strict superset of HTML).

## axp-hardware (separate list)

Hardware-focused sub-list hosted on lists.alphalinux.org, distinct from axp-list.

### December 1999 – September 2001 (21 months, 249 messages) — primary
**Source:** Pipermail shtml files in `axp-hardware/`  
**Script:** `html-to-mbox-hardware.py`  
**Output:** `axp-hardware-mbox/YYYY-Month.mbox`  
**Quality:** Good — all 249 files have original Message-IDs.

### May 2000 – August 2001 (113 messages) — supplementary
**Source:** Wayback Machine full-archive mbox  
**URL:** `http://lists.alphalinux.org/pipermail/axp-hardware.mbox/axp-hardware.mbox`  
**Capture used:** 20011104 (two captures exist: 20011104, 20020120 — identical content)  
**Output:** `axp-hardware.mbox`  
Subset of HTML coverage (113 vs 249 messages); retained for the 2 messages
not present in HTML. public-inbox deduplicates by Message-ID on import.

## axp-software (separate list)

### December 1999 – September 2001 (19 months, 116 messages)
**Source:** Pipermail shtml files in `axp-software/`  
**Script:** `html-to-mbox-hardware.py axp-software`  
**Output:** `axp-software-mbox/YYYY-Month.mbox`  
**Quality:** Good — all files have original Message-IDs.  
No Wayback mbox capture exists for this list.

## cooker-axp (separate list)

### July 2000 – November 2001 (12 months, 110 messages)
**Source:** Pipermail shtml files in `cooker-axp/`  
**Script:** `html-to-mbox-hardware.py cooker-axp`  
**Output:** `cooker-axp-mbox/YYYY-Month.mbox`  
**Quality:** Good — all files have original Message-IDs.  
Mandrake Linux Cooker Alpha port list. Messages in `cooker-axp/2001/` (flat
year dir, no month subdirs) were bucketed by Date header.

## milo-list (separate list)

### April 1999 – November 2001 (29 months, 89 messages)
**Source:** HTML files in `milo-list/`  
**Script:** `html-to-mbox-hardware.py milo-list`  
**Output:** `milo-list-mbox/YYYY-Month.mbox`  
**Quality:** Good — all files have original Message-IDs.  
MILO (Mini Loader for Alpha) development list, hosted on alphalinux.org
(talisman.mv.com). Bare year directory layout (1999/, 2000/, 2001/) with
no month subdirs; messages bucketed by Date header. One message has a
malformed sent date (year 100); correctly placed via received date fallback.  
No Wayback mbox, not on marc.info, not on Gmane.

## high_perf (separate list)

### November 1998 – November 2001 (27 months, 152 messages)
**Source:** HTML files in `high_perf/`  
**Script:** `html-to-mbox-hardware.py high_perf`  
**Output:** `high_perf-mbox/YYYY-Month.mbox`  
**Quality:** Good — all files have original Message-IDs.  
High Performance Alpha Linux list, hosted on alphalinux.org. Mixed
directory layout: `Month{YEAR}` dirs (some lowercase) plus bare `2000/`
and `2001/` year dirs.

## debian-alpha (Debian Alpha port mailing list)

List still active at lists.debian.org/debian-alpha/. No pre-built mbox
downloads available — archives served as per-message MHonArc HTML only.

### 1995-November (1 month, 0 messages)
**Source:** lists.debian.org HTML  
**Script:** `fetch-debian-alpha-html.py`  
No messages archived for this month on the live site.

### 1996-January – 1998-December (partial months, ~2,900 messages)
**Source:** lists.debian.org HTML  
**Script:** `fetch-debian-alpha-html.py`  
**Output:** `debian-alpha-mbox/YYYY-Month.mbox`  
Not all months exist (list was low-traffic early on).  
**Quality:** Reconstructed from MHonArc HTML. Two formats encountered:
- Old format: `<!-- received="" sent="" name="" email="" subject="" id="" -->` comments
- New format: `<!--X-Subject: -->`, `<!--X-Date: -->`, `<!--X-Message-Id: -->` with
  headers parsed from `<!--X-Head-of-Message-->` `<ul>` block

### 1999-January – 2001-September (32 months, 5,918 messages)
**Source:** Local MHonArc HTML files in `debian-alpha/`  
**Script:** `html-to-mbox-debian-alpha.py`  
**Output:** `debian-alpha-mbox/YYYY-Month.mbox`  
**Quality:** Good — original Message-IDs and In-Reply-To preserved.

### 2001-October – 2002-February (5 months, ~571 messages)
**Source:** lists.debian.org HTML  
**Script:** `fetch-debian-alpha-html.py`  
**Output:** `debian-alpha-mbox/YYYY-Month.mbox`

### 2002-March – 2026-May (10,192 messages)
**Source:** Gmane (news.gmane.io), group `gmane.linux.debian.ports.alpha`  
**Script:** `fetch-debian-alpha-mbox.py` (NNTP via python3.12 nntplib)  
**Output:** `debian-alpha-mbox/YYYY-Month.mbox`  
**Quality:** Good — full RFC 2822 headers intact.  
Note: Gmane had sparse coverage before March 2002; a handful of articles
had malformed dates (one spam with fake 1997 date — replaced with real data).

## freebsd-alpha (separate list)

FreeBSD's Alpha port list, `freebsd-alpha@freebsd.org`, retired in
November 2010.

### 1998-January – 2002-February (49 months, 9,986 messages)
**Source:** marc.info, list `freebsd-alpha`
**Script:** `fetch-marc-list.py freebsd-alpha freebsd-alpha-mbox 199801 200202`
**Output:** `freebsd-alpha-mbox/YYYY-Month.mbox`
**Quality:** Reconstructed — marc.info supplies no Message-ID and no
In-Reply-To, and obfuscates addresses (`user () host ! com`). No other
source covers these years.
**Key detail:** marc.info month listings show thread *heads* only, so each
thread has to be expanded (`?t=<tid>&r=N&w=2`) and both views paginate 30
rows at a time. Collecting only the month listing's links yields roughly a
quarter of the messages. `fetch-marc-mbox.py` (the earlier axp-redhat
script, never used for archived data) has this bug; `fetch-marc-list.py`
does not.

### 2002-March – 2010-December (106 months, 6,278 messages)
**Source:** Gmane (news.gmane.io), group `gmane.os.freebsd.devel.alpha`
**Script:** `fetch-gmane-nntp.py gmane.os.freebsd.devel.alpha freebsd-alpha-mbox`
**Output:** `freebsd-alpha-mbox/gmane-YYYY-Month.mbox`
**Quality:** Good — full headers, including Message-ID and References.
Every article in the group (1–6308, 30 absent server-side) was retrieved.

### 2003-March – 2010-December (94 months, 3,781 messages)
**Source:** Pipermail at `https://lists.freebsd.org/pipermail/freebsd-alpha/`
**Script:** `fetch-freebsd-alpha-mbox.py`
**Output:** `freebsd-alpha-mbox/YYYY-Month.mbox`
**Quality:** Good — original Message-IDs, but Pipermail obscures addresses
(`user at host`). Fully overlapped by the Gmane copy; both are kept because
public-inbox deduplicates by Message-ID, and each fills small holes in the
other.

## port-alpha (NetBSD)

`port-alpha@netbsd.org`, still active.

### 1996-January – 2002-February (73 months, 10,587 messages)
**Source:** mail-index.netbsd.org (NetBSD's official archive)
**Script:** `fetch-netbsd-mailindex.py port-alpha netbsd-port-alpha-mbox 199601 200112`
(plus a second run for `200202`, the one month Gmane skips)
**Output:** `netbsd-port-alpha-mbox/YYYY-Month.mbox`
**Quality:** Reconstructed — message pages carry only Subject/To/From/Date;
no Message-ID, no In-Reply-To. Dates are UTC, `MM/DD/YYYY HH:MM:SS`.
Every message linked from every month index parsed cleanly.

### 2002-January – 2026-August (223 months, 5,491 messages)
**Source:** Gmane (news.gmane.io), group `gmane.os.netbsd.ports.alpha`
**Script:** `fetch-gmane-nntp.py gmane.os.netbsd.ports.alpha netbsd-port-alpha-mbox`
**Output:** `netbsd-port-alpha-mbox/gmane-YYYY-Month.mbox`
**Quality:** Good — full headers.

marc.info also carries this list (1997-11 onwards, 13,156 messages) but was
not used: mail-index reaches back further (1996-01), is NetBSD's own
archive, and neither source has Message-IDs, so mixing them would produce
undeduplicatable duplicates. Gmane is 370 messages short of marc.info
across 46 months in 2002–2026; those gaps were left rather than filled with
header-stripped copies that public-inbox cannot deduplicate against.

## openbsd-alpha (OpenBSD)

`alpha@openbsd.org`, archived officially on marc.info.

### 2001-September – 2026-February (147 months, 1,061 messages)
**Source:** marc.info, list `openbsd-alpha`
**Script:** `fetch-marc-list.py openbsd-alpha openbsd-alpha-mbox 200109 202602`
**Output:** `openbsd-alpha-mbox/YYYY-Month.mbox`
**Quality:** Reconstructed — no Message-ID, obfuscated addresses.

### 2026-September (1 message)
**Source:** Gmane (news.gmane.io), group `gmane.os.openbsd.alpha`
**Script:** `fetch-gmane-nntp.py gmane.os.openbsd.alpha openbsd-alpha-mbox`
**Output:** `openbsd-alpha-mbox/gmane-YYYY-Month.mbox`

Gmane carries 472 messages for this list with full headers, but marc.info
has 1,061 over the same span. Since marc.info messages have no Message-ID,
the two cannot be deduplicated against each other, so marc.info was kept
for every month it covers and the Gmane copies of those months were
deleted; only 2026-September, which marc.info lacks, comes from Gmane.
The full Gmane fetch is reproducible from the script if the trade-off is
ever revisited.

## Sources investigated, not used

### marc.info — axp-redhat list
Covers 1995-November through 1999-June, ~13,181 messages. Headers
reconstructed (no original Message-ID). All months covered by higher-quality
sources; not fetched.

### marc.info — axp-list, axp-kernel-list
Neither list is indexed on marc.info ("No such list").

### Gmane — gmane.linux.redhat.axp.general (7,152 articles, Mar 2002 – Jun 2015)
Fully covered by Wayback mbox; no new data.

### lore.kernel.org — linux-alpha@vger.kernel.org
14,923 messages, April 2002 – present. This is the upstream vger kernel
Alpha list, distinct from Red Hat's axp-list/axp-kernel-list. Starts too
late to fill any gaps. Not fetched.

### marc.info — linux-alpha@vger.kernel.org
May 1998 – present. Same vger list as lore, different archive. Predates
lore's coverage by ~4 years, but is still a different list from axp-kernel-list.
Not fetched.

### axp-kernel-list (Red Hat, pre-2002)
Referenced in external archives by September 1998. Checked Wayback Machine
(nothing), marc.info (not indexed), Gmane (starts April 2002 only). No
pre-2002 archive found anywhere. Headers in the Gmane messages contain
`List-Archive: <https://listman.redhat.com/mailman/private/axp-kernel-list/>`
— it was a **private** Mailman list. Pre-2002 content is almost certainly
gone unless someone retained personal copies.

## Usenet groups (comp.os.linux.alpha, comp.sys.dec, comp.sys.vms, comp.unix.tru64, comp.os.linux.announce)

Real Usenet, not mailing lists. Gmane does not carry these (it mirrors
mailing lists via NNTP, not the comp.* hierarchy). Eternal September has
live/recent feed only (0-93 articles per group, no comp.sys.vms at all) —
useless for archival purposes.

**Source:** Internet Archive `usenet-comp` collection
(`https://archive.org/download/usenet-comp/<group>.mbox.zip`), a Google
Groups/Deja News mbox dump.  
**Script:** `fetch-usenet-archive-mbox.py <group> <out-dir>`  
**Output:** `<out-dir>/googlegroups-YYYY-Month.mbox`

**Quality:** Good, with caveats.
- These dumps use `From <deja-id>` separator lines (a bare, possibly
  negative integer) instead of a real sender+date. Plain body text lines
  starting with "From " are common and are NOT escaped in the source
  dump — splitting naively on any `^From ` line corrupts messages. The
  script requires the numeric-ID pattern to recognize a real separator.
- No reliable sender/date in the separator line, so messages are bucketed
  by the `Date:` header, which is present but highly irregular (RFC822
  variants, bare `YYYY/MM/DD` for comp.sys.vms, occasional prose dates).
  Unparseable dates go to `googlegroups-undated.mbox` for manual triage.
- Message-ID present on most but not all messages (~1% missing in
  comp.sys.dec).

**Coverage and undated fraction:**
| Group | Months | Messages | Undated |
|-------|--------|----------|---------|
| comp.os.linux.alpha | 1997-Aug – 2013-May | 29,127 | 0 |
| comp.sys.dec | 1990-Apr – 2013-May | 108,195 | 2,274 (~2%) |
| comp.sys.vms | 1990-Jan – 2004-Sep | 876 | 7 |
| comp.unix.tru64 | 2000-Apr – 2013-Mar | 14,500 | 0 |
| comp.os.linux.announce | 1993-Apr – 2013-May | 13,052 | 0 |

## Coverage summary

| Period | List | Source | Quality |
|--------|------|--------|---------|
| pre-1995-Nov | axp-list | Unknown | — |
| 1995-Nov – 1998-Feb | axp-list | HTML → mbox | Good (original Message-IDs) |
| 1998-Mar – 2022-Apr | axp-list | Wayback Machine | Lossless |
| pre-2002 | axp-kernel-list | Not found | — |
| 2002-Apr – 2003-Sep | axp-kernel-list | Gmane | Good (full headers) |
| 1999-Dec – 2001-Sep | axp-hardware | HTML → mbox + Wayback | Good |
| 1999-Dec – 2001-Sep | axp-software | HTML → mbox | Good |
| 2000-Jul – 2001-Nov | cooker-axp | HTML → mbox | Good |
| 1999-Apr – 2001-Nov | milo-list | HTML → mbox | Good |
| 1998-Nov – 2001-Nov | high_perf | HTML → mbox | Good |
| 1995-Nov – 1998-Dec | debian-alpha | lists.debian.org HTML → mbox | Reconstructed |
| 1999-Jan – 2001-Sep | debian-alpha | Local HTML → mbox | Good |
| 2001-Oct – 2002-Feb | debian-alpha | lists.debian.org HTML → mbox | Reconstructed |
| 2002-Mar – 2026-May | debian-alpha | Gmane NNTP | Good (full headers) |
| 1998-Jan – 2002-Feb | freebsd-alpha | marc.info | Reconstructed |
| 2002-Mar – 2010-Dec | freebsd-alpha | Gmane NNTP | Good (full headers) |
| 2003-Mar – 2010-Dec | freebsd-alpha | lists.freebsd.org Pipermail | Good |
| 1996-Jan – 2002-Feb | port-alpha (NetBSD) | mail-index.netbsd.org | Reconstructed |
| 2002-Jan – 2026-Aug | port-alpha (NetBSD) | Gmane NNTP | Good (full headers) |
| 2001-Sep – 2026-Feb | openbsd-alpha | marc.info | Reconstructed |
| 1997-Aug – 2013-May | comp.os.linux.alpha | archive.org usenet-comp | Good |
| 1990-Apr – 2013-May | comp.sys.dec | archive.org usenet-comp | Good (~2% undated) |
| 1990-Jan – 2004-Sep | comp.sys.vms | archive.org usenet-comp | Good |
| 2000-Apr – 2013-Mar | comp.unix.tru64 | archive.org usenet-comp | Good |
| 1993-Apr – 2013-May | comp.os.linux.announce | archive.org usenet-comp | Good |
