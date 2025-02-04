from venv import logger
from django.http import JsonResponse, FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.middleware.csrf import get_token
from .models import *
from .serializer import *
import json
from threading import Thread, Event
import queue
import os
from .model_loader import load_model
from .gpt_prompt_utils import GPT_HIST_SYSTEM_PROMPT, GPT_REAL_TIME_SYSTEM_PROMPT
from .llama_prompt_utils import LLAMA_DEFAULT_PROMPT, LLAMA_REAL_TIME_SYSTEM_PROMPT, LLAMA_PREFIX_ANALYSYS, LLAMA_AS_PATH_OPERATIONS, LLAMA_MED_COMMUNITY, LLAMA_SYSTEM_PROMPT
from .llama_prompt_local_run import LOCAL_OUTAGE, LOCAL_PREFIX_ANALYSYS, LOCAL_AS_PATH_ANALYSYS, LOCAL_DEFAULT, LOCAL_MED_COMMUNITY_ANALYSYS, LOCAL_HIJACKING
from .exec_code_util import StreamToQueue, is_code_safe
import re
import logging
import time
import traceback
from openai import OpenAI
import sys
import io
from contextlib import redirect_stdout
import signal
import pandas as pd
import pybgpstream
import datetime
import ast

logger = logging.getLogger(__name__)
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

status_update_event = Event()

def get_gpt4_output(query):
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

def extract_code_from_reply(assistant_reply_content):
    code_pattern = r"```python\s*\n(.*?)```"
    match = re.search(code_pattern, assistant_reply_content, re.DOTALL)
    if match:
        code = match.group(1)
        return code
    else:
        return None


def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed_modules = {'pandas', 'pybgpstream', 'datetime', 'matplotlib'}
    logger.info(f"Attempting to import module: {name}")
    if name in allowed_modules:
        logger.info(f"Importing '{name}' is allowed.")
        return __import__(name, globals, locals, fromlist, level)
    else:
        logger.warning(f"Importing '{name}' is not allowed.")
        raise ImportError(f"Importing '{name}' is not allowed.")

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
    
    session_id = request.session.session_key
    if session_id is None:
        request.session.save()
        session_id = request.session.session_key

    logger.info(f"gpt_4o_mini - Session ID: {session_id}")
    
    def event_stream():
        try:
            # Send 'generating_started' status
            yield f"data: {json.dumps({'status': 'generating_started'})}\n\n"

            response = get_gpt4_output(query)
            if response is None:
                raise Exception("Failed to get assistant's reply.")

            assistant_reply_content = ''

            # Stream the assistant's reply to the frontend
            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta'):
                        delta = choice.delta
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            assistant_reply_content += content
                            yield f"data: {json.dumps({'status': 'generating', 'generated_text': content})}\n\n"

            # logger.info(f"Assistant's full reply:\n{assistant_reply_content}")

            # Extract code from the assistant's reply
            code = extract_code_from_reply(assistant_reply_content)
            logger.info(f"Generated code to save:\n{code}")

            if code:
                # Save the extracted code to the session
                request.session['generated_code'] = code
                request.session.modified = True
                logger.info("Code has been saved to the session.")
                
                request.session.save()
                logger.info(f"GPT 4o mini session data after saving code: {dict(request.session.items())}")
            if code:
                yield f"data: {json.dumps({'status': 'code_ready', 'code': code})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'no_code_found'})}\n\n"


        except Exception as e:
            logger.error(f"Error in gpt_4o_mini view: {str(e)}")
            error_message = str(e)
            yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"

    # Return a StreamingHttpResponse with the event_stream generator
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

@require_http_methods(["GET"])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

@require_http_methods(["GET"])
def status_updates(request):
    return StreamingHttpResponse(status_update_stream(), content_type='text/event-stream')

def status_update_stream():
    while True:
        status_update_event.wait()  # Wait until the event is set
        status_message = get_current_status_message()  # Retrieve the current status message
        yield f'data: {json.dumps({"status": status_message})}\n\n'
        status_update_event.clear()  # Clear the event after sending the update

def get_current_status_message():
    if status_update_event.is_set():
        return "Data collection complete, ready for query."
    else:
        return "Data is being collected..."
    
