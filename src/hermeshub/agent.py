import requests


class HermesAgentClient:
    def __init__(self, config):
        self.config = config

    def ask(self, text, image_path=None, wake=None):
        payload = {
            "message": text,
            "text": text,
            "source": "hermeshub",
        }
        if image_path:
            payload["image_path"] = image_path
        if wake:
            payload["wake"] = wake

        response = requests.post(
            self.config.agent_url.rstrip("/") + "/chat",
            json=payload,
            timeout=self.config.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return _reply_from_response(data)


def _reply_from_response(data):
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return ""
    for key in ("reply", "response", "text", "message", "content"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if isinstance(data.get("choices"), list) and data["choices"]:
        first = data["choices"][0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"].strip()
    return ""
