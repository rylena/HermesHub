from hermeshub.agent import _reply_from_response


def test_reply_from_common_shapes():
    assert _reply_from_response({"reply": "hello"}) == "hello"
    assert _reply_from_response({"response": "hello"}) == "hello"
    assert _reply_from_response({"text": "hello"}) == "hello"
    assert _reply_from_response({"message": "hello"}) == "hello"
    assert _reply_from_response({"content": "hello"}) == "hello"


def test_reply_from_openai_shape():
    data = {"choices": [{"message": {"content": "hello"}}]}
    assert _reply_from_response(data) == "hello"


def test_reply_from_empty_shape():
    assert _reply_from_response({}) == ""
