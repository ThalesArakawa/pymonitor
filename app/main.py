from services.pyagent import PyAgent
import asyncio

async def main() -> None:
    pyagent = PyAgent()
    await pyagent.start()

if __name__ == "__main__":
    asyncio.run(main())