@csrf_exempt
def bgp_llama(request):
    query = request.GET.get('query', '')
    session = request.session

    if not query:
        return JsonResponse({"status": "error", "message": "No query provided"}, status=400)

    # Ensure the session is saved and has a session_key
    if not session.session_key:
        session.save()

    session_id = session.session_key
    # logger.info(f"User query: {query}")
    logger.info(f"LLaMA Session ID for current request: {session_id}")

    try:
        # query_lower = query.lower()
        
        # Determine the system prompt based on the user query
        if "real-time" in query:
            system_prompt = LLAMA_REAL_TIME_SYSTEM_PROMPT
        elif "origin" in query or "unique prefixes" in query:
            system_prompt = LOCAL_PREFIX_ANALYSYS
        elif "path" in query or "as-path" in query:
            system_prompt = LOCAL_AS_PATH_ANALYSYS
        elif "MED" in query or "community" in query:
            system_prompt = LOCAL_MED_COMMUNITY_ANALYSYS
        # elif "route flapping" in query_lower:
        #     system_prompt = LLAMA_ROUTE_FLAPPING
        # elif "anomaly detection" in query_lower and "prefix announcement" in query_lower:
        #     system_prompt = LLAMA_ANOMALY_DETECTION_PREFIX
        # elif "anomaly detection" in query_lower and "as path changes" in query_lower:
        #     system_prompt = LLAMA_ANOMALY_DETECTION_AS_PATH
        # elif "anomaly detection" in query_lower and "potential hijacking" in query_lower:
        #     system_prompt = LLAMA_ANOMALY_DETECTION_HIJACKING
        else:
            system_prompt = LOCAL_DEFAULT
            
        logger.info(f"SYSTEM PROMPT: {system_prompt}")
        input = system_prompt + query
        response_stream = generate_llm_response(input, request)
        response = StreamingHttpResponse(response_stream, content_type="text/event-stream")
        response['X-Accel-Buffering'] = 'no'
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        return response
    except Exception as e:
        logger.error(f"Error in bgp_llama view: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def generate_llm_response(query, request):
    try:
        # Load the model and tokenizer
        model, tokenizer, streamer = load_model()

        # Tokenize the input query with attention mask
        inputs = tokenizer(
            query,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=1500
        )

        input_ids = inputs.input_ids.to(model.device)
        attention_mask = inputs.attention_mask.to(model.device)
        
        # Start the generation in a separate thread
        generation_kwargs = dict(
            input_ids=input_ids,
            attention_mask=attention_mask,
            streamer=streamer,
            max_new_tokens=1012,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.0,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
        def generate():
            model.generate(**generation_kwargs)

        generation_thread = Thread(target=generate)
        generation_thread.start()

        assistant_reply_content = ''

        # Stream the tokens as they are generated
        for new_text in streamer:
            # Append the new_text to assistant_reply_content
            assistant_reply_content += new_text
            # Yield the token to the client in the SSE format
            data = json.dumps({"status": "generating", "generated_text": new_text})
            yield f'data: {data}\n\n'

        # Wait for the generation thread to finish
        generation_thread.join()

        # logger.info(f"Assistant's full reply:\n{assistant_reply_content}")

        # Extract code from the assistant's reply
        code = extract_code_from_reply(assistant_reply_content)
        # logger.info(f"Generated code to save:\n{code}")

        if code:
            # Save the extracted code to the session
            request.session['generated_code'] = code
            request.session.modified = True
            logger.info("Code has been saved to the session.")
            request.session.save()
            # logger.info(f"LLaMA mini session data after saving code: {dict(request.session.items())}")
            
        if code:
            yield f"data: {json.dumps({'status': 'code_ready', 'code': code})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'no_code_found'})}\n\n"

    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        data = json.dumps({"status": "error", "message": str(e)})
        yield f'data: {data}\n\n'



@csrf_exempt
def execute_code(request):
    if request.method != 'POST':
        logger.warning("Invalid request method for execute_code.")
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
    
    session_id = request.session.session_key
    logger.info(f"execute_code - Session ID: {session_id}")

    try:
        # logger.info(f"Session data: {request.session.items()}")
        
        # Retrieve the code from the session
        code = request.session.get('generated_code', None)
        # logger.info(f"Retrieved generated_code from session: {code}")
        if not code:
            return JsonResponse({"status": "error", "message": "No code available to execute."}, status=400)

        # Clear the code from the session to prevent re-execution
        request.session['generated_code'] = None
        request.session.modified = True

        def event_stream():
            output_q = queue.Queue()

            def run_code():
                try:
                    # Redirect stdout and stderr to the queue
                    sys_stdout = sys.stdout
                    sys_stderr = sys.stderr
                    sys.stdout = StreamToQueue(output_q)
                    sys.stderr = sys.stdout

                    logger.info("Starting code execution.")
                    # Prepare a local namespace for exec, including '__name__'
                    safe_globals = {
                        "__builtins__": __builtins__,
                        "pybgpstream": pybgpstream,
                        "datetime": datetime,
                        "__name__": "__main__",
                        "import": restricted_import,  # Override import
                    }
                    # safe = is_code_safe(code, safe_globals.keys())
                    # if not safe:
                    #     raise ValueError("Code contains unsafe or undefined variables.")

                    exec(code, safe_globals)
                    logger.info("Code execution completed successfully.")
                    
                except Exception as e:
                    error_output = traceback.format_exc()
                    output_q.put(f"\nError while executing the code:\n{error_output}")
                    logger.error(f"Error during code execution: {e}")
                finally:
                    # Restore the original stdout and stderr
                    sys.stdout = sys_stdout
                    sys.stderr = sys_stderr

            # Start the code execution in a separate thread
            code_thread = Thread(target=run_code)
            code_thread.start()

            try:
                while True:
                    try:
                        # Wait for new output with a timeout
                        output = output_q.get(timeout=10)
                        yield f"data: {json.dumps({'status': 'code_output', 'code_output': output})}\n\n"
                    except queue.Empty:
                        if not code_thread.is_alive():
                            break
                        yield f"data: {json.dumps({'status': 'keep_alive'})}\n\n"

                # Ensure all remaining output is sent
                while not output_q.empty():
                    output = output_q.get()
                    yield f"data: {json.dumps({'status': 'code_output', 'code_output': output})}\n\n"

                # Send 'complete' status
                yield f"data: {json.dumps({'status': 'complete'})}\n\n"

            except Exception as e:
                logger.error(f"Error in execute_code view: {str(e)}")
                error_message = str(e)
                yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"

        # Return a StreamingHttpResponse with the event_stream generator
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'

        return response
    except Exception as e:
        logger.error(f"Error in execute_code view: {str(e)}")
        error_message = str(e)
        return JsonResponse({"status": "error", "message": error_message}, status=500)


def catch_all(request):
    return HttpResponse("Catch-all route executed")

def download_file_with_query(request):
    file_name = request.GET.get('file')
    if not file_name:
        return HttpResponse("No file specified", status=400)

    # Remove leading slashes to prevent absolute paths
    file_name = file_name.lstrip('/')

    # Normalize and build the full file path
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_name))
    logger.info("Constructed file path:", full_path)

    # Check if the path starts with the MEDIA_ROOT directory
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        logger.info("Unauthorized access attempt:", full_path)
        raise Http404("Unauthorized access.")

    # Check if the file exists and is a file
    if os.path.exists(full_path) and os.path.isfile(full_path):
        logger.info("File found, returning response:", full_path)
        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=os.path.basename(full_path))
    else:
        logger.info("File not found:", full_path)
        raise Http404("File not found.")


