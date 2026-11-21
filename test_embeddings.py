
import asyncio

from app.services.ai.embeddings import embedding_service
from app.services.ai.gemini import gemini_service


async def main():
    try:
        print("Testing Kady embedding service...")

        # Test document embedding
        document = (
            "Kady is an AI customer support assistant "
            "that helps customers resolve their questions."
        )

        document_vector = await embedding_service.generate_embedding(
            document
        )

        print("\nDocument embedding:")
        print(f"Dimensions: {len(document_vector)}")
        print(f"First 5 values: {document_vector[:5]}")

        # Test query embedding
        query = "What does Kady help customers with?"

        query_vector = await embedding_service.generate_query_embedding(
            query
        )

        print("\nQuery embedding:")
        print(f"Dimensions: {len(query_vector)}")

        # Test batch embeddings
        texts = [
            "Kady provides customer support.",
            "Customers can request human assistance.",
            "Businesses can upload knowledge documents.",
        ]

        batch_vectors = (
            await embedding_service.generate_batch_embeddings(texts)
        )

        print("\nBatch embedding:")
        print(f"Documents: {len(batch_vectors)}")
        print(f"Dimensions per document: {[len(v) for v in batch_vectors]}")

        print("\nEmbedding integration successful!")

    except Exception as error:
        print(f"\nEmbedding test failed: {error}")

    finally:
        await gemini_service.close()


if __name__ == "__main__":
    asyncio.run(main())
