
import asyncio

from app.services.ai.gemini import gemini_service
from app.services.ai.prompts import KADY_SYSTEM_PROMPT


async def main():
    try:
        print("Testing Kady Gemini connection...")

        response = await gemini_service.generate_response(
            message="Hello Kady! Introduce yourself briefly.",
            system_instruction=KADY_SYSTEM_PROMPT,
        )

        print("\nKady response:")
        print(response)

        print("\nGemini integration successful!")

    except Exception as error:
        print(f"\nGemini test failed: {error}")

    finally:
        await gemini_service.close()


if __name__ == "__main__":
    asyncio.run(main())
