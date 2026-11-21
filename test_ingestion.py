
import asyncio

from app.db.session import AsyncSessionLocal
from app.services.knowledge.ingestion import (
    document_ingestion_service,
)


async def main():
    sample_text = """
    KADY CUSTOMER SUPPORT POLICY

    Refund Policy:
    Customers can request a refund within 14 days
    of purchasing a service.

    Refund requests must include a valid transaction ID.

    Customer Support:
    Customer support is available Monday to Friday,
    from 8:00 AM to 5:00 PM.

    Account Management:
    Customers can request assistance with account
    registration, password recovery, and profile updates.
    """

    async with AsyncSessionLocal() as db:
        result = await document_ingestion_service.ingest_document(
            db=db,
            filename="customer_policy.txt",
            file_content=sample_text.encode("utf-8"),
        )

        print("\nDocument ingestion successful!")
        print(f"Document ID: {result['document_id']}")
        print(f"Title: {result['title']}")
        print(f"Status: {result['status']}")
        print(f"Total chunks: {result['total_chunks']}")
        print(result["message"])


if __name__ == "__main__":
    asyncio.run(main())
