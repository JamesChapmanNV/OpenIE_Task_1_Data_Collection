import re
from oie_search.query_generator import build_phrase_candidates

def test_build_phrase_candidates_basic():
    seed = {
        "title": "rTMS vs tDCS for depression",
        "description": "Comparative points and meta-analyses. Real-world outcomes. Safety profile discussed.",
        "transcript": None, "ocr": None, "body": ""
    }
    phrases = build_phrase_candidates(seed)
    # title first
    assert phrases[0].startswith("rtms vs tdcs")
    # long-ish sentences included & normalized
    assert any("comparative points and meta analyses" in p or "comparative points and meta-analyses" in p for p in phrases)
    # dedupe & cap
    assert len(phrases) <= 6
    # all lowercase/alnum/space
    assert all(re.match(r"^[a-z0-9\s\-\+]+$", p) for p in phrases)
