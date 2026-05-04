from hermeshub.agent import _prompt_with_system, _reply_from_response


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


def test_prompt_with_system_keeps_user_text_and_short_reply_instruction():
    prompt = _prompt_with_system("tell me about mars", "Keep replies short.")

    assert "System instructions:" in prompt
    assert "Keep replies short." in prompt
    assert "User said:\ntell me about mars" in prompt
    assert prompt.endswith("Answer:")
