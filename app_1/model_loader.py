from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, pipeline
import os
from langchain.llms.huggingface_pipeline import HuggingFacePipeline

class ModelContainer:
    model_pipeline = None

    @classmethod
    def load_model(cls):
        if cls.model_pipeline is None:
            model_id = 'hyonbokan/BGP-LLaMA7-BGPStream-5k-cutoff-1024-max-2048'
            hf_auth = os.environ.get('hf_token')

            model_config = AutoConfig.from_pretrained(
                model_id,
                use_auth_token=hf_auth
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True,
                config=model_config,
                device_map='auto',
                use_auth_token=hf_auth
            )
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                use_auth_token=hf_auth
            )
            # tokenizer.eos_token_id = 2 # pad id changed according to the suggestion
            # tokenizer.pad_token = tokenizer.eos_token
            # tokenizer.padding_side = "right"
            
            cls.model_pipeline = pipeline(
                task="text-generation", 
                return_full_text=True,
                model=model, 
                tokenizer=tokenizer, 
                max_length=724,
                repetition_penalty=1.1
                )
            
            # model_pipeline = pipeline(
            #     task="text-generation", 
            #     return_full_text=True,
            #     model=model, 
            #     tokenizer=tokenizer, 
            #     max_length=724,
            #     repetition_penalty=1.1
            #     )
            # cls.llm = HuggingFacePipeline(pipeline=model_pipeline)

        return cls.model_pipeline