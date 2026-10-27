"""Official sources: NDMA SACHET CAP (IMD and SDMA alerts arrive through it) and the AMC, GSDMA and Ahmedabad
Police pages (OSINT_SOURCES.md §3). Official inputs are authoritative and cooperative: Veer feeds the city's
channels, it never second-guesses them.

SACHET (``sachet_cap``, §3a):

* the Gujarat CAP RSS, every 5 min; ``OFFICIAL-VERIFIED``, credibility 0.95, public domain (``SOURCE_PRIORS``);
* the area hint keeps its real level (plan R28): ``LGD:AHMEDABAD`` (a **district**) for an alert naming
  Ahmedabad or Amdavad, otherwise ``LGD:GUJARAT`` (the **state**: the state-wide nowcasts that name other
  districts are not Ahmedabad locations, and OS-3/OS-4 hold them as outside the city);
* ``fetch`` also caches the full CAP 1.2 XML of up to ten new alerts per cycle (best effort; a failure leaves the
  RSS-only signal); ``parse`` reads it, when cached, for the expiry, severity, urgency, certainty, LGD district
  codes and the polygon URL. Every XML document goes through ``defusedxml``. The RSS ``author`` (an NDMA control
  room mailbox) and the CAP ``sender``, ``contact``, ``addresses`` and ``note`` are never read;
* official URLs are kept (identifier-only paths, ``FetchXMLFile?identifier=...``).

Official pages (``amc_scrape``, ``gsdma``, ``ahmedabad_police_scrape``; hourly, best effort): stdlib
``html.parser`` only, robots.txt honoured (a disallowed path disables the connector: "robots.txt disallows",
raised as :class:`~.base.ConnectorDisabled`, so the cached page is NOT served in its place; an unreachable
robots.txt is a failure like any other), and a failure degrades to the cached page. Each notice-like same-site
link becomes one signal. The police
connector is **disabled in code**: the host listed in OSINT_SOURCES.md §3e serves an unrelated gambling page
(``research/samples/acp.html``), so its content must not be labelled ``OFFICIAL-VERIFIED`` until an official host
is verified and added to the egress allow-list.
"""

from __future__ import annotations

import asyncio
import re
import urllib.parse
from collections import Counter
from html.parser import HTMLParser
from typing import Any, ClassVar

import httpx

from osint_common.types import RawOsintSignal
from osint_ingress.cache import Cache, CacheEntry
from osint_ingress.connectors.base import (
    AHMEDABAD_RE,
    Connector,
    ConnectorDisabled,
    ConnectorError,
    Draft,
    build_signals,
    canonical_url,
    parse_xml,
    strip_html,
    url_sha256,
)
from osint_ingress.safe_http import ROBOTS_DISALLOWS, EgressRefused, FetchError, RobotsCache, fetch

__all__ = [
    "CAP_URL",
    "RSS_URL",
    "AmcPage",
    "GsdmaPage",
    "OfficialPage",
    "PolicePage",
    "Sachet",
    "cap_fields",
]

RSS_URL = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_gujarat.xml"
CAP_URL = "https://sachet.ndma.gov.in/cap_public_website/FetchXMLFile?identifier={identifier}"
SACHET_HOST = "sachet.ndma.gov.in"
_CAP = "{urn:oasis:names:tc:emergency:cap:1.2}"
_GUID = re.compile(r"^\d{6,32}$")
_CAP_ID = re.compile(r"[?&]identifier=([A-Za-z0-9_.\-]{1,64})")
_LGD_CODE = re.compile(r"^\d{1,6}$")
MAX_CAP_DETAILS_PER_CYCLE = 10


def _official_url(url: str | None, host: str) -> str | None:
    """``url`` when it is an https URL on ``host`` (an official identifier URL), else ``None``."""
    c = canonical_url(url)
    if not c or not c.startswith(f"https://{host}/"):
        return None
    return c


def cap_fields(data: bytes) -> dict[str, Any]:
    """The CAP 1.2 fields Veer uses, from one alert (``defusedxml``). ``{}`` when it is not a CAP alert."""
    root = parse_xml(data)
    if root.tag != f"{_CAP}alert":
        return {}

    def t(el: Any, name: str) -> str:
        return ((el.findtext(_CAP + name) if el is not None else None) or "").strip()

    info = root.find(_CAP + "info")
    area = info.find(_CAP + "area") if info is not None else None
    lgd: list[str] = []
    polygon = None
    if area is not None:
        for gc in area.findall(_CAP + "geocode"):
            if t(gc, "valueName") == "LGD District Code" and _LGD_CODE.match(t(gc, "value")):
                lgd.append(t(gc, "value"))
    if info is not None:
        for p in info.findall(_CAP + "parameter"):
            if t(p, "valueName") == "Polygon URL":
                polygon = _official_url(t(p, "value"), SACHET_HOST)
    return {
        "identifier": t(root, "identifier"),
        "sent": t(root, "sent"),
        "status": t(root, "status"),
        "msg_type": t(root, "msgType"),
        "scope": t(root, "scope"),
        "category": t(info, "category"),
        "event": t(info, "event"),
        "urgency": t(info, "urgency"),
        "severity": t(info, "severity"),
        "certainty": t(info, "certainty"),
        "effective": t(info, "effective"),
        "onset": t(info, "onset"),
        "expires": t(info, "expires"),
        "headline": t(info, "headline"),
        "description": t(info, "description"),
        "area_desc": t(area, "areaDesc"),
        "lgd_codes": lgd,
        "polygon_url": polygon,
    }


