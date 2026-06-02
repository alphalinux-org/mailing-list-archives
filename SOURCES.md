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

## axp-list/ (pre-existing Pipermail HTML)
37,389 HTML files, 1995-November through 1999-November.  
Two directory layouts:
- `axp-list/{YEAR}/{Month}{YEAR}/NNNN.html` (1995–1998)
- `axp-list/{Month}{YEAR}/NNNN.html` (1999)

Each file contains original metadata in HTML comments: `received`, `sent`,
`name`, `email`, `subject`, `id` (Message-ID), `inreplyto`.  
The 1999 months overlap with Wayback mbox coverage; Wayback takes priority
there (verified for 1998-March: Wayback is a strict superset of HTML).

## Gmane (news.gmane.io)

### gmane.linux.redhat.axp.general (7,152 articles)
Date range: March 2002 – June 2015.  
Fully covered by Wayback mbox — no new data.

### gmane.linux.redhat.axp.kernel (137 articles)
Date range: April 2002 – September 2003.  
Separate kernel sub-list, not present in any other source.  
**Script:** `fetch-gmane-mbox.py`  
**Output:** `axp-list-mbox/axp-kernel-YYYY-Month.mbox` (15 files)

## Sources not used

### marc.info (axp-redhat list)
Script `fetch-marc-mbox.py` written and ready. Covers 1995-November through
1999-June, ~13,181 messages. Headers are reconstructed (no original
Message-ID). All months have data from higher-quality sources, so this
scrape has not been run.

## Coverage summary

| Period | Source | Quality |
|--------|--------|---------|
| pre-1995-Nov | Unknown | — |
| 1995-Nov – 1998-Feb | HTML → mbox | Good (original Message-IDs) |
| 1998-Mar – 2022-Apr | Wayback Machine | Lossless |
| 2002-Apr – 2003-Sep | gmane.linux.redhat.axp.kernel | Good (full headers) |
