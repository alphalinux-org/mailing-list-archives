# Alpha mailing list archives

Mail and Usenet archives about DEC Alpha systems, gathered from wherever
copies survived: the Wayback Machine, Pipermail and MHonArc HTML, marc.info,
Gmane, public-inbox mirrors, and the archive.org Usenet collections.

The Red Hat axp-list was the starting point. The collection now also covers
the smaller alphalinux.org lists, the Debian, FreeBSD, NetBSD, OpenBSD and
Gentoo Alpha port lists, AlphaNT, tru64-unix-managers, and newsgroups such as
comp.os.linux.alpha, comp.sys.dec, comp.sys.vms and comp.unix.tru64.

## Layout

Each list has a `<list>-mbox/` directory with one mbox file per month, named
`YYYY-Month.mbox`. Some files carry a prefix naming their source or sub-list,
such as `googlegroups-` for the Usenet groups or `axp-kernel-` for the axp-kernel
list inside `axp-list-mbox/`.

The Python scripts at the top level fetch or convert one source each. Most
start with `fetch-` (download) or `html-to-mbox-` (convert scraped HTML). A few
one-off scripts repair specific problems in the debian-alpha archive.
`verify-mbox.py` re-downloads the axp-list files from the Wayback Machine and
checks them against the stored copies.

Download caches live in dot-directories and are not tracked.

## Sources

`SOURCES.md` records, for every list and date range, where the messages came
from, which script produced them, and how faithful the result is. Where a
source only offered HTML, headers had to be rebuilt and some are incomplete;
those ranges are marked "Reconstructed". It also lists the sources that were
checked and rejected, and the known gaps.
