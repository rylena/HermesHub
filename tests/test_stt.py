from hermeshub.stt import _parse_result


def test_parse_vosk_result_text():
    assert _parse_result('{"text": "hello hermes"}') == "hello hermes"


def test_parse_vosk_result_missing_text():
    assert _parse_result('{"partial": "hello"}') == ""


def test_parse_vosk_result_bad_json():
    assert _parse_result("not json") == ""
