
import asyncio
from sqlalchemy import text
from app.db.session import engine


async def main():
    async with engine.connect() as connection:
        result = await connection.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'conversations'
                AND column_name IN (
                    'summary',
                    'summary_updated_at'
                )
                ORDER BY column_name
            """)
        )

        columns = [row[0] for row in result.fetchall()]

        print("Memory columns:", columns)

        assert "summary" in columns
        assert "summary_updated_at" in columns

        print("Conversation memory migration successful!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
