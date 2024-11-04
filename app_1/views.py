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
from .model_loader import load_model, GPT_HIST_SYSTEM_PROMPT, GPT_REAL_TIME_SYSTEM_PROMPT, LLAMA_SYSTEM_PROMPT
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
    else:
        system_prompt = GPT_HIST_SYSTEM_PROMPT

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
        # No code block found
        return None
import ast

def is_code_safe(code, safe_globals_keys):
    try:
        tree = ast.parse(code)
        defined_vars = set()
        undefined_vars = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_vars.add(target.id)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    if node.id not in defined_vars and node.id not in safe_globals_keys:
                        undefined_vars.add(node.id)

        if undefined_vars:
            logger.warning(f"Undefined variables detected: {undefined_vars}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error parsing code for undefined variables: {e}")
        return False


def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed_modules = {'pandas', 'pybgpstream', 'datetime'}
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
        data = json.loads(request.body)
        query = data.get('query', '')
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

    if not query:
        return JsonResponse({"status": "error", "message": "No query provided"}, status=400)

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

            logger.info(f"Assistant's full reply:\n{assistant_reply_content}")

            # Extract code from the assistant's reply
            code = extract_code_from_reply(assistant_reply_content)
            logger.info(f"Generated code to execute:\n{code}")

            # Send 'running_code' status
            yield f"data: {json.dumps({'status': 'running_code'})}\n\n"

            # Initialize a queue to receive code execution output
            output_queue = queue.Queue()

            def run_code():
                output_capture = io.StringIO()
                try:
                    with redirect_stdout(output_capture):
                        # Prepare a local namespace for exec
                        safe_globals = {
                            "__builtins__": __builtins__,
                            "pybgpstream": pybgpstream,
                            "datetime": datetime,
                            "__name__": "__main__",
                        }
                        exec(code, safe_globals)
                        logger.info("Code execution completed successfully.")
                except Exception as e:
                    # Capture the traceback if an error occurs
                    error_output = traceback.format_exc()
                    output_capture.write("\nError while executing the code:\n")
                    output_capture.write(error_output)
                    logger.error(f"Error during code execution: {e}")
                # Put the captured output into the queue
                output = output_capture.getvalue()
                logger.info(f"Captured code output: {output}")
                output_queue.put(output)

            # Start the code execution in a separate thread
            code_thread = Thread(target=run_code)
            code_thread.start()

            # Periodically send keep-alive messages while code is executing
            while code_thread.is_alive():
                time.sleep(30)  # Send keep-alive every 30 seconds
                yield f"data: {json.dumps({'status': 'keep_alive'})}\n\n"

            # Retrieve the output
            if not output_queue.empty():
                code_output = output_queue.get()
                logger.info(f"Code output:\n{code_output}")
                # Send 'code_output' status with the output
                yield f"data: {json.dumps({'status': 'code_output', 'code_output': code_output})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'code_output', 'code_output': 'No output captured.'})}\n\n"

            # Send 'complete' status
            yield f"data: {json.dumps({'status': 'complete'})}\n\n"

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
    logger.info(f"Session ID for current request: {session_id}")

    try:
        # Directly generate the response stream from the LLM
        input = LLAMA_SYSTEM_PROMPT + query
        response_stream = generate_llm_response(input)
        response = StreamingHttpResponse(response_stream, content_type="text/event-stream")
        response['X-Accel-Buffering'] = 'no'
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        return response
    except Exception as e:
        logger.error(f"Error in bgp_llama view: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def generate_llm_response(query):
    logger.info(f"User query: {query}")
    try:
        # Load the model and tokenizer
        model, tokenizer, streamer = load_model()

        # Tokenize the input query with attention mask
        inputs = tokenizer(
            query,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=1024
        )

        input_ids = inputs.input_ids.to(model.device)
        attention_mask = inputs.attention_mask.to(model.device)
        
        # Start the generation in a separate thread
        generation_kwargs = dict(
            input_ids=input_ids,
            attention_mask=attention_mask,
            streamer=streamer,
            max_new_tokens=600,
            do_sample=True,
            temperature=0.1,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
        def generate():
            model.generate(**generation_kwargs)

        generation_thread = Thread(target=generate)
        generation_thread.start()

        # Stream the tokens as they are generated
        for new_text in streamer:
            # Yield the token to the client in the SSE format
            data = json.dumps({"status": "generating", "generated_text": new_text})
            yield f'data: {data}\n\n'

        # Wait for the generation thread to finish
        generation_thread.join()

        # Indicate completion
        yield 'data: {"status": "complete"}\n\n'

    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        data = json.dumps({"status": "error", "message": str(e)})
        yield f'data: {data}\n\n'

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


def catch_all(request):
    return HttpResponse("Catch-all route executed")