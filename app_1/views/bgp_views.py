import json
import logging
import re
import traceback
from threading import Thread

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from app_1.utils.model_loader import load_model
from app_1.prompts.llama_prompt_local_run import BASE_SETUP
from app_1.utils import extract_code_from_reply

logger = logging.getLogger(__name__)

@csrf_exempt
def bgp_llama(request):
    """
    Processes a query for the LLaMA-based model and streams back a response.
    """
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({"status": "error", "message": "No query provided"}, status=400)

    # Ensure the session is saved and has a session_key.
    if not request.session.session_key:
        request.session.save()

    session_id = request.session.session_key
    logger.info(f"LLaMA Session ID for current request: {session_id}")

    try:
        system_prompt = BASE_SETUP
        logger.info(f"System prompt: {system_prompt}")
        full_input = system_prompt + query

        response_stream = generate_llm_response(full_input, request)
        response = StreamingHttpResponse(response_stream, content_type="text/event-stream")
        response['X-Accel-Buffering'] = 'no'
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        return response

    except Exception as e:
        logger.error(f"Error in bgp_llama view: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def generate_llm_response(query, request):
    """
    Streams model tokens back to the client as they are generated.
    """
    try:
        # Load your model, tokenizer, and streamer.
        model, tokenizer, streamer = load_model()

        inputs = tokenizer(
            query,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=1500
        )
        input_ids = inputs.input_ids.to(model.device)
        attention_mask = inputs.attention_mask.to(model.device)
        
        generation_kwargs = dict(
            input_ids=input_ids,
            attention_mask=attention_mask,
            streamer=streamer,
            max_new_tokens=912,
            do_sample=True,
            temperature=0.1,
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )

        def generate():
            model.generate(**generation_kwargs)

        generation_thread = Thread(target=generate)
        generation_thread.start()

        assistant_reply_content = ''

        # Stream tokens as they are produced.
        for new_text in streamer:
            assistant_reply_content += new_text
            data = json.dumps({"status": "generating", "generated_text": new_text})
            yield f"data: {data}\n\n"

        generation_thread.join()

        # Extract code from the reply.
        code = extract_code_from_reply(assistant_reply_content)
        if code:
            request.session['generated_code'] = code
            request.session.modified = True
            request.session.save()

        if code:
            yield f"data: {json.dumps({'status': 'code_ready', 'code': code})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'no_code_found'})}\n\n"

    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
