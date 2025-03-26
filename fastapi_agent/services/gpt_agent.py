import logging
import asyncio
from typing import Iterator
from fastapi_agent.services.gpt_service import call_openai_stream
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)

class GPTAgent:
    async def stream_gpt_chunks(self, query: str) -> Iterator[str]:
        response_iter = await self._call_gpt_async(query)
        if not response_iter:
            raise RuntimeError("Failed to get GPT response iterator.")

        loop = asyncio.get_event_loop()

        def get_next_chunk(iterator):
            try:
                return next(iterator)
            except StopIteration:
                return None

        while True:
            chunk = await loop.run_in_executor(None, get_next_chunk, response_iter)
            if chunk is None:
                break
            # chunk.choices[0].delta.content -> partial token
            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if hasattr(choice, "delta") and hasattr(choice.delta, "content") and choice.delta.content:
                    yield choice.delta.content

    async def generate_full_response(self, query: str) -> dict:
        partial_text = []
        async for token in self.stream_gpt_chunks(query):
            partial_text.append(token)
        full_response = "".join(partial_text)
        code = extract_code_from_reply(full_response)
        return {"response": full_response, "code": code}

    async def _call_gpt_async(self, query: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, call_openai_stream, query)