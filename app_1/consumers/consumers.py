import json
import logging
import os
import re
import asyncio
import traceback

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from myapp.utils.gpt_prompt_utils import GPT_REAL_TIME_SYSTEM_PROMPT, LOCAL_HIJACKING, LOCAL_OUTAGE, LOCAL_AS_PATH_ANALYSYS, LOCAL_DEFAULT
from myapp.utils.model_loader import load_model
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

def extract_code_from_reply(reply_content):
    code_pattern = r"```python\s*\n(.*?)```"
    match = re.search(code_pattern, reply_content, re.DOTALL)
    if match:
        return match.group(1)
    return None

class GPTStreamingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.session = self.scope["session"]
        logger.info("WebSocket connected. Session: %s", self.session.session_key)

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected. Session: %s", self.session.session_key)

    async def receive(self, text_data):
        data = json.loads(text_data)
        query = data.get("query", "")
        if not query:
            await self.send(json.dumps({"status": "error", "message": "No query provided"}))
            return

        await self.send(json.dumps({"status": "generating_started"}))

        # Wrap synchronous call with sync_to_async
        response = await sync_to_async(get_gpt4_output)(query)
        if response is None:
            await self.send(json.dumps({"status": "error", "message": "API call failed"}))
            return

        assistant_reply_content = ""
        try:
            for chunk in response:
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if hasattr(choice, "delta"):
                        delta = choice.delta
                        if hasattr(delta, "content") and delta.content:
                            content = delta.content
                            assistant_reply_content += content
                            await self.send(json.dumps({
                                "status": "generating",
                                "generated_text": content
                            }))
        except Exception as e:
            logger.error("Error during streaming: %s", str(e))
            await self.send(json.dumps({"status": "error", "message": str(e)}))
            return

        code = extract_code_from_reply(assistant_reply_content)
        if code:
            self.session["generated_code"] = code
            await sync_to_async(self.session.save)()
            await self.send(json.dumps({"status": "code_ready", "code": code}))
        else:
            await self.send(json.dumps({"status": "no_code_found"}))