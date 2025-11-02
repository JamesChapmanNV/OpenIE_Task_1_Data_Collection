from oie_search.scoring import featurize_preview, score_preview

def test_scoring_monotonic_overlap():
    seed = {"title": "ketamine therapy overview", "description": "mechanisms and safety"}
    p_low = {"title": "gardening tips", "description": "soil and water", "platform":"youtube"}
    p_hi  = {"title": "ketamine therapy safety", "description": "mechanisms dosing", "platform":"youtube"}

    f_low = featurize_preview(p_low, seed)
    f_hi  = featurize_preview(p_hi, seed)

    s_low = score_preview(f_low)
    s_hi  = score_preview(f_hi)
    assert s_hi > s_low
