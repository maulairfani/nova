"""One-off setup: creates LangGraph's checkpoint tables in nova_kb.

Run once before first `docker-compose up` (or after wiping the nova_kb
volume). Usage: python setup_checkpointer.py
"""
import asyncio

from app.agent.checkpointer import get_checkpointer_cm


async def main() -> None:
    async with get_checkpointer_cm() as checkpointer:
        await checkpointer.setup()
    print("nova_kb checkpoint tables created.")


if __name__ == "__main__":
    asyncio.run(main())
