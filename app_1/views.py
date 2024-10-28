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
from .bgp_utils import (
    extract_asn,
    extract_collectors,
    extract_target_prefixes,
    extract_times,
    collect_historical_data,
    collect_real_time_data,
    extract_real_time_span
)
from .model_loader import stream_bgp_query
import re

status_update_event = Event()
scenario = ""

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
    """
    Returns the current status message to be sent to the frontend.
    This could be collecting, querying, etc.
    """
    if status_update_event.is_set():
        return "Data collection complete, ready for query."
    else:
        return "Data is being collected..."
    
@csrf_exempt
def bgp_llama(request):
    query = request.GET.get('query', '')
    session = request.session

    if not query:
        return StreamingHttpResponse(
            json.dumps({"status": "error", "message": "No query provided"}), 
            content_type="application/json"
        )

    # Ensure the session is saved and has a session_key
    if not session.session_key:
        session.save()

    session_id = session.session_key
    print(f"Session ID for current request: {session_id}")

    try:
        response_stream = check_query(query, session)
        response = StreamingHttpResponse(response_stream, content_type="text/event-stream")
        response['X-Accel-Buffering'] = 'no'  # Disable Nginx buffering
        return response
    except Exception as e:
        logger.error(f"Error in bgp_llama view: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def check_query(query, session):
    global status_update_event
    status_update_event.clear()

    asn = extract_asn(query)
    print(asn)
    target_prefixes = extract_target_prefixes(query)
    from_time, until_time = extract_times(query)
    real_time_span = extract_real_time_span(query)
    collectors = extract_collectors(query)

    # Queue to communicate the directory path from the thread
    dir_path_queue = queue.Queue()

    def collect_historical_wrapper():
        dir_path = collect_historical_data(from_time=from_time, until_time=until_time, target_asn=asn, collectors=collectors, target_prefixes=target_prefixes)
        dir_path_queue.put(dir_path)
        status_update_event.set()

    def collect_real_time_wrapper():
        dir_path = collect_real_time_data(asn=asn, target_prefixes=target_prefixes, collection_period=real_time_span)
        dir_path_queue.put(dir_path)
        status_update_event.set()

    # Handle real-time data collection
    if "real-time" in query.lower():
        print("\n Begin real-time collection and analysis")
        yield 'data: {"status": "collecting", "message": "Collecting BGP messages..."}\n\n'
        Thread(target=collect_real_time_wrapper).start()

        status_update_event.wait()
        dir_path = dir_path_queue.get()
        if dir_path:
            # Update session in main thread
            session['data_dir'] = dir_path
            session.save()
            print(f"\nSession updated data_dir in main thread: {session['data_dir']}\n")
            for token in run_rag_query(query, directory_path=dir_path):
                yield token
        else:
            yield 'data: {"status": "error", "message": "Real-time data collection failed"}\n\n'

    # Handle historical data collection
    elif re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', query):
        print("\n Begin historical data collection and analysis")
        yield 'data: {"status": "collecting", "message": "Collecting BGP messages..."}\n\n'
        Thread(target=collect_historical_wrapper).start()
        status_update_event.wait()
        dir_path = dir_path_queue.get()
        if dir_path:
            # Update session in main thread
            session['data_dir'] = dir_path
            session.save()
            print(f"\nSession updated data_dir in main thread: {session['data_dir']}\n")
            for token in run_rag_query(query, directory_path=dir_path):
                yield token
        else:
            yield 'data: {"status": "error", "message": "Historical data collection failed"}\n\n'

    # Handle regular query
    else:
        print(f"\nProcessing regular query...\n")
        data_dir = session.get('data_dir')
        print(f"Session data_dir retrieved: {data_dir}")
        if data_dir:
            for token in run_rag_query(query, directory_path=data_dir):
                yield token
        else:
            print("\nNo data directory found in session.\n")
            for token in run_rag_query(query, directory_path=None):
                yield token
        status_update_event.set()

def run_rag_query(query, directory_path):
    try:
        if directory_path:
            logger.info(f"Running RAG query with data from: {directory_path}")
        else:
            logger.info("Running RAG query with default documents.")

        # Stream query with the collected BGP data or default documents
        for token in stream_bgp_query(query, directory_path):
            yield f'data: {json.dumps({"status": "generating", "generated_text": token})}\n\n'
    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        yield f'data: {json.dumps({"status": "error", "message": str(e)})}\n\n'


def download_file_with_query(request):
    file_name = request.GET.get('file')
    if not file_name:
        return HttpResponse("No file specified", status=400)

    # Remove leading slashes to prevent absolute paths
    file_name = file_name.lstrip('/')

    # Normalize and build the full file path
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_name))
    print("Constructed file path:", full_path)

    # Check if the path starts with the MEDIA_ROOT directory
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        print("Unauthorized access attempt:", full_path)
        raise Http404("Unauthorized access.")

    # Check if the file exists and is a file
    if os.path.exists(full_path) and os.path.isfile(full_path):
        print("File found, returning response:", full_path)
        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=os.path.basename(full_path))
    else:
        print("File not found:", full_path)
        raise Http404("File not found.")


def catch_all(request):
    return HttpResponse("Catch-all route executed")