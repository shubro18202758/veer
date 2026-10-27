"""The connectors: one per ``RawOsintSignal.source``, each with ``fetch(client, cache)`` and
``parse(entry, protect)``.

======================== ======================== =====================================================
source                   module                   endpoint (egress allow-list)
======================== ======================== =====================================================
``sachet_cap``           :mod:`.official`         sachet.ndma.gov.in (CAP RSS + CAP 1.2 detail)
``google_news_rss``      :mod:`.google_news`      news.google.com (RSS search)
``gdelt_events``         :mod:`.gdelt`            data.gdeltproject.org (lastupdate.txt + export zip)
``gdelt_doc``            :mod:`.gdelt`            api.gdeltproject.org (DOC 2.0 ArtList, ≥ 5 s spacing)
``reddit_rss``           :mod:`.reddit`           www.reddit.com (r/ahmedabad Atom)
``amc_scrape``           :mod:`.official`         ahmedabadcity.gov.in (page, robots.txt)
``gsdma``                :mod:`.official`         gsdma.org (page, robots.txt)
``ahmedabad_police_scrape`` :mod:`.official`      disabled: host unverified
``common_crawl``         :mod:`.common_crawl`     index.commoncrawl.org + data.commoncrawl.org (backfill)
======================== ======================== =====================================================
"""

from __future__ import annotations

from osint_ingress.connectors.base import Connector, ConnectorError
from osint_ingress.connectors.common_crawl import CommonCrawl
from osint_ingress.connectors.gdelt import GdeltBulk, GdeltDoc
from osint_ingress.connectors.google_news import GoogleNews
from osint_ingress.connectors.official import AmcPage, GsdmaPage, PolicePage, Sachet
from osint_ingress.connectors.reddit import Reddit
from osint_ingress.safe_http import RobotsCache

__all__ = ["Connector", "ConnectorError", "build_connectors"]


def build_connectors(*, robots: RobotsCache | None = None) -> dict[str, Connector]:
    """Every connector, keyed by source name, in the order a cycle runs them (official first)."""
    robots = robots or RobotsCache()
    conns: list[Connector] = [
        Sachet(),
        GoogleNews(),
        GdeltBulk(),
        GdeltDoc(),
        Reddit(),
        AmcPage(robots),
        GsdmaPage(robots),
        PolicePage(robots),
        CommonCrawl(),
    ]
    return {c.name: c for c in conns}
