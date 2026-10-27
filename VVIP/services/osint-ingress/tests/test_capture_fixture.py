"""The committed synthetic capture (``tests/fixtures/capture/``): import-poc reads it unchanged; per-source counts;
every publisher is fictional (``*.example``, the community ``reddit.com/r/example_city``) or ``sachet.ndma.gov.in``;
redaction is counted; its README marks every file, and only the public-domain SACHET sample is real."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter

from conftest import CAPTURE, FIXTURES, PACKAGE, POC_RAW, parse_cache

from osint_ingress.cache import Cache
from osint_ingress.connectors import build_connectors
from osint_ingress.importer import CAPTURE_FILES, import_capture

#: sha256 of NDMA SACHET's public-domain Gujarat CAP RSS as the PoC captured it (the one real file).
SACHET_SHA256 = "5859003279823785ee36e1071cee5ffa8158c00ff639c5246fbb4bc3540eef4d"
EXPECTED = {"sachet_cap": 10, "google_news_rss": 8, "gdelt_events": 2, "gdelt_doc": 4, "reddit_rss": 4}


def test_import_poc_cli_reads_the_capture(tmp_path):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(str(PACKAGE / p) for p in ("src", "../osint-common/src")))
    proc = subprocess.run(
        [sys.executable, "-m", "osint_ingress", "import-poc", str(CAPTURE), str(tmp_path / "cache")],
        cwd=PACKAGE, env=env, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr[-1000:]
    out = json.loads(proc.stdout)
    assert set(out["imported"]) == set(EXPECTED) and out["gdelt_export_blobs"] == ["20261020120000.export.CSV.zip"]
    assert out["ignored"] == ["README.md"]
    cache = Cache(tmp_path / "cache")
    assert all(cache.latest(n) is not None and cache.latest(n).origin == "import-poc" for n in EXPECTED)


def test_per_source_counts_publishers_and_redaction(tmp_path, protect):
    import_capture(CAPTURE, tmp_path / "cache")
    got = parse_cache(Cache(tmp_path / "cache"), build_connectors(), protect)
    assert {k: len(v) for k, v in got.items()} == EXPECTED
    sigs = [s for v in got.values() for s in v]
    for s in sigs:
        assert (
            s.publisher.endswith(".example")
            or s.publisher == "reddit.com/r/example_city"
            or s.publisher == "sachet.ndma.gov.in"
        ), s.publisher
        assert s.fetch_mode == "cached-sample"
    by_source = Counter()
    for s in sigs:
        by_source[s.source] += s.pii_redactions
    assert sum(by_source.values()) > 0
    assert by_source["google_news_rss"] > 0 and by_source["gdelt_doc"] > 0 and by_source["reddit_rss"] > 0
    assert by_source["sachet_cap"] == 0  # official weather alerts name no person


def test_readme_marks_every_file_and_only_sachet_is_real():
    readme = (CAPTURE / "README.md").read_text(encoding="utf-8")
    rows = dict(re.findall(r"^\|\s*`([^`]+)`\s*\|\s*\*\*(real|synthetic)\*\*", readme, re.MULTILINE))
    files = {p.name for p in CAPTURE.iterdir() if p.is_file() and p.name != "README.md"}
    assert set(rows) == files, (set(rows) ^ files)
    assert [f for f, kind in rows.items() if kind == "real"] == ["sachet_gujarat_live.xml"]
    assert (FIXTURES / "README.md").is_file()


def test_the_real_file_is_the_public_domain_sachet_sample_verbatim():
    data = (CAPTURE / "sachet_gujarat_live.xml").read_bytes()
    assert hashlib.sha256(data).hexdigest() == SACHET_SHA256
    assert b"<copyright>public domain</copyright>" in data
    if POC_RAW.is_dir():
        assert (POC_RAW / "sachet_gujarat_live.xml").read_bytes() == data


def test_capture_layout_matches_a_poc_raw_directory():
    names = {p.name for p in CAPTURE.iterdir() if p.is_file()}
    assert set(CAPTURE_FILES) <= names
    if POC_RAW.is_dir():
        poc = {p.name for p in POC_RAW.iterdir() if p.is_file()}
        assert set(CAPTURE_FILES) <= poc  # the same file names as the PoC's out/raw


def test_synthetic_gdelt_files_match_their_generator():
    proc = subprocess.run([sys.executable, str(FIXTURES / "build_synthetic_gdelt.py"), "--check"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ── F-HONEST OSINT-5: the synthetic capture is SIMULATED and names no real community ──────────────────────────


def test_import_marks_the_readme_synthetic_files_and_their_signals_are_simulated(tmp_path, protect):
    from osint_ingress.importer import synthetic_files

    marked = synthetic_files(CAPTURE)
    assert marked == {p.name for p in CAPTURE.iterdir() if p.is_file() and p.name not in ("README.md",
                                                                                         "sachet_gujarat_live.xml")}
    report = import_capture(CAPTURE, tmp_path / "cache")
    assert {k: v["synthetic"] for k, v in report["imported"].items()} == {
        "sachet_cap": False, "google_news_rss": True, "gdelt_events": True, "gdelt_doc": True, "reddit_rss": True}
    cache = Cache(tmp_path / "cache")
    assert cache.latest("google_news_rss").synthetic and not cache.latest("sachet_cap").synthetic  # survives a reload
    got = parse_cache(cache, build_connectors(), protect)
    for source, sigs in got.items():
        labels = {s.provenance_label for s in sigs}
        # the one real file (public-domain SACHET) keeps its source's label; every written one is SIMULATED
        assert labels == ({"OFFICIAL-VERIFIED"} if source == "sachet_cap" else {"SIMULATED"}), (source, labels)


def test_a_capture_without_a_readme_is_not_synthetic(tmp_path, protect):
    import shutil

    from osint_ingress.importer import synthetic_files

    raw = tmp_path / "raw"
    raw.mkdir()
    shutil.copy(CAPTURE / "gnews_live.xml", raw / "gnews_live.xml")
    assert synthetic_files(raw) == frozenset()
    import_capture(raw, tmp_path / "cache")
    entry = Cache(tmp_path / "cache").latest("google_news_rss")
    assert not entry.synthetic
    assert {s.provenance_label for s in build_connectors()["google_news_rss"].parse(entry, protect)} == {
        "NEWS-REPORTED"}


def test_the_synthetic_posts_name_a_fictional_community_never_r_ahmedabad(tmp_path, protect):
    feed = (CAPTURE / "reddit_live.rss").read_text(encoding="utf-8")
    assert "ahmedabad" not in feed.lower() and 'term="example_city"' in feed
    import_capture(CAPTURE, tmp_path / "cache")
    sigs = build_connectors()["reddit_rss"].parse(Cache(tmp_path / "cache").latest("reddit_rss"), protect)
    assert len(sigs) == 4
    assert {(s.publisher, s.raw["subreddit"], s.provenance_label) for s in sigs} == {
        ("reddit.com/r/example_city", "example_city", "SIMULATED")}
