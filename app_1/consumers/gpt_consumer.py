import json
import logging
import asyncio
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from prompts.gpt_prompt_utils import GPT_REAL_TIME_SYSTEM_PROMPT
from prompts.llama_prompt_local_run import LOCAL_HIJACKING, LOCAL_OUTAGE, LOCAL_AS_PATH_ANALYSYS, LOCAL_DEFAULT
from app_1.utils.extract_code_from_reply import extract_code_from_reply
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client.
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt4_output(query):
    """
    Calls the OpenAI API to stream GPT-4o-mini output.
    """
    if "real-time" in query.lower():
        system_prompt = GPT_REAL_TIME_SYSTEM_PROMPT
    elif "hijacking" in query.lower() or "hijack" in query.lower():
        system_prompt = LOCAL_HIJACKING
    elif "outage" in query.lower():
        system_prompt = LOCAL_OUTAGE
    elif "as path" in query.lower():
        system_prompt = LOCAL_AS_PATH_ANALYSYS
    else:
        system_prompt = LOCAL_DEFAULT

    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=2000,
            temperature=0.7,
            stream=True,
        )
        return response
    except Exception as e:
        logger.error(f"Error during API call: {e}")
        return None

class GPTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.session = self.scope["session"]
        logger.info("GPTConsumer connected, session id: %s", self.session.session_key)

    async def disconnect(self, close_code):
        logger.info("GPTConsumer disconnected, session id: %s", self.session.session_key)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            query = data.get("query", "")
            if not query:
                await self.send(json.dumps({"status": "error", "message": "No query provided"}))
                return

            await self.send(json.dumps({"status": "generating_started"}))

            # Call OpenAI API via a sync-to-async wrapper.
            response = await sync_to_async(get_gpt4_output)(query)
            if response is None:
                raise Exception("Failed to get GPT response.")

            assistant_reply_content = ""
            loop = asyncio.get_event_loop()

            # Define a helper to safely call next() on the response iterator.
            def get_next_chunk(resp):
                try:
                    return next(resp)
                except StopIteration:
                    return None

            while True:
                chunk = await loop.run_in_executor(None, get_next_chunk, response)
                if chunk is None:
                    break
                # The API returns streaming chunks with a structure similar to:
                # { "choices": [ { "delta": { "content": "some token" } } ] }
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if hasattr(choice, "delta") and hasattr(choice.delta, "content") and choice.delta.content:
                        content = choice.delta.content
                        assistant_reply_content += content
                        await self.send(json.dumps({
                            "status": "generating",
                            "generated_text": content
                        }))
            # Once the stream is done, extract code if present.
            code = extract_code_from_reply(assistant_reply_content)
            if code:
                self.session["generated_code"] = code
                await sync_to_async(self.session.save)()
                await self.send(json.dumps({"status": "code_ready", "code": code}))
            else:
                await self.send(json.dumps({"status": "no_code_found"}))
            
            # Optionally close the WebSocket to signal completion.
            await self.close()

        except Exception as e:
            logger.error("Error in GPTConsumer: %s", str(e))
            await self.send(json.dumps({"status": "error", "message": str(e)}))
