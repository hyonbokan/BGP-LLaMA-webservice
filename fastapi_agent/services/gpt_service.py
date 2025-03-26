import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from prompts.gpt_prompt_utils import GPT_REAL_TIME_SYSTEM_PROMPT
from prompts.llama_prompt_local_run import LOCAL_HIJACKING, LOCAL_OUTAGE, LOCAL_AS_PATH_ANALYSYS, LOCAL_DEFAULT
load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


def determine_system_prompt(query: str) -> str:
    lower_query = query.lower()
    if "real-time" in lower_query:
        return GPT_REAL_TIME_SYSTEM_PROMPT
    elif "hijacking" in lower_query:
        return LOCAL_HIJACKING
    elif "outage" in lower_query:
        return LOCAL_OUTAGE
    elif "as path" in lower_query:
        return LOCAL_AS_PATH_ANALYSYS
    else:
        return LOCAL_DEFAULT

def call_openai_stream(query: str):
    system_prompt = determine_system_prompt(query)
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