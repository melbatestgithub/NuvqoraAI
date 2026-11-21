
from google.genai import types

from app.services.ai.gemini import gemini_service
from app.core.config import settings


class EmbeddingService:
    """Generate semantic text embeddings using Gemini."""

    def __init__(self):
        self.client = gemini_service.client
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text.strip(),
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimensions,
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )

            embedding = response.embeddings[0].values

            if len(embedding) != self.dimensions:
                raise ValueError(
                    f"Expected {self.dimensions} dimensions, "
                    f"received {len(embedding)}."
                )

            return list(embedding)

        except Exception as error:
            raise RuntimeError(
                f"Embedding generation failed: {error}"
            ) from error

    async def generate_query_embedding(
        self,
        text: str
    ) -> list[float]:
        """Generate an embedding optimized for search queries."""

        if not text or not text.strip():
            raise ValueError("Query cannot be empty.")

        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text.strip(),
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimensions,
                    task_type="RETRIEVAL_QUERY",
                ),
            )

            embedding = response.embeddings[0].values

            if len(embedding) != self.dimensions:
                raise ValueError(
                    f"Expected {self.dimensions} dimensions, "
                    f"received {len(embedding)}."
                )

            return list(embedding)

        except Exception as error:
            raise RuntimeError(
                f"Query embedding generation failed: {error}"
            ) from error

    async def generate_batch_embeddings(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for multiple documents."""

        if not texts:
            raise ValueError("Text list cannot be empty.")

        if any(not text or not text.strip() for text in texts):
            raise ValueError("All texts must contain content.")

        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=[text.strip() for text in texts],
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimensions,
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )

            embeddings = [
                list(item.values)
                for item in response.embeddings
            ]

            if len(embeddings) != len(texts):
                raise ValueError("Embedding count does not match input count.")

            if any(len(item) != self.dimensions for item in embeddings):
                raise ValueError("Unexpected embedding dimensions.")

            return embeddings

        except Exception as error:
            raise RuntimeError(
                f"Batch embedding generation failed: {error}"
            ) from error


embedding_service = EmbeddingService()
