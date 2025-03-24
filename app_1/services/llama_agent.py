
import asyncio
import logging
from app_1.utils.model_loader import load_model
from app_1.prompts.llama_prompt_local_run import BASE_SETUP
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)

class LlamaAgent:
    def __init__(self):
        # Load the model, tokenizer, and streamer factory once.
        self.model, self.tokenizer, self.streamer_factory = load_model()

    async def generate_response(self, query: str, context: str = "") -> dict:
        # Build the full prompt with optional context injection (MCP)
        # the context could be a conversation history.
        full_query = (context + "\n" if context else "") + BASE_SETUP + query

        # Create a fresh streamer instance.
        streamer = self.streamer_factory()

        # Tokenize the input.
        inputs = self.tokenizer(
            full_query,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=1500
        )
        input_ids = inputs.input_ids.to(self.model.device)
        attention_mask = inputs.attention_mask.to(self.model.device)

        generation_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "streamer": streamer,
            "max_new_tokens": 912,
            "do_sample": True,
            "temperature": 0.1,
            "repetition_penalty": 1.1,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "early_stopping": True,
        }

        loop = asyncio.get_event_loop()
        generation_future = loop.run_in_executor(None, lambda: self.model.generate(**generation_kwargs))
        assistant_reply_content = ""

        # Helper to get tokens safely.
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

        await generation_future

        code = extract_code_from_reply(assistant_reply_content)
        logger.info("Generated response with code: %s", code)
        return {"response": assistant_reply_content, "code": code}