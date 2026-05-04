from hermeshub.wake import _matches_wake_phrase


def test_matches_wake_phrase_aliases():
    phrases = ["hermes", "her mes", "hermies", "her miss"]
    assert _matches_wake_phrase("hermes", phrases)
    assert _matches_wake_phrase("her mes", phrases)
    assert _matches_wake_phrase("okay hermies", phrases)
    assert _matches_wake_phrase("her miss", phrases)


def test_does_not_match_unrelated_text():
    assert not _matches_wake_phrase("turn on the light", ["hermes"])
