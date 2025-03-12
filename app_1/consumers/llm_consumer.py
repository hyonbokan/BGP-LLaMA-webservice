
import json
import logging
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from app_1.utils.model_loader import load_model
from app_1.prompts.llama_prompt_local_run import BASE_SETUP
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)

# Pre-load the model, tokenizer, and streamer factory at server startup.
MODEL, TOKENIZER, STREAMER_FACTORY = load_model()

class LLMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.session = self.scope["session"]
        logger.info("LLMConsumer connected, session id: %s", self.session.session_key)

    async def disconnect(self, close_code):
        logger.info("LLMConsumer disconnected, session id: %s", self.session.session_key)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            query = data.get("query", "")
            if not query:
                await self.send(json.dumps({"status": "error", "message": "No query provided"}))
                return

            full_query = BASE_SETUP + query
            await self.send(json.dumps({"status": "generating_started"}))

            # Create a fresh streamer using the factory
            streamer = STREAMER_FACTORY()

            inputs = TOKENIZER(
                full_query,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=1500
            )
            input_ids = inputs.input_ids.to(MODEL.device)
            attention_mask = inputs.attention_mask.to(MODEL.device)

            generation_kwargs = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "streamer": streamer,
                "max_new_tokens": 912,
                "do_sample": True,
                "temperature": 0.1,
                "repetition_penalty": 1.1,
                "eos_token_id": TOKENIZER.eos_token_id,
                "pad_token_id": TOKENIZER.pad_token_id,
                "early_stopping": True,
            }

            loop = asyncio.get_event_loop()
            generation_future = loop.run_in_executor(None, lambda: MODEL.generate(**generation_kwargs))
            assistant_reply_content = ""

            # Helper to get next token safely
            def get_next_token(streamer):
                try:
                    return next(streamer)
                except StopIteration:
                    return None

            while True:
                new_text = await loop.run_in_executor(None, get_next_token, streamer)
                if new_text is None:
                    break
                assistant_reply_content += new_text
                await self.send(json.dumps({"status": "generating", "generated_text": new_text}))

            await generation_future

            code = extract_code_from_reply(assistant_reply_content)
            if code:
                self.session["generated_code"] = code
                await sync_to_async(self.session.save)()
                await self.send(json.dumps({"status": "code_ready", "code": code}))
            else:
                await self.send(json.dumps({"status": "no_code_found"}))
            
            await self.close()
            
        except Exception as e:
            logger.error("Error in LLMConsumer: %s", str(e))
            await self.send(json.dumps({"status": "error", "message": str(e)}))

