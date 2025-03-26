from threading import Thread
import asyncio
from app_1.utils.model_loader import load_model
from app_1.prompts.llama_prompt_local_run import BASE_SETUP
from app_1.utils.extract_code_from_reply import extract_code_from_reply

class LlamaAgent:
    def __init__(self):
        # Load model, tokenizer, and streamer factory once.
        self.model, self.tokenizer, self.streamer_factory = load_model()
        self.base_setup = BASE_SETUP

    def stream_tokens(self, query: str, context: str = ""):
        """
        Prepare generation and return a tuple (streamer, thread).
        The thread runs model.generate() in the background and the streamer yields tokens.
        """
        full_query = (context + "\n" if context else "") + self.base_setup + query

        # Create a fresh streamer instance.
        streamer = self.streamer_factory()

        # Tokenize input.
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
            # "use_cache": False,
        }

        # Start generation in a separate thread.
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        return streamer, thread

    async def generate_response(self, query: str, context: str = "") -> dict:
        """
        Accumulate tokens to form the full response (non-streaming).
        """
        streamer, thread = self.stream_tokens(query, context)
        assistant_reply_content = ""
        loop = asyncio.get_event_loop()

        def get_next_token():
            try:
                return next(streamer)
            except StopIteration:
                return None

        while True:
            new_text = await loop.run_in_executor(None, get_next_token)
            if new_text is None:
                break
            assistant_reply_content += new_text

        thread.join()
        code = extract_code_from_reply(assistant_reply_content)
        return {"response": assistant_reply_content, "code": code}