
from app.services.knowledge.document_processor import document_processor
from app.services.knowledge.chunker import document_chunker


def main():
    sample_text = """
    KADY CUSTOMER SUPPORT POLICY

    1. Refund Policy

    Customers can request a refund within 14 days
    of purchasing a service.

    Refund requests must include a valid transaction ID.

    2. Customer Support

    Customer support is available Monday to Friday,
    from 8:00 AM to 5:00 PM.

    3. Account Management

    Customers can request assistance with account
    registration, password recovery, and profile updates.
    """

    # Test TXT extraction
    extracted_text = document_processor.extract_text(
        sample_text.encode("utf-8"),
        "customer_policy.txt",
    )

    print("Document extraction successful!")
    print(f"Extracted characters: {len(extracted_text)}")

    # Test chunking
    chunks = document_chunker.split_text(extracted_text)

    print(f"\nGenerated chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks):
        print(f"\nChunk {index + 1}:")
        print(chunk)

    # Test validation
    try:
        document_processor.extract_text(
            b"",
            "empty.txt",
        )
    except ValueError as error:
        print(f"\nValidation successful: {error}")

    print("\nDocument processing tests completed!")


if __name__ == "__main__":
    main()
