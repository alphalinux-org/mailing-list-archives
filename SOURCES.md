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

## Coverage summary

| Period | List | Source | Quality |
|--------|------|--------|---------|
| pre-1995-Nov | axp-list | Unknown | — |
| 1995-Nov – 1998-Feb | axp-list | HTML → mbox | Good (original Message-IDs) |
| 1998-Mar – 2022-Apr | axp-list | Wayback Machine | Lossless |
| pre-2002 | axp-kernel-list | Not found | — |
| 2002-Apr – 2003-Sep | axp-kernel-list | Gmane | Good (full headers) |
