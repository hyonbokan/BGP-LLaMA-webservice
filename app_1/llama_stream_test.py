import os
import json
import logging
from threading import Lock, Thread
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    AutoConfig, 
    TextIteratorStreamer
)

# Initialize model, tokenizer, and streamer variables
model = None
tokenizer = None
streamer = None
model_lock = Lock()

def load_model():
    global model, tokenizer, streamer
    with model_lock:
        if model is None or tokenizer is None or streamer is None:
            try:
                # model_id = 'meta-llama/Llama-2-13b-chat-hf'
                model_id = 'hyonbokan/bgp-llama-knowledge-5k'
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

                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.pad_token_id = tokenizer.eos_token_id
                tokenizer.padding_side = "right"

                streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
                logging.info("Model loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load the model: {str(e)}")
                raise

    return model, tokenizer, streamer

def generate_response(prompt):
    model, tokenizer, streamer = load_model()
    
    inputs = tokenizer([prompt], return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    generation_kwargs = dict(
        inputs=inputs["input_ids"],
        streamer=streamer,
        max_new_tokens=756,  # Adjust based on your requirements
        # do_sample=True,
    )
    
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    generated_text = ""
    
    # Collect the output from the streamer
    for new_text in streamer:
        generated_text += new_text
        print(new_text, end="")
    
    thread.join()
    
    return generated_text.strip()

# user_query = "Identify timestamps where the number of routes announced by AS3356 exceeds a threshold of 150000."
# user_query = "Identify any time intervals where AS3356 had a significant increase in the number of new routes."
user_query = "Analyze the consistency of AS3356 in maintaining the same maximum path length over the monitoring period."
prompt = f"""
You are an AI assistant and your task is to answers the user query on the given BGP data. Here are some rules you always follow:
- Generate only the requested output, don't include any other language before or after the requested output..
- Your answers should be direct and include relevant timestamps when analyzing BGP data features.
- Check the collected BGP data given below. Each row represents the features collected over a specific period.
- Never say thank you, that you are happy to help, that you are an AI agent, and additional suggestions. Just answer directly.
Answer this user query: {user_query}
[TAB] col: | Timestamp | Autonomous System Number | Number of Routes | Number of New Routes | Number of Withdrawals | Number of Origin Changes | Number of Route Changes | Maximum Path Length | Average Path Length | Maximum Edit Distance | Average Edit Distance | Number of Announcements | Total Withdrawals | Number of Unique Prefixes Announced | row 1: | 2024-08-30 06:04:38 | 3356 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 158761 | 0 | 4 | [SEP]row 2: | 2024-08-30 06:05:38 | 3356 | 52 | 48 | 0 | 0 | 3 | 3 | 0.17307692307692307 | 3 | 0.1346153846153846 | 196104 | 0 | 52 | [SEP]row 3: | 2024-08-30 06:06:38 | 3356 | 1 | 0 | 0 | 0 | 1 | 5 | 5.0 | 3 | 3.0 | 162647 | 51 | 1 | [SEP]row 4: | 2024-08-30 06:07:38 | 3356 | 70 | 69 | 0 | 0 | 0 | 5 | 0.07142857142857142 | 0 | 0.0 | 141600 | 0 | 70 | [SEP]
"""
response = generate_response(prompt)
print("\n\nFinal generated response:\n")
print(response)
