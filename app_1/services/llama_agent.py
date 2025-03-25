import asyncio
import logging
from app_1.utils.model_loader_sse import load_model
from app_1.prompts.llama_prompt_local_run import BASE_SETUP
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)

class LlamaAgent:
    def __init__(self):
        # Load the model, tokenizer, and streamer factory once at startup.
        self.model, self.tokenizer, self.streamer_factory = load_model()
        self.base_setup = BASE_SETUP

    def stream_tokens(self, query: str, context: str = ""):
        """
        Prepares the generation process and returns an iterator over generated tokens.
        Generation is started in a background thread.
        """
        full_query = (context + "\n" if context else "") + self.base_setup + query

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

        # Set up generation parameters.
        generation_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "streamer": streamer,
            "max_new_tokens": 100,
            "do_sample": True,
            "temperature": 0.1,
            "repetition_penalty": 1.1,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "early_stopping": True,
        }

        # Start generation in the background so that tokens can be yielded as soon as they're produced.
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: self.model.generate(**generation_kwargs))
        
        # Return the streamer (which is an iterator over tokens).
        return streamer

    async def generate_response(self, query: str, context: str = "") -> dict:
        """
        Generates the complete response by accumulating tokens.
        This method is used for non-streaming endpoints.
        """
        streamer = self.stream_tokens(query, context)
        assistant_reply_content = ""
        loop = asyncio.get_event_loop()

        # Helper to get the next token.
        def get_next_token():
            try:
                return next(streamer)
            except StopIteration:
                return None

        # Loop until the streamer is exhausted.
        while True:
            new_text = await loop.run_in_executor(None, get_next_token)
            if new_text is None:
                break
            assistant_reply_content += new_text

        code = extract_code_from_reply(assistant_reply_content)
        logger.info("Generated response with code: %s", code)
        return {"response": assistant_reply_content, "code": code}