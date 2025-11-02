from oie_search.digestors import digest_youtube_preview

def test_digest_youtube_preview_minimal():
    raw = {
        "id": "abc123",
        "url": "https://youtube.com/watch?v=abc123",
        "title": "AuDHD lived experience – coping strategies",
        "description": "Short tips and daily routine ideas.",
        "channel": "NeuroTalk",
        "publishedAt": "2025-10-31T09:00:00Z",
        "statistics": {"viewCount": 1000, "likeCount": 45, "commentCount": 7},
    }
    out = digest_youtube_preview(raw)
    assert out["platform"] == "youtube"
    assert out["post_id"] == "abc123"
    assert out["url"].startswith("https://youtube.com")
    assert "AuDHD" in out["title"]
    assert isinstance(out["engagement"], dict)

