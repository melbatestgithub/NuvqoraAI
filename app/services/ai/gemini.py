
from typing import AsyncIterator

from google import genai
from google.genai import types

from app.core.config import settings


class GeminiService:
    """Reusable asynchronous Gemini client for Nuvqora."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing. Check your .env file."
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                api_version="v1beta"
            ),
        )

        self.model = settings.GEMINI_CHAT_MODEL

    # --------------------------------------------------
    # SHARED GENERATION CONFIGURATION
    # --------------------------------------------------

    def _get_generation_config(
        self,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> types.GenerateContentConfig:
        """
        Shared Gemini configuration.

        Google Search grounding allows Gemini to retrieve current
        public information when needed.
        """

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ],
        )

    # --------------------------------------------------
    # STANDARD GENERATION
    # --------------------------------------------------

    async def generate_response(
        self,
        message: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> str:

        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=message,
                config=self._get_generation_config(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except Exception as error:
            raise RuntimeError(
                f"Gemini response generation failed: {error}"
            ) from error

    async def generate_chat_response(
        self,
        messages: list[dict[str, str]],
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> str:

        if not messages:
            raise ValueError(
                "Conversation history cannot be empty."
            )

        try:
            contents = [
                types.Content(
                    role=(
                        "model"
                        if item["role"] == "assistant"
                        else "user"
                    ),
                    parts=[
                        types.Part(text=item["content"])
                    ],
                )
                for item in messages
                if item["role"] in ("user", "assistant")
            ]

            if not contents:
                raise ValueError(
                    "No valid conversation messages provided."
                )

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=self._get_generation_config(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except Exception as error:
            raise RuntimeError(
                f"Gemini chat generation failed: {error}"
            ) from error

    # --------------------------------------------------
    # STREAMING GENERATION
    # --------------------------------------------------

    async def generate_response_stream(
        self,
        message: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Generate a response and yield text as Gemini produces it."""

        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")

        try:
            stream = await (
                self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=message,
                    config=self._get_generation_config(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                )
            )

            has_content = False

            async for chunk in stream:
                chunk_text = chunk.text

                if chunk_text:
                    has_content = True
                    yield chunk_text

            if not has_content:
                raise RuntimeError(
                    "Gemini returned an empty streaming response."
                )

        except Exception as error:
            raise RuntimeError(
                f"Gemini streaming generation failed: {error}"
            ) from error

    async def generate_chat_response_stream(
        self,
        messages: list[dict[str, str]],
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream a response using multi-turn conversation history."""

        if not messages:
            raise ValueError(
                "Conversation history cannot be empty."
            )

        try:
            contents = [
                types.Content(
                    role=(
                        "model"
                        if item["role"] == "assistant"
                        else "user"
                    ),
                    parts=[
                        types.Part(text=item["content"])
                    ],
                )
                for item in messages
                if item["role"] in ("user", "assistant")
            ]

            if not contents:
                raise ValueError(
                    "No valid conversation messages provided."
                )

            stream = await (
                self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=self._get_generation_config(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                )
            )

            has_content = False

            async for chunk in stream:
                chunk_text = chunk.text

                if chunk_text:
                    has_content = True
                    yield chunk_text

            if not has_content:
                raise RuntimeError(
                    "Gemini returned an empty streaming response."
                )

        except Exception as error:
            raise RuntimeError(
                f"Gemini chat streaming failed: {error}"
            ) from error

    # --------------------------------------------------
    # CLIENT CLEANUP
    # --------------------------------------------------

    async def close(self):
        """Close the asynchronous Gemini client."""

        await self.client.aio.aclose()


# Reusable service instance
gemini_service = GeminiService()
