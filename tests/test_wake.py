from hermeshub.wake import _matches_wake_phrase


def test_matches_wake_phrase_aliases():
    phrases = ["hermes", "her mes", "her miss", "her knees", "harness", "armies"]
    assert _matches_wake_phrase("hermes", phrases)
    assert _matches_wake_phrase("her mes", phrases)
    assert _matches_wake_phrase("her miss", phrases)
    assert _matches_wake_phrase("her knees", ["her knees"])
    assert _matches_wake_phrase("armies", ["armies"])


def test_does_not_match_unrelated_text():
    assert not _matches_wake_phrase("turn on the light", ["hermes"])