# @csrf_exempt
# def bgp_llama(request):
#     query = request.GET.get('query', '')
#     session = request.session

#     if not query:
#         return JsonResponse({"status": "error", "message": "No query provided"}, status=400)

#     # Ensure the session is saved and has a session_key
#     if not session.session_key:
#         session.save()

#     session_id = session.session_key
#     logger.info(f"Session ID for current request: {session_id}")

#     try:
#         response_stream = check_query(query, session)
#         response = StreamingHttpResponse(response_stream, content_type="text/event-stream")
#         response['X-Accel-Buffering'] = 'no'
#         response['Cache-Control'] = 'no-cache'
#         response['Connection'] = 'keep-alive'
#         return response
#     except Exception as e:
#         logger.error(f"Error in bgp_llama view: {str(e)}")
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)

# def check_query(query, session):
#     global status_update_event
#     status_update_event.clear()

#     asn = extract_asn(query)
#     logger.info(asn)
#     target_prefixes = extract_target_prefixes(query)
#     from_time, until_time = extract_times(query)
#     real_time_span = extract_real_time_span(query)
#     collectors = extract_collectors(query)

#     # Queue to communicate the directory path from the thread
#     dir_path_queue = queue.Queue()

#     def collect_historical_wrapper():
#         dir_path = collect_historical_data(from_time=from_time, until_time=until_time, target_asn=asn, collectors=collectors, target_prefixes=target_prefixes)
#         dir_path_queue.put(dir_path)
#         status_update_event.set()

