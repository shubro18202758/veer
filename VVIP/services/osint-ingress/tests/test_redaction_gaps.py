"""F-HONEST OSINT-2 and OSINT-6: the redaction gaps the audit proved (``probes/osint_redaction_probe.txt``).

Names with no cue word, Gujarati and Hindi names, and a poster's age and sex shorthand all survived parse-time
redaction while ``ethics.find_pii`` still answered ``[]``. Every fictional name below is the audit's probe text or
shaped like it; none is a real person's.
"""

from __future__ import annotations

import pytest

from osint_common import ethics
from osint_ingress.connectors._redact import TOKEN_WITHHELD, redact_persons

#: (text, name words that must be gone): the audit probe's leaks, news tiers.
AUDIT_LEAKS = [
    ("Biker Jignesh Solanki dies after truck hits him on SP Ring Road", ["Jignesh", "Solanki"]),
    ("Jignesh Solanki dies after truck hits him on SP Ring Road", ["Jignesh", "Solanki"]),
    ("Hit-and-run: Paresh Desai, a resident of Maninagar, succumbs", ["Paresh", "Desai"]),
    ("Police arrest Mehul Joshi for chain snatching in Navrangpura", ["Mehul", "Joshi"]),
    ("Accused Bharatbhai alias Bhuro held for robbery", ["Bharatbhai", "Bhuro"]),
    ("Septuagenarian Hasmukhlal Mehta robbed at Satellite", ["Hasmukhlal", "Mehta"]),
    ("Doctor couple Nirav and Priya Shah robbed at gunpoint near Bodakdev", ["Nirav", "Priya", "Shah"]),
    ("રમેશભાઈ પટેલ (45) નું અકસ્માતમાં મોત", ["રમેશભાઈ", "પટેલ", "45"]),
    ("अहमदाबाद में रमेश पटेल की हत्या", ["रमेश", "पटेल"]),
    ("Where is Kalpita's body? 11 days on, sewer search continues", ["Kalpita"]),  # the stored-victim shape
]


def _kept(word: str, text: str) -> bool:
    import re

    if word.isascii():
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text) is not None
    return word in text


@pytest.mark.parametrize("tier", ["news_regional", "aggregator", "news_wire", "social_unverified", "official"])
@pytest.mark.parametrize(("text", "names"), AUDIT_LEAKS)
def test_the_audit_leaks_are_redacted_in_every_tier(protect, tier, text, names):
    out, n = redact_persons(text, tier, protect)
    assert n > 0 and not [w for w in names if _kept(w, out)], out
    assert ethics.find_pii(out) == [] and ethics.find_unredactable(out) == []


@pytest.mark.parametrize(
    ("text", "kept"),
    [
        ("Biker Jignesh Solanki dies after truck hits him on SP Ring Road", ["Biker", "SP Ring Road"]),
        ("Hit-and-run: Paresh Desai, a resident of Maninagar, succumbs", ["Maninagar"]),
        ("Truck overturns on Sardar Patel Ring Road near Odhav Ring Road Circle", ["Sardar Patel Ring Road",
                                                                                   "Odhav Ring Road Circle"]),
        ("Fixture Kiosk Opens At Riverfront", ["Fixture Kiosk Opens At Riverfront"]),  # a Title-Case headline
        ("Youth Congress protest near Income Tax Circle", ["Youth Congress"]),  # an organisation after a role noun
        ("Patel community meeting at GMDC Ground", ["Patel community"]),  # a surname alone is not a person
    ],
)
def test_places_organisations_and_headlines_survive(protect, text, kept):
    out, _ = redact_persons(text, "news_regional", protect)
    assert all(k in out for k in kept), out


def test_indic_words_are_withheld_but_gazetteer_places_and_common_words_stay(protect):
    out, n = redact_persons("પાલડીમાં આગ: રમેશભાઈ શાહ સહિત ત્રણ ઘાયલ", "news_regional", protect)
    assert out == f"પાલડીમાં આગ: {TOKEN_WITHHELD} સહિત ત્રણ ઘાયલ" and n == 1
    out, _ = redact_persons("एस जी हाईवे पर टक्कर, ओढव में जाम", "aggregator", protect)
    assert TOKEN_WITHHELD not in out  # a place phrase and common words only
    # the Devanagari name in a half-Latin title (the shape of a stored int3c case) goes with the Latin one
    out, _ = redact_persons("फिक्टस डमीवाला के खिलाफ केस; case on Accused Fictus Dummyvala", "aggregator", protect)
    assert "फिक्टस" not in out and "डमीवाला" not in out and "Dummyvala" not in out


def test_indic_suffixes_are_the_geo_scanners(protect):
    from osint_geo import translit

    assert set(ethics.INDIC_SUFFIXES) == set(translit.GU_SUFFIXES)


@pytest.mark.parametrize(
    ("text", "marker"),
    [
        ("IT'S SO BORINGGGG IN WEEEKEND HERE F(28)", "F(28)"),
        ("Any other 22M second-gen imitation jewelry wholesalers here?", "22M"),
        ("27/F, is the Paldi underpass flooded?", "27/F"),
        ("(24F) looking for a flatmate in Vastrapur", "24F"),
        ("M/30 here, moved to Gota last month", "M/30"),
        ("26 M, looking for a cycling group", "26 M"),
    ],
)
def test_a_posters_age_and_sex_shorthand_is_redacted(protect, text, marker):
    out, n = redact_persons(text, "social_unverified", protect)
    assert marker not in out and "[AGE]" in out and n >= 1, out


@pytest.mark.parametrize("text", ["Flat for Rs 22M in Bodakdev", "Flat for Rs. 22M in Bodakdev", "Budget ₹22M"])
def test_amounts_are_not_age_markers(protect, text):
    # known over-redaction, accepted: a bare "15M" or "M25" in a post reads as an age marker (the poster's own
    # "22M" cannot be told apart from it without context)
    out, _ = redact_persons(text, "social_unverified", protect)
    assert "[AGE]" not in out, out
