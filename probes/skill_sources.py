#!/usr/bin/env python3
"""Print what every source a skill cites answers today, with a verdict per URL.

    python3 probes/skill_sources.py
    python3 probes/skill_sources.py --list
    python3 probes/skill_sources.py --url nowhere.invalid --url rauno.me/craft

Rule 9. A cited source is an external interface this repository does not
control. `design-references` cites 28 URLs and `motion` cites five, three of
them the same, and `.claude/skills/` comes to 31 URLs on 28 hosts. The only
thing standing behind any of them is that somebody read it once. A 404 or a
parked domain is what a reader hits, and it is the half of freshness a machine
can check.

Exit status is 1 when a URL is dead, so a scheduled workflow can open an issue
on the output. A host that answers 403 to a script, times out, or redirects
somewhere ambiguous is reported and does not fail: those are guesses, and a
report nobody can act on is worse than the silence it replaced.

Prints. Writes nothing. Standard library, so it runs before the project does.
"""

from __future__ import annotations

import argparse
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SKILLS_DIR = ".claude/skills"

USER_AGENT = "agentkit-skill-sources/1 (+https://github.com/ksallee/agentkit)"
TIMEOUT_SECONDS = 20
MAX_HOPS = 5
BODY_BYTES = 65536
DEFAULT_DELAY_SECONDS = 1.0

ALIVE, CHECK, DEAD = "alive", "check", "dead"

# A host, optionally schemed, optionally with a path. The lookbehind keeps the
# tail of a file path out of the match: in `docs/development/style.md` the `md`
# label follows a slash, and without this every relative link in a skill would
# arrive here as a hostname.
CANDIDATE = re.compile(
    r"(?<![\w/@.:-])"
    r"(?:(?P<scheme>https?)://)?"
    r"(?P<host>[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+)"
    r"(?P<path>/[^\s`)>\"'\]]*)?"
    r"(?![\w-])"
)

# Trailing sentence punctuation is not part of a URL. A closing paren is left
# alone, because a Wikipedia-shaped path carries one.
TRAILING = ".,;:!?'\"`"

# Labels that make the thing around them a filename or an expression rather
# than a host. Every entry came out of a run over these skills, not a guess.
#
# File extensions: `.md`, `.sh` and `.ai` are real top level domains, and
# `STANDARDS.md` is a file. `gates.yml.local` is rejected on `yml`, which is
# why the test reads every label and not only the last one. Reserved names
# resolve nowhere by design, RFC 6761 and RFC 2606. Javascript globals:
# `document.fonts.check` and `document.startViewTransition` are both cited in a
# code span, and `check` is no top level domain today.
#
# A real `example.md` or `document.com` goes with them. Every rejection prints,
# so that stays visible instead of being silently missing.
NOT_A_HOSTNAME = frozenset(
    # File extensions.
    ["css", "htm", "html", "ini", "js", "json", "jsonl", "lock", "md", "mjs"]
    + ["php", "png", "py", "pyc", "rs", "sh", "svg", "toml", "ts", "tsx"]
    + ["txt", "xml", "yaml", "yml"]
    # Reserved names.
    + ["example", "internal", "invalid", "local", "localhost", "test"]
    # Javascript globals.
    + ["console", "document", "navigator", "window"]
)

# What a parked domain says on the page it serves in place of the site. A 200
# carrying one of these is reported rather than failed: the words also appear on
# real pages about domain sales, and a probe cannot tell those apart.
PARKED_MARKERS = (
    "this domain is for sale",
    "buy this domain",
    "the domain name is for sale",
    "domain is parked",
    "parked domain",
    "parkingcrew",
    "sedoparking",
    "hugedomains",
    "afternic",
    "dan.com",
    "godaddy.com/domainsearch",
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Hand every 3xx back as a response, so the probe walks the chain itself.

    urllib follows redirects silently and reports only where it landed. The
    interesting verdict lives in the hop: a redirect to a path is the site
    reorganising, and a redirect to a domain root is the site having lost the
    page.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
        return None


OPENER = urllib.request.build_opener(NoRedirect)


# ---------------------------------------------------------------------------
# Finding the URLs


def markdown_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def looks_like_a_host(host: str) -> bool:
    labels = host.split(".")
    tld = labels[-1]
    return (
        len(tld) >= 2
        and tld.isalpha()
        and not any(label in NOT_A_HOSTNAME for label in labels)
    )


def candidates(text: str) -> list[tuple[int, str, bool]]:
    """Every (line number, URL, kept) the text offers, in the order they appear.

    One pattern covers all three spellings a source arrives in. A bare
    `https://` URL and a markdown link destination both start with the scheme.
    Every source cited in `design-references` and `motion` is spelled without
    one, as a host in an inline code span (`rauno.me/craft`) or in a sentence
    ("the animations.dev course"), so the scheme is optional and the filter
    carries the weight.
    """
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        for match in CANDIDATE.finditer(line):
            host = match.group("host")
            path = (match.group("path") or "").rstrip(TRAILING)
            scheme = match.group("scheme") or "https"
            kept = bool(match.group("scheme")) or looks_like_a_host(host)
            found.append((number, f"{scheme}://{host}{path}", kept))
    return found


def cited(root: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Every URL under a skills root, and every candidate the filter rejected.

    A URL maps to every `file:line` citing it, because the same source is cited
    by two skills and a dead one has to be fixed in both.
    """
    kept: dict[str, list[str]] = {}
    dropped = []
    for path in markdown_files(root):
        where = path.relative_to(root.parent.parent)
        for number, url, keep in candidates(path.read_text(encoding="utf-8", errors="replace")):
            if keep:
                kept.setdefault(url, []).append(f"{where}:{number}")
            else:
                dropped.append(f"{where}:{number}  {url}")
    return kept, dropped


# ---------------------------------------------------------------------------
# Asking each one


def fetch(url: str) -> tuple[int, str, bytes, str]:
    """Status, Location, first bytes of body, and any transport error.

    A failed call reports instead of raising, and the error string separates a
    name that does not resolve from a host that was slow.
    """
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en",
        },
    )
    try:
        with OPENER.open(request, timeout=TIMEOUT_SECONDS) as answer:
            return answer.status, answer.headers.get("Location", ""), answer.read(BODY_BYTES), ""
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location", ""), exc.read(BODY_BYTES), ""
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.gaierror):
            return 0, "", b"", f"name does not resolve ({reason.strerror or reason})"
        return 0, "", b"", str(reason)
    except (TimeoutError, OSError, ValueError) as exc:
        return 0, "", b"", str(exc)


def host_of(url: str) -> str:
    return url.split("://", 1)[-1].split("/", 1)[0]


def path_of(url: str) -> str:
    rest = url.split("://", 1)[-1]
    return rest[len(host_of(url)) :] or "/"


def parked(body: bytes) -> str:
    text = body.decode("utf-8", "replace").lower()
    return next((marker for marker in PARKED_MARKERS if marker in text), "")


def walk(url: str, delay: float, last: dict[str, float]) -> tuple[str, str, list[str], str]:
    """Verdict, one line of detail, the redirect chain, and where it landed.

    The rule this encodes, and what measurement would change it, is in the
    module docstring's exit status paragraph. 404 and a name that does not
    resolve are the two cases where nothing is left to interpret.
    """
    chain = []
    here = url
    for _ in range(MAX_HOPS):
        host = host_of(here)
        wait = delay - (time.monotonic() - last.get(host, -delay))
        if wait > 0:
            time.sleep(wait)
        last[host] = time.monotonic()

        status, location, body, error = fetch(here)
        if error:
            chain.append(f"{here} -> {error}")
            if "resolve" in error:
                return DEAD, error, chain, here
            return CHECK, error, chain, here
        if status in (301, 302, 303, 307, 308) and location:
            landing = absolute(location, here)
            chain.append(f"{status} -> {landing}")
            here = landing
            continue
        chain.append(f"{status} {here}")
        if status in (404, 410):
            return DEAD, f"{status} at {here}", chain, here
        if status >= 400:
            return CHECK, f"{status}, which a browser may not see", chain, here
        marker = parked(body)
        if marker:
            return CHECK, f"200 whose body says {marker!r}", chain, here
        if path_of(url) != "/" and path_of(here) == "/":
            return CHECK, f"landed on the domain root {here}, so the cited page is gone", chain, here
        return ALIVE, f"{status} at {here}", chain, here
    return CHECK, f"more than {MAX_HOPS} redirects", chain, here


def same_page(cited_url: str, landing: str) -> bool:
    """Whether a redirect ended where the citation pointed.

    A `www.` prefix and a trailing slash are one page under two spellings, and
    calling those a move would report a third of the list every run. Anything
    else moved: `github.com/pacocoursey/cmdk` answers 200 at
    `github.com/dip/cmdk`, an account rename the citation knows nothing about,
    and the day GitHub stops redirecting it the link dies with no warning.
    """

    def plain(url: str) -> str:
        rest = url.split("://", 1)[-1].rstrip("/")
        return rest[4:] if rest.startswith("www.") else rest

    return plain(cited_url) == plain(landing)


def absolute(location: str, base: str) -> str:
    """A Location header resolved against the URL it came from.

    `urllib.parse.urljoin` covers this, and it is one import for one call in a
    file that already splits a URL by hand for the host and the path.
    """
    if "://" in location:
        return location
    if location.startswith("//"):
        return base.split(":", 1)[0] + ":" + location
    root = base.split("://", 1)[0] + "://" + host_of(base)
    if location.startswith("/"):
        return root + location
    return root + "/" + location.lstrip("./")


# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe every source a skill cites.")
    ap.add_argument(
        "--skills",
        default=str(Path(__file__).resolve().parent.parent / SKILLS_DIR),
        help=f"Skills root. Default: {SKILLS_DIR} in the repository this probe sits in.",
    )
    ap.add_argument(
        "--url",
        action="append",
        default=[],
        help="Check this URL instead of the skills. Repeatable.",
    )
    ap.add_argument("--list", action="store_true", help="Print what was found and ask nothing.")
    ap.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Seconds between two requests to one host. Default: {DEFAULT_DELAY_SECONDS}.",
    )
    args = ap.parse_args()

    if args.url:
        urls = {u if "://" in u else f"https://{u}": ["--url"] for u in args.url}
        dropped: list[str] = []
        print(f"{len(urls)} URL(s) from the command line")
    else:
        root = Path(args.skills)
        if not root.is_dir():
            sys.exit(f"{root} is not a directory.")
        urls, dropped = cited(root)
        files = len(markdown_files(root))
        print(f"{len(urls)} distinct URL(s) cited by {files} markdown file(s) under {root}")

    print("\nWhat was found, and where it is cited")
    for url, where in sorted(urls.items()):
        print(f"  {url}\n      {'  '.join(where)}")

    print(f"\nCandidates the filter rejected as not a hostname: {len(dropped)}")
    for line in dropped:
        print(f"  {line}")

    if args.list:
        return 0

    print(f"\nWhat each one answers, {args.delay}s between two calls to one host")
    verdicts: dict[str, str] = {}
    landings: dict[str, str] = {}
    last: dict[str, float] = {}
    for url in sorted(urls, key=lambda u: (host_of(u), u)):
        verdict, detail, chain, landing = walk(url, args.delay, last)
        verdicts[url] = verdict
        landings[url] = landing
        print(f"  {verdict:<5}  {url}")
        print(f"         {detail}")
        if len(chain) > 1:
            for hop in chain:
                print(f"           {hop}")

    counts = {name: sum(1 for v in verdicts.values() if v == name) for name in (ALIVE, CHECK, DEAD)}
    print(f"\n{counts[ALIVE]} alive, {counts[CHECK]} to look at, {counts[DEAD]} dead")
    for name in (DEAD, CHECK):
        for url, verdict in sorted(verdicts.items()):
            if verdict == name:
                print(f"  {name:<5}  {url}  cited at {'  '.join(urls[url])}")

    moved = [(u, landings[u]) for u in sorted(urls) if not same_page(u, landings.get(u, u))]
    print(f"\nAlive at a URL the skill does not cite: {len(moved)}")
    for url, landing in moved:
        print(f"  {url}\n      now {landing}, cited at {'  '.join(urls[url])}")
    return 1 if counts[DEAD] else 0


if __name__ == "__main__":
    sys.exit(main())