#     def collect_real_time_wrapper():
#         dir_path = collect_real_time_data(asn=asn, target_prefixes=target_prefixes, collection_period=real_time_span)
#         dir_path_queue.put(dir_path)
#         status_update_event.set()
#     if "real-time" in query.lower():
#         logger.info("\n Begin real-time collection and analysis")
#         yield 'data: {"status": "collecting", "message": "Collecting BGP messages..."}\n\n'

#         # Start data collection process
#         Thread(target=collect_real_time_wrapper).start()

#         while True:
#             if status_update_event.wait(timeout=10):
#                 try:
#                     # Retrieve directory path once data collection is done
#                     dir_path = dir_path_queue.get_nowait()
#                     if dir_path:
#                         session['data_dir'] = dir_path
#                         session.save()
#                         logger.info("Running RAG query with collected data...")
#                         for token in run_rag_query(query, directory_path=dir_path):
#                             yield token
#                         yield 'data: {"status": "complete"}\n\n'
#                         break
#                     else:
#                         # If no directory path, the collection failed
#                         yield 'data: {"status": "error", "message": "Data collection failed."}\n\n'
#                         break
#                 except queue.Empty:
#                     # Log and yield "still collecting" if directory path isn't ready
#                     yield 'data: {"status": "in progress", "message": "Still collecting BGP messages..."}\n\n'
#                     logger.info("Still collecting data, checking again...")
#                     continue
#             else:
#                 # Log and yield "in progress" if still within timeout but collection not yet completed
#                 yield 'data: {"status": "in progress", "message": "Still collecting BGP messages..."}\n\n'
#                 logger.info("Collection in progress, continuing to wait...")

#     # Handle historical data collection
#     elif re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', query):
#         logger.info("\n Begin historical data collection and analysis")
#         yield 'data: {"status": "collecting", "message": "Collecting BGP messages..."}\n\n'
#         Thread(target=collect_historical_wrapper).start()
#         while True:
#             if status_update_event.wait(timeout=10):
#                 dir_path = dir_path_queue.get()
#                 if dir_path:
#                     session['data_dir'] = dir_path
#                     session.save()
#                     for token in run_rag_query(query, directory_path=dir_path):
#                         yield token
#                     break
#                 else:
#                     yield 'data: {"status": "error", "message": "Real-time data collection failed"}\n\n'
#                     break
#             else:
#                 yield 'data: {"status": "error", "message": "Historical data collection failed"}\n\n'

#     # Handle regular query
#     else:
#         logger.info(f"\nProcessing regular query...\n")
#         data_dir = session.get('data_dir')
#         logger.info(f"Session data_dir retrieved: {data_dir}")
#         if data_dir:
#             for token in run_rag_query(query, directory_path=data_dir):
#                 yield token
#         else:
#             logger.info("\nNo data directory found in session.\n")
#             for token in run_rag_query(query, directory_path=None):
#                 yield token
#         status_update_event.set()

# def run_rag_query(query, directory_path):
#     try:
#         if directory_path:
#             logger.info(f"Running RAG query with data from: {directory_path}")
#         else:
#             logger.info("Running RAG query with default documents.")

#         # Stream query with the collected BGP data or default documents
#         for token in stream_bgp_query(query, directory_path):
#             yield f'data: {json.dumps({"status": "generating", "generated_text": token})}\n\n'
#     except Exception as e:
#         logger.error(f"RAG query failed: {str(e)}")
#         yield f'data: {json.dumps({"status": "error", "message": str(e)})}\n\n'
