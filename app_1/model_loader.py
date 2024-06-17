from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, TextStreamer, TextIteratorStreamer, pipeline, logging
import transformers
import logging
import os
from langchain.llms.huggingface_pipeline import HuggingFacePipeline

class ModelContainer:
    model = None
    tokenizer = None
    streamer = None
    
    @classmethod
    def load_model(cls):
        if cls.model is None or cls.tokenizer is None or cls.streamer is None:
            try:
                model_id = 'meta-llama/Llama-2-7b-hf'
                hf_auth = os.environ.get('hf_token')

                model_config = AutoConfig.from_pretrained(
                    model_id,
                    use_auth_token=hf_auth
                )
                cls.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    config=model_config,
                    device_map='auto',
                    use_auth_token=hf_auth
                )
                cls.tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    use_auth_token=hf_auth
                )
                
                cls.tokenizer.pad_token = cls.tokenizer.eos_token
                cls.tokenizer.padding_side = "right"
                
                cls.streamer = TextIteratorStreamer(cls.tokenizer)
                transformers.logging.set_verbosity(transformers.logging.CRITICAL)

                logging.info("Model and tokenizer loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load the model: {str(e)}")
                raise

        return cls.model, cls.tokenizer, cls.streamer
        
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
