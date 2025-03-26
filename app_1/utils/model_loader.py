from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig, TextIteratorStreamer
import logging
import os
from threading import Lock

logger = logging.getLogger(__name__)
CUSTOM_MODEL = "hyonbokan/bgp-llama-3.1-instruct-10kSteps-2kDataset"
LLAMA_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
model = None
tokenizer = None
model_lock = Lock()

def load_model():
    global model, tokenizer
    with model_lock:
        if model is None or tokenizer is None:
            try:
                model_id = CUSTOM_MODEL
                hf_auth = os.environ.get('hf_token')
                model_config = AutoConfig.from_pretrained(model_id, use_auth_token=hf_auth)
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    config=model_config,
                    device_map='auto',
                    use_auth_token=hf_auth
                )
                tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=hf_auth)
                # Set tokenizer options
                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.padding_side = "left"
                tokenizer.truncation_side = "left"
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load the model: {str(e)}")
                raise
    # Create a factory callable that returns a fresh TextIteratorStreamer per query.
    streamer_factory = lambda: TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    return model, tokenizer, streamer_factory
