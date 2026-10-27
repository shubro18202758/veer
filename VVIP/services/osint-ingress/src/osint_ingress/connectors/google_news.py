"""Google News RSS search (``google_news_rss``, OSINT_SOURCES.md §2): a discovery / pointer layer.

* One search feed for Ahmedabad incident terms (the PoC's query), ``hl=en-IN&gl=IN&ceid=IN:en``; parsed with
  ``defusedxml``.
* The feed's terms are personal use only, so every signal is ``redistributable: false`` (from
  ``SOURCE_PRIORS``): a pointer with our own redacted headline and classification, never Google's text re-served.
* ``publisher`` is the domain of the item's ``<source url>``: an outlet (a place or organisation), never a
  person. The ``<source>`` element's display name is free text that is never emitted: a personal blog's display
  name would be a person's name, and no cue word would reveal it. So it is no hint, the title's trailing
  ``" - <display name>"`` (Google appends it to every headline) is cut when it equals the ``<source>`` text, and
  the description's ``<font>`` publisher label (the same name) is dropped; the domain carries the provenance.
* ``source_id`` is the item ``guid`` (an opaque Google article id). An old-format guid base64-encodes the
  publisher's URL (whose slug can name a person), so a guid that is, or decodes to, a URL is replaced by
  ``url-sha256:`` of the item link (:func:`guid_embeds_url`). The item link is never emitted (it resolves to the
  publisher's URL): only its ``url_sha256:`` hint is kept.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
import urllib.parse
from collections import Counter

import httpx

from osint_common.types import RawOsintSignal
from osint_ingress.cache import Cache, CacheEntry
from osint_ingress.connectors.base import (
    PERSON_RECORD_DOMAINS,
    Connector,
    ConnectorError,
    Draft,
    bare_domain,
    build_signals,
    parse_xml,
    strip_html,
    url_sha256,
)
from osint_ingress.safe_http import fetch

__all__ = ["FEED_URL", "QUERY", "GoogleNews", "guid_embeds_url", "without_display_name"]

QUERY = (
    'Ahmedabad (robbery OR "road rage" OR accident OR fire OR protest OR '
    "waterlogging OR clash OR crash OR flood) when:3d"
)
FEED_URL = (
    "https://news.google.com/rss/search?q=" + urllib.parse.quote(QUERY) + "&hl=en-IN&gl=IN&ceid=IN:en"
)


_B64URL = re.compile(r"^[A-Za-z0-9_-]{8,}={0,2}$")


def guid_embeds_url(guid: str) -> bool:
    """Is the guid a URL, or a base64 payload that holds one? Google's old ``CBMi…`` article ids encode the
    publisher's URL (its slug can name a person); the current ones (``CBMi…AU_yqL…``) are opaque."""
    g = guid.strip()
    low = g.lower()
    if "://" in low or low.startswith(("http", "www.")):
        return True
    if not _B64URL.match(g):
        return False
    try:
        raw = base64.urlsafe_b64decode(g.rstrip("=") + "=" * (-len(g.rstrip("=")) % 4)).lower()
    except (binascii.Error, ValueError):
        return False
    return b"http" in raw or b"www." in raw


def without_display_name(title: str, display_name: str) -> str:
    """``"<headline> - <display name>"`` → ``"<headline>"`` when the suffix is exactly the ``<source>`` text."""
    name = " ".join(display_name.split())
    head = " ".join(title.split())
    suffix = f" - {name}"
    if name and head.endswith(suffix) and len(head) > len(suffix):
        return head[: -len(suffix)].rstrip()
    return title


class GoogleNews(Connector):
    name = "google_news_rss"
    default_cadence_sec = 600
    max_bytes = 5 * 1024 * 1024

    async def fetch(self, client: httpx.AsyncClient, cache: Cache) -> CacheEntry | None:
        res = await fetch(client, FEED_URL, max_bytes=self.max_bytes)
        if not res.ok:
            raise ConnectorError(f"HTTP {res.status}")
        parse_xml(res.content)  # refuse a hostile or broken document before it is cached as "good"
        return cache.put(self.name, res.content, "xml")

    def parse(self, entry: CacheEntry, protect: frozenset[str]) -> list[RawOsintSignal]:
        self.last_dropped = Counter()
        root = parse_xml(entry.read_bytes(self.max_bytes))
        drafts: list[Draft] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            guid = (item.findtext("guid") or "").strip()
            link = (item.findtext("link") or "").strip()
            source_el = item.find("source")
            domain = bare_domain(source_el.get("url")) if source_el is not None else None
            if domain in PERSON_RECORD_DOMAINS:
                self.last_dropped["person_record_domain"] += 1
                continue
            display = (source_el.text or "").strip() if source_el is not None else ""
            title = without_display_name(title, display)
            digest = url_sha256(link)
            if guid and guid_embeds_url(guid):
                # never keep a URL inside an id: the link's hash stands in (else a hash of the guid itself)
                guid_hash = hashlib.sha256(guid.encode("utf-8")).hexdigest()
                source_id = f"url-sha256:{digest}" if digest else f"guid-sha256:{guid_hash}"
            else:
                source_id = guid or (f"url-sha256:{digest}" if digest else "")
            if not source_id or not title:
                continue
            # the description is "<a>headline</a>&nbsp;&nbsp;<font>display name</font>": the label is dropped
            desc = strip_html(item.findtext("description") or "", drop=("font",))
            if display and desc.endswith(display):  # a label without its <font> wrapper
                desc = desc[: -len(display)].rstrip()
            pub = (item.findtext("pubDate") or "").strip()
            drafts.append(
                Draft(
                    source_id=source_id,
                    title=title,
                    text=(title + ". " + desc)[:1000] if desc else title,
                    published_at=pub,
                    url=link or None,
                    publisher=domain,
                    language="en",
                    category_hint=[f"domain:{domain}"] if domain else [],
                    raw={"source_domain": domain, "pub_date": pub[:64] or None},
                )
            )
        return build_signals(self.name, drafts, entry, protect, dropped=self.last_dropped)
