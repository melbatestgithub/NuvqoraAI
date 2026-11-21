
import asyncio

from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal, engine
from app.models.conversation import Conversation
from app.models.message import Message


async def main():
    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )

        conversation = result.scalar_one_or_none()

        if not conversation:
            print("No conversation found.")
            return

        count_result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation.id
            )
        )

        message_count = count_result.scalar_one()

        print("\n--- CONVERSATION MEMORY STATUS ---")
        print("Conversation ID:", conversation.id)
        print("Total messages:", message_count)
        print("Summary:", conversation.summary)
        print(
            "Summarized messages:",
            conversation.summary_message_count
        )
        print("Updated at:", conversation.summary_updated_at)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