class Sachet(Connector):
    """NDMA SACHET CAP alerts for Gujarat (RSS, plus the CAP detail of new alerts)."""

    name = "sachet_cap"
    default_cadence_sec = 300
    max_bytes = 2 * 1024 * 1024
    #: polite spacing between CAP detail requests (seconds)
    detail_spacing_sec: float = 0.5

    async def fetch(self, client: httpx.AsyncClient, cache: Cache) -> CacheEntry | None:
        res = await fetch(client, RSS_URL, max_bytes=self.max_bytes)
        if not res.ok:
            raise ConnectorError(f"HTTP {res.status}")
        root = parse_xml(res.content)
        ids = [g for g in ((i.findtext("guid") or "").strip() for i in root.iter("item")) if _GUID.match(g)]
        fetched = 0
        for gid in ids:
            blob = f"cap-{gid}.xml"
            if cache.blob_path(self.name, blob) is not None:
                continue
            if fetched >= MAX_CAP_DETAILS_PER_CYCLE:
                break
            fetched += 1
            try:
                if fetched > 1 and self.detail_spacing_sec:
                    await asyncio.sleep(self.detail_spacing_sec)
                cres = await fetch(client, CAP_URL.format(identifier=gid), max_bytes=512 * 1024)
                if cres.ok and cap_fields(cres.content):
                    cache.put_blob(self.name, blob, cres.content)
            except (FetchError, ConnectorError, EgressRefused, httpx.HTTPError):
                # the CAP detail is an enrichment: the RSS alert still stands without it (also when one detail
                # URL redirects off the allow-list: that request is refused, the rest of the fetch goes on)
                continue
        blobs = [f"cap-{g}.xml" for g in ids if cache.blob_path(self.name, f"cap-{g}.xml") is not None]
        return cache.put(self.name, res.content, "xml", blobs=blobs)

    def _detail(self, entry: CacheEntry, guid: str) -> dict[str, Any]:
        if not _GUID.match(guid):
            return {}
        path = entry.blob_path(f"cap-{guid}.xml")
        if path is None:
            return {}
        try:
            return cap_fields(path.read_bytes())
        except ConnectorError:
            self.last_dropped["cap_detail_refused"] += 1
            return {}

    def parse(self, entry: CacheEntry, protect: frozenset[str]) -> list[RawOsintSignal]:
        self.last_dropped = Counter()
        root = parse_xml(entry.read_bytes(self.max_bytes))
        drafts: list[Draft] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            guid = (item.findtext("guid") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            desc = strip_html(item.findtext("description") or "")
            category = (item.findtext("category") or "").strip()
            cap = self._detail(entry, guid)
            hay = " ".join((title, desc, cap.get("headline", ""), cap.get("area_desc", "")))
            ahmedabad = bool(AHMEDABAD_RE.search(hay))
            area = "ahmedabad" if ahmedabad else "gujarat"
            source_id = guid or (f"url-sha256:{url_sha256(link)}" if url_sha256(link) else "")
            if not source_id or not title:
                continue
            text = title + (". " + desc if desc else "")
            extra = cap.get("description") or ""
            if extra and extra not in text:
                text = f"{text}. {extra}"
            cap_category = cap.get("category") or category
            polygon = cap.get("polygon_url")
            drafts.append(
                Draft(
                    source_id=source_id,
                    title=title,
                    text=text[:1000],
                    published_at=pub or cap.get("sent"),
                    valid_until=cap.get("expires"),
                    url=_official_url(link, SACHET_HOST),
                    publisher=SACHET_HOST,
                    language="en",
                    place_names=["Ahmedabad"] if ahmedabad else ["Gujarat"],
                    admin_codes=["LGD:AHMEDABAD"] if ahmedabad else ["LGD:GUJARAT"],
                    polygon_url=polygon,
                    geo_confidence=0.3 if ahmedabad else 0.1,
                    category_hint=[
                        h
                        for h in ("CAP", f"CAP:{cap_category}" if cap_category else "", f"area:{area}",
                                  f"CAP_EVENT:{cap['event']}" if cap.get("event") else "")
                        if h
                    ],
                    raw={
                        "cap_identifier": cap.get("identifier") or guid,
                        "cap_category": cap_category or None,
                        "cap_sent": cap.get("sent") or None,
                        "cap_status": cap.get("status") or None,
                        "cap_msg_type": cap.get("msg_type") or None,
                        "cap_scope": cap.get("scope") or None,
                        "cap_event": cap.get("event") or None,
                        "cap_urgency": cap.get("urgency") or None,
                        "cap_severity": cap.get("severity") or None,
                        "cap_certainty": cap.get("certainty") or None,
                        "cap_effective": cap.get("effective") or None,
                        "cap_onset": cap.get("onset") or None,
                        "cap_expires": cap.get("expires") or None,
                        "cap_area_code": ",".join(cap.get("lgd_codes") or [])[:512] or None,
                        "cap_polygon_id": (m.group(1) if polygon and (m := _CAP_ID.search(polygon)) else None),
                    },
                )
            )
        return build_signals(self.name, drafts, entry, protect, dropped=self.last_dropped)


# ── official page scrapers ────────────────────────────────────────────────────────────────────────────────────

_NOTICE_PATH = re.compile(
    r"(press|news|notice|advisor|circular|release|update|announce|traffic|monsoon|alert|warning|bulletin|\.pdf$)",
    re.IGNORECASE,
)
_NOTICE_WORDS = re.compile(
    r"\b(press|notice|advisory|circular|release|traffic|diversion|closure|closed|monsoon|rain|flood|waterlog\w*|"
    r"alert|warning|cyclone|heat\s?wave|fire|accident|emergency|helpline|control room|road|bridge|metro|drainage)\b",
    re.IGNORECASE,
)
_SKIP_EXT = re.compile(r"\.(?:jpe?g|png|gif|svg|webp|css|js|ico|woff2?|ttf|mp4|zip)$", re.IGNORECASE)


class _Anchors(HTMLParser):
    """Collects ``(href, visible text)`` of every anchor and the page's ``<html lang>``."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[tuple[str, str]] = []
        self.lang = ""
        self._href: str | None = None
        self._text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.lang = str(a["lang"])[:16]
        elif tag in ("script", "style", "noscript", "template"):
            self._skip += 1
        elif tag == "a":
            self._flush()
            self._href = (a.get("href") or "").strip()
            self._text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript", "template") and self._skip:
            self._skip -= 1
        elif tag == "a":
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._href is not None and not self._skip:
            self._text.append(data)

    def _flush(self) -> None:
        if self._href is not None and len(self.items) < 2000:
            self.items.append((self._href, re.sub(r"\s+", " ", "".join(self._text)).strip()))
        self._href = None
        self._text = []

    def close(self) -> None:
        super().close()
        self._flush()


class OfficialPage(Connector):
    """A government page whose notice links become signals (best effort; robots.txt honoured)."""

    default_cadence_sec = 3600
    max_bytes = 5 * 1024 * 1024
    page_url: ClassVar[str]
    host: ClassVar[str]
    #: the area level this office covers: ``ahmedabad`` (a district hint) or ``gujarat`` (state)
    area: ClassVar[str]

    def __init__(self, robots: RobotsCache | None = None) -> None:
        super().__init__()
        self.robots = robots or RobotsCache()

    async def fetch(self, client: httpx.AsyncClient, cache: Cache) -> CacheEntry | None:
        if not self.enabled:
            return None
        allowed, reason = await self.robots.allowed(client, self.page_url)
        if not allowed:
            reason = reason or ROBOTS_DISALLOWS
            if reason.startswith(ROBOTS_DISALLOWS):
                raise ConnectorDisabled(reason)  # the site says no: disabled, and its cache is not served
            raise ConnectorError(reason)  # robots.txt unreachable: a failure (the cached page may be served)
        try:
            res = await fetch(client, self.page_url, max_bytes=self.max_bytes)
        except httpx.ConnectError as exc:
            raise ConnectorError("connection failed (TLS or network)") from exc
        if not res.ok:
            raise ConnectorError(f"HTTP {res.status}")
        ctype = res.headers.get("content-type", "text/html").lower()
        if "html" not in ctype:
            raise ConnectorError("not an HTML page")
        return cache.put(self.name, res.content, "html")

    def parse(self, entry: CacheEntry, protect: frozenset[str]) -> list[RawOsintSignal]:
        self.last_dropped = Counter()
        html = entry.read_bytes(self.max_bytes).decode("utf-8", "replace")
        anchors = _Anchors()
        try:
            anchors.feed(html)
            anchors.close()
        except Exception as exc:  # noqa: BLE001 - html.parser is lenient; a hard failure means an unusable page
            raise ConnectorError("page could not be parsed") from exc
        drafts: list[Draft] = []
        for href, text in anchors.items:
            if not 12 <= len(text) <= 300 or not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            url = canonical_url(urllib.parse.urljoin(self.page_url, href))
            if not url or not url.startswith(f"https://{self.host}/") or _SKIP_EXT.search(url.split("?")[0]):
                continue
            if not (_NOTICE_PATH.search(urllib.parse.urlsplit(url).path) or _NOTICE_WORDS.search(text)):
                continue
            digest = url_sha256(url + "\n" + text)
            drafts.append(
                Draft(
                    source_id=f"url-sha256:{digest}",
                    title=text,
                    text=text,
                    url=url,
                    publisher=self.host,
                    language=anchors.lang or "en",
                    place_names=["Ahmedabad"] if self.area == "ahmedabad" else ["Gujarat"],
                    admin_codes=["LGD:AHMEDABAD"] if self.area == "ahmedabad" else ["LGD:GUJARAT"],
                    geo_confidence=0.3 if self.area == "ahmedabad" else 0.1,
                    category_hint=["page:notice", f"area:{self.area}"],
                    raw={"page_hash": entry.sha256, "page_url_domain": self.host},
                )
            )
        return build_signals(self.name, drafts, entry, protect, dropped=self.last_dropped)


class AmcPage(OfficialPage):
    """Amdavad Municipal Corporation (OSINT_SOURCES.md §3c; the server needs legacy TLS renegotiation, which is
    not enabled: the fetch then fails honestly and the cached page, if any, is served)."""

    name = "amc_scrape"
    page_url = "https://ahmedabadcity.gov.in/"
    host = "ahmedabadcity.gov.in"
    area = "ahmedabad"


class GsdmaPage(OfficialPage):
    """Gujarat State Disaster Management Authority (§3d; its CAP warnings arrive through SACHET already)."""

    name = "gsdma"
    page_url = "https://gsdma.org/"
    host = "gsdma.org"
    area = "gujarat"


class PolicePage(OfficialPage):
    """Ahmedabad City Police notices: disabled until an official host is verified (module docstring)."""

    name = "ahmedabad_police_scrape"
    page_url = "https://ahmedabadcitypolice.org/"
    host = "ahmedabadcitypolice.org"
    area = "ahmedabad"
    disabled_reason = (
        "disabled: host unverified (the OSINT_SOURCES.md §3e domain serves unrelated content; "
        "verify the official police host before allow-listing it)"
    )
