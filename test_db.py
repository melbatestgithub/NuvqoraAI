import asyncio
from sqlalchemy import text
from app.db.session import engine


async def test_connection():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT version()")
            )

            print("Database connected successfully!")
            print(result.scalar())

    except Exception as error:
        print("Database connection failed:")
        print(error)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())