"""Suno AI client integrations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from ..models import AudioGenerationRequest, AudioGenerationResult
from ..settings import get_settings
from .base import TextGenerator


class SunoError(RuntimeError):
    """Base exception for Suno client errors."""


class SunoAuthError(SunoError):
    """Raised when authentication fails."""


class SunoRateLimitError(SunoError):
    """Raised when Suno returns a rate limit response."""


class SunoServiceError(SunoError):
    """Raised when the Suno service returns an unexpected error."""


class SunoClient:
    """HTTP client for interacting with Suno AI."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.suno_api_key
        if not self.api_key:
            raise SunoAuthError("SUNO_API_KEY is required to use the Suno client.")

        self.base_url = (base_url or settings.suno_base_url).rstrip("/")
        self.model = model or settings.suno_model
        self.timeout = timeout or settings.suno_timeout
        if client is not None:
            self._client = client
        else:
            transport = httpx.HTTPTransport(retries=3)
            self._client = httpx.Client(timeout=self.timeout, transport=transport)

    # --------------------------------------------------------------------- text
    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate text such as lyrics/briefs."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = self._request("POST", "/v1/generate", json=payload)
        return self._extract_text(data)

    # -------------------------------------------------------------------- audio
    def generate_audio(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Submit an audio generation job to Suno."""

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": request.prompt,
            "metadata": {
                "title": request.title,
                "tags": request.tags,
                "style": request.style,
                "duration_seconds": request.duration_seconds,
                "instrumental": request.instrumental,
            },
        }
        if request.continue_clip_id:
            payload["continue_clip_id"] = request.continue_clip_id

        data = self._request("POST", "/v1/music/generate", json=payload)
        return self._parse_audio_response(data)

    def poll_audio_task(self, task_id: str) -> AudioGenerationResult:
        """Poll a previously submitted audio generation task."""

        data = self._request("GET", f"/v1/music/tasks/{task_id}")
        return self._parse_audio_response(data)

    def ping(self) -> None:
        """Perform a lightweight status check against the Suno API."""

        try:
            self._request("GET", "/v1/status")
        except SunoError as exc:  # pragma: no cover - network dependent
            raise SunoServiceError(f"Suno status check failed: {exc}") from exc

    # ------------------------------------------------------------------ helpers
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, *, json: Dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self._client.request(method, url, headers=self._headers(), json=json)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.RequestError as exc:
            raise SunoServiceError(f"Suno request failed: {exc}") from exc

        if not response.content:
            return {}
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise SunoServiceError(f"Invalid JSON response from Suno: {exc}") from exc

    @staticmethod
    def _map_status_error(exc: httpx.HTTPStatusError) -> SunoError:
        status = exc.response.status_code
        body = exc.response.text
        if status in {401, 403}:
            return SunoAuthError("Suno authentication failed. Check SUNO_API_KEY.")
        if status == 429:
            return SunoRateLimitError("Suno rate limit exceeded. Please retry later.")
        message = f"Suno request failed with status {status}: {body}"
        return SunoServiceError(message)

    @staticmethod
    def _extract_text(payload: Any) -> str:
        """Attempt to resolve text output from varying Suno response shapes."""

        if isinstance(payload, dict):
            text = payload.get("text") or payload.get("result")
            if text:
                return str(text)

            choices = payload.get("choices")
            if isinstance(choices, list) and choices:
                choice = choices[0]
                if isinstance(choice, dict):
                    if "text" in choice:
                        return str(choice["text"])
                    message = choice.get("message")
                    if isinstance(message, dict) and "content" in message:
                        return str(message["content"])

            data = payload.get("data")
            if isinstance(data, list) and data:
                first = data[0]
                if isinstance(first, dict):
                    for key in ("text", "result", "content", "lyrics"):
                        if key in first and first[key]:
                            return str(first[key])
                return str(first)

        return str(payload)

    @staticmethod
    def _parse_audio_response(data: Any) -> AudioGenerationResult:
        """Normalise audio response payloads."""

        if isinstance(data, list):
            data = data[0]

        if not isinstance(data, dict):
            raise SunoServiceError(f"Unexpected audio response payload: {data}")

        task_id = data.get("task_id") or data.get("id") or ""
        status = data.get("status") or data.get("state") or "unknown"

        audio_url = (
            data.get("audio_url")
            or data.get("audio")
            or data.get("audio_file")
            or None
        )
        preview_url = data.get("preview_url") or data.get("preview_audio")
        lyric = data.get("lyric") or data.get("lyrics")
        image_url = data.get("image_url") or data.get("cover_art")
        metadata = data.get("metadata") or {}

        return AudioGenerationResult(
            task_id=str(task_id),
            status=str(status),
            audio_url=audio_url,
            preview_url=preview_url,
            lyric=lyric,
            image_url=image_url,
            metadata=metadata if isinstance(metadata, dict) else {},
        )


class SunoTextGenerator(TextGenerator):
    """Adapter that conforms to the TextGenerator protocol."""

    def __init__(self, client: Optional[SunoClient] = None) -> None:
        self.client = client or SunoClient()

    def __call__(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        return self.client.generate_text(prompt, temperature=temperature, max_tokens=max_tokens)


@dataclass
class SunoAudioEngine:
    """Generate audio tracks through Suno."""

    client: SunoClient | None = None

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = SunoClient()

    def generate(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Submit a generation request and return the initial result."""

        return self.client.generate_audio(request)

    def poll(self, task_id: str) -> AudioGenerationResult:
        """Retrieve the latest status for a task."""

        return self.client.poll_audio_task(task_id)
