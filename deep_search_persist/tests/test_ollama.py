import asyncio

from ..deep_search_persist.helper_classes import Message, Messages
from ..deep_search_persist.local_ai import call_ollama_async


async def test_ollama():
    msgs = Messages(messages=[Message(role="user", content="Say hello world")])
    resp = await call_ollama_async(None, msgs, model="gemma3:4b", max_tokens=50, ctx=256000)
    print("RESPONSE:", resp)


if __name__ == "__main__":
    asyncio.run(test_ollama())
