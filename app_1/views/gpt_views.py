import json
import re
import logging

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from app_1.prompts.gpt_prompt_utils import GPT_REAL_TIME_SYSTEM_PROMPT
from app_1.prompts.llama_prompt_local_run import LOCAL_HIJACKING, LOCAL_OUTAGE, LOCAL_AS_PATH_ANALYSYS, LOCAL_DEFAULT
from app_1.utils.extract_code_from_reply import extract_code_from_reply
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

# Initialize OpenAI client (this might be done in a separate module/service)
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt4_output(query):
    """Retrieve GPT-4 mini output based on the query content."""
    if "real-time" in query.lower():
        system_prompt = GPT_REAL_TIME_SYSTEM_PROMPT
    elif "hijacking" in query.lower() or "hijack" in query.lower():
        system_prompt = LOCAL_HIJACKING
    elif "outage" in query.lower():
        system_prompt = LOCAL_OUTAGE
    elif "as path" in query.lower():
        system_prompt = LOCAL_AS_PATH_ANALYSYS
    else:
        system_prompt = LOCAL_DEFAULT
        
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

@csrf_exempt
def gpt_4o_mini(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

    if not query:
        return JsonResponse({"status": "error", "message": "No query provided"}, status=400)
    
    # Ensure the session exists
    if not request.session.session_key:
        request.session.save()
    
    logger.info(f"gpt_4o_mini - Session ID: {request.session.session_key}")
    
    def event_stream():
        try:
            # Send 'generating_started' status
            yield f"data: {json.dumps({'status': 'generating_started'})}\n\n"

            response = get_gpt4_output(query)
            if response is None:
                raise Exception("Failed to get assistant's reply.")

            assistant_reply_content = ''
            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta'):
                        delta = choice.delta
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            assistant_reply_content += content
                            yield f"data: {json.dumps({'status': 'generating', 'generated_text': content})}\n\n"

            code = extract_code_from_reply(assistant_reply_content)
            logger.info(f"Generated code: {code}")
            if code:
                request.session['generated_code'] = code
                request.session.modified = True
                request.session.save()
                yield f"data: {json.dumps({'status': 'code_ready', 'code': code})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'no_code_found'})}\n\n"

        except Exception as e:
            logger.error(f"Error in gpt_4o_mini view: {str(e)}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')