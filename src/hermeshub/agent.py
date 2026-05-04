import base64
import shlex
import subprocess

import requests


class AgentUnavailableError(RuntimeError):
    pass


class HermesAgentClient:
    def __init__(self, config):
        self.config = config

    def ask(self, text, image_path=None, wake=None):
        if self.config.command:
            return self._ask_command(text, image_path=image_path, wake=wake)

        prompt = _prompt_with_system(text, self.config.system_prompt, image_path=image_path)
        payload = {
            "message": prompt,
            "text": text,
            "source": "hermeshub",
            "system": self.config.system_prompt,
            "system_prompt": self.config.system_prompt,
            "instructions": self.config.system_prompt,
        }
        if image_path:
            payload["image_path"] = image_path
        if wake:
            payload["wake"] = wake

        url = self.config.agent_url.rstrip("/") + "/chat"
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.request_timeout_seconds,
            )
        except requests.exceptions.RequestException as exc:
            raise AgentUnavailableError(
                f"Could not reach Hermes agent at {url}. Start the agent HTTP server "
                "or set assistant.command to a local Hermes command."
            ) from exc
        response.raise_for_status()
        data = response.json()
        return _reply_from_response(data)

    def _ask_command(self, text, image_path=None, wake=None):
        prompt = _prompt_with_system(text, self.config.system_prompt, image_path=image_path)
        command = self.config.command.format(
            prompt=shlex.quote(prompt),
            text=shlex.quote(text),
            prompt_b64=base64.b64encode(prompt.encode("utf-8")).decode("ascii"),
            text_b64=base64.b64encode(text.encode("utf-8")).decode("ascii"),
            image_path=shlex.quote(image_path or ""),
            wake=shlex.quote(str(wake or "")),
        )
        try:
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=self.config.request_timeout_seconds,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            if not detail:
                detail = f"exit code {exc.returncode}"
            raise AgentUnavailableError(f"Hermes command failed: {detail}") from exc
        except subprocess.TimeoutExpired as exc:
            raise AgentUnavailableError("Hermes command timed out") from exc
        return result.stdout.strip()


def _prompt_with_system(text, system_prompt, image_path=None):
    parts = []
    if system_prompt:
        parts.append(f"System instructions:\n{system_prompt.strip()}")
    parts.append(f"User said:\n{text}")
    if image_path:
        parts.append(f"Camera frame path from HermesHub:\n{image_path}")
    parts.append("Answer:")
    return "\n\n".join(parts)


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


def is_backend_error(reply):
    lowered = (reply or "").lower()
    return any(
        marker in lowered
        for marker in (
            "failed to execute:",
            "error invoking",
            "exceeded your current quota",
            "rate-limit",
            "rate limit",
        )
    )
