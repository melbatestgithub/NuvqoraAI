
import asyncio

from app.db.session import AsyncSessionLocal
from app.services.knowledge.retrieval import (
    knowledge_retrieval_service,
)


async def main():
    questions = [
        "How long do customers have to request a refund?",
        "When is customer support available?",
        "Can Kady help customers recover their passwords?",
        "What is the company's refund policy?",
    ]

    async with AsyncSessionLocal() as db:

        for question in questions:
            print("\n" + "=" * 70)
            print(f"QUESTION: {question}")
            print("=" * 70)

            results = (
                await knowledge_retrieval_service.search_knowledge(
                    db=db,
                    query=question,
                    top_k=3,
                )
            )

            if not results:
                print("No relevant knowledge found.")
                continue

            for index, item in enumerate(results, start=1):
                print(f"\nResult {index}")
                print(f"Document: {item['document_title']}")
                print(f"Similarity: {item['similarity']}")
                print(f"Chunk: {item['chunk_index']}")
                print(f"Content:\n{item['content']}")

    print("\nSemantic retrieval tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
