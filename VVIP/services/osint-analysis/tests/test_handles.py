"""Poster handles are never a cue (ethics rule 2: a handle is never stored, shown, tracked or scored).

A handle that survives parse (37 of the PoC capture's 40 Reddit texts end in "submitted by /u/<name> [link]
[comments]") must never classify a post, never add a similarity token, never reach an embedder, and never leave the
pipeline; so two posts by ONE poster are never more alike than the same two posts by two posters."""

from __future__ import annotations

import json
import re

import pytest

from analysis_fixtures import PALDI_CROSS_ROADS, FakeResolver, at, make_signal, offset, point, poc_out_dir
from osint_common.types import RawOsintSignal
from osint_analysis.classify import classify, normalize_text, similarity_text, strip_handles
from osint_analysis.fusion import content_tokens
from osint_analysis.pipeline import fit_text, run_pipeline

COMMUNITY = "social-a.example/r/example_city"
OTHER_COMMUNITY = "social-b.example/r/example_town"


@pytest.mark.parametrize(
    ("text", "analysis", "outgoing"),
    [
        ("Waterlogging near Paldi submitted by /u/example_user [link] [comments]", "Waterlogging near Paldi",
         "Waterlogging near Paldi"),
        ("Waterlogging near Paldi, submitted by u/example_user", "Waterlogging near Paldi", "Waterlogging near Paldi"),
        ("Underpass flooded submitted by [PERSON] [link] [comments]", "Underpass flooded", "Underpass flooded"),
        ("Underpass flooded submitted by", "Underpass flooded", "Underpass flooded"),
        ("Thanks u/flood-watcher for the photo", "Thanks   for the photo", "Thanks [PERSON] for the photo"),
        ("See https://www.reddit.com/user/crash_kid/ for more", "See   for more", "See [PERSON] for more"),
        ("old.reddit.com/u/Some_One posted it", "posted it", "[PERSON] posted it"),
        ("(u/someone) and /U/SHOUTING", "( ) and", "([PERSON]) and [PERSON]"),
    ],
)
def test_strip_handles_removes_every_written_form(text, analysis, outgoing):
    assert strip_handles(text) == analysis
    assert strip_handles(text, "[PERSON]") == outgoing
    assert "/u/" not in normalize_text(text) and "submitted by" not in normalize_text(text)


@pytest.mark.parametrize(
    "text",
    [
        "Accused booked u/s 302 at the city court",  # "under section": one letter is not a handle
        "A petition submitted by March 15 to the collector",  # "submitted by" without a handle stays
        "Menu/item and AMU/abc and r/example_city",  # inside a word or a path; a community is not a person
    ],
)
def test_strip_handles_leaves_ordinary_text_alone(text):
    assert strip_handles(text) == text
    assert strip_handles(text, "[PERSON]") == text


#: (a text with a handle whose name carries a lexicon cue, the same text without the handle)
_DECORATIONS = [
    (" submitted by /u/crash-test-kid [link] [comments]", ""),
    (" submitted by u/mob_watch", ""),
    (" thanks u/flood-alerts for the photo", " thanks for the photo"),
    (" via https://www.reddit.com/user/fire-at-will/", " via"),
    (" /u/heavy-rain-guy", ""),
]
_BASES = [
    ("Evening at the lake", "general_news"),
    ("Waterlogging near Paldi underpass", "urban_flooding"),
    ("Car crash near the circle", "road_accident"),
]


@pytest.mark.parametrize(("decoration", "without"), _DECORATIONS)
@pytest.mark.parametrize(("base", "event_class"), _BASES)
def test_a_handle_never_changes_the_class_the_tokens_or_the_embedder_text(base, event_class, decoration, without):
    plain = make_signal("reddit_rss", title=base, text=base + without, publisher=COMMUNITY)
    handled = make_signal("reddit_rss", title=base, text=base + decoration, publisher=COMMUNITY)
    assert classify(plain).event_class == event_class
    assert classify(handled) == classify(plain)
    assert content_tokens(handled) == content_tokens(plain)
    assert similarity_text(handled) == similarity_text(plain)
    # a handle in the title is stripped as well
    titled = make_signal("reddit_rss", title=base + decoration, text=base + without, publisher=COMMUNITY)
    plain_titled = make_signal("reddit_rss", title=base + without, text=base + without, publisher=COMMUNITY)
    assert classify(titled) == classify(plain_titled)
    assert content_tokens(titled) == content_tokens(plain_titled)
    assert similarity_text(titled) == similarity_text(plain_titled)


def _pair(second_handle: str):
    """A post in one community and a different-looking post in another, the second signed by ``second_handle``
    (the same ``source_id`` each time, so the two variants are the same signal but for the handle)."""
    a = make_signal("reddit_rss", title="Waterlogging near Paldi",
                    text="Waterlogging near Paldi submitted by /u/example_user [link] [comments]",
                    publisher=COMMUNITY, published_at=at(0), source_id="synthetic:handle-pair-a")
    b = make_signal("reddit_rss", title="Underpass flooded at the circle",
                    text=f"Underpass flooded at the circle submitted by /u/{second_handle} [link] [comments]",
                    publisher=OTHER_COMMUNITY, published_at=at(10), source_id="synthetic:handle-pair-b")
    geos = [point(a, PALDI_CROSS_ROADS, toponym="Paldi"),
            point(b, offset(PALDI_CROSS_ROADS, north_m=400), toponym="Paldi north")]
    return [a, b], FakeResolver(geos)


def test_one_poster_in_two_communities_is_never_more_alike_than_two_posters():
    same, resolver = _pair("example_user")  # the review's probe: shared handle tokens once fused these into an event
    other, resolver_other = _pair("someone_else")
    assert content_tokens(same[0]) & content_tokens(same[1]) == frozenset()
    r_same = run_pipeline(same, resolver=resolver)
    r_other = run_pipeline(other, resolver=resolver_other)
    assert r_same.model_dump() == r_other.model_dump()  # the output never depends on who posted
    assert r_same.counts.surfaced == 0 and r_same.counts.fused == 2


def test_fit_text_drops_the_trailer_and_redacts_any_other_handle():
    assert fit_text("Underpass flooded, submitted by /u/example_user [link] [comments]", 1000) == "Underpass flooded"
    assert fit_text("Thanks u/flood-watcher for the photo", 1000) == "Thanks [PERSON] for the photo"
    assert fit_text("short /u/abc", 1000) == "short [PERSON]"


_POC = poc_out_dir()


@pytest.mark.skipif(_POC is None, reason="PoC outputs not present (read in place only)")
def test_no_handle_of_the_poc_capture_reaches_the_class_a_token_or_the_embedder_text():
    """Every text of the PoC capture with a handle, read in place: the analysis view equals that of the same signal
    cleaned by an independent reading of the Reddit trailer, and no ``u/<name>`` is left in it (texts are only
    compared in memory, never printed)."""
    raw = json.loads((_POC / "signals.raw.json").read_text(encoding="utf-8"))
    handle = re.compile(r"(?<![\w/])/?u/[A-Za-z0-9_-]{3,}", re.I)
    trailer = re.compile(r"submitted\s+by\s+/?u/[A-Za-z0-9_-]{3,}(?:\s*\[(?:link|comments)\])*", re.I)

    def clean(text: str) -> str:
        return handle.sub(" ", trailer.sub(" ", text))

    seen = 0
    for record in raw:
        signal = RawOsintSignal.model_validate(record)
        if not handle.search(f"{signal.title} {signal.text}"):
            continue
        seen += 1
        cleaned = signal.model_copy(update={"title": clean(signal.title), "text": clean(signal.text)})
        assert handle.search(similarity_text(signal, limit=100_000)) is None, signal.signal_id
        assert similarity_text(signal) == similarity_text(cleaned), signal.signal_id
        assert content_tokens(signal) == content_tokens(cleaned), signal.signal_id
        assert classify(signal) == classify(cleaned), signal.signal_id
    assert seen >= 30  # the capture has 37 texts with a handle
