from django.http import JsonResponse, FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from .models import *
from .serializer import *
import json
from threading import Thread, Lock, Event
import os
from django.conf import settings
from .bgp_utils import extract_asn, extract_times, collect_historical_data, collect_real_time_data, split_dataframe, preprocess_data
from .model_loader import model, tokenizer, streamer

status_update_event = Event()
data_collected_event = Event()
collected_data = None

SYSTEM_PROMPT = """
Your task is to answers the user query in a friendly manner, based on the given BGP data. Here are some rules you always follow:
1. The data is already provided in the table format.
2. First, carefully read and analyze the values of the features of BGP data. For example, you should identify and extract specific details like number of announcements, timestamps, and other relevant features.
3. Never say thank you, that you are happy to help, that you are an AI agent, etc. Just answer directly.
"""

input_text = ""
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
        yield f'data: {json.dumps({"status": collected_data})}\n\n'
        status_update_event.clear()  # Clear the event after sending the update

@require_http_methods(["GET"])
def status_updates(request):
    return StreamingHttpResponse(status_update_stream(), content_type='text/event-stream')
        
def process_dataframe(df):
    chunks = split_dataframe(df, split_size=20)
    processed_data = []
    for chunk in chunks:
        processed_data.append(preprocess_data(chunk))
    return processed_data

def generate_input_text(query, scenario, data=None):
    """
    Generate the appropriate input text based on the scenario and available data.
    
    -query: The original query from the user.
    -scenario: The type of scenario ("real-time", "historical", "general", "error").
    -data: The collected data to include in the input (optional).
    """
    if scenario == "real-time":
        return f"{SYSTEM_PROMPT}\nHere is the collected BGP data, with each row representing the features collected over a 1-minute period:\n{''.join(data)}\nHere is the query: {query}"
    elif scenario == "historical":
        return f"{SYSTEM_PROMPT}\nHere is the collected BGP data, with each row representing the features collected over a 5-minute period:\n{''.join(data)}\nHere is the query: {query}"
    elif scenario == "error":
        return f"{SYSTEM_PROMPT}\nFirst state that due to an error, BGP data cannot be collected. Then address the query."
    else:
        return f"{SYSTEM_PROMPT}Here is the query: {query}"
    
    
def check_query(query):
    global collected_data, data_collected_event, input_text
    data_collected_event.clear()  # Reset the event
    asn = extract_asn(query)
    from_time, until_time = extract_times(query)
    
    def collect_historical_wrapper():
        global collected_data, input_text
        df = collect_historical_data(asn, from_time, until_time)
        collected_data = process_dataframe(df)
        if collected_data:
            scenario = 'historical'
            input_text = generate_input_text(query=query, scenario=scenario, data=collected_data)
        else:
            scenario = 'error'
            input_text = generate_input_text(query=query, scenario=scenario)
        data_collected_event.set()  # Signal that data collection is complete
        status_update_event.set()  # Send status update

    def collect_real_time_wrapper():
        global collected_data, input_text
        # collected_data = ["No data collected only say that "]
        df = collect_real_time_data(asn)
        collected_data = process_dataframe(df)
        if collected_data:
            scenario = 'real-time'
            input_text = generate_input_text(query=query, scenario=scenario, data=collected_data)
        else:
            scenario = 'error'
            input_text = generate_input_text(query=query, scenario=scenario)
        data_collected_event.set()  # Signal that data collection is complete
        status_update_event.set()
        
    if "real-time" in query.lower():
        print("\n Begin real-time collection and analysis")
        status_update_event.set() # Send status update
        Thread(target=collect_real_time_wrapper).start()
        
    elif "real-time" not in query.lower():
        print("\n Begin historical data collection and analysis")
        status_update_event.set() 
        Thread(target=collect_historical_wrapper).start()
    else:
        print("regular query")
        collected_data = None
        input_text = generate_input_text(query=query)
        data_collected_event.set()  # Signal immediately for regular queries
        status_update_event.set() 


def stream_response_generator(query):
    global model, tokenizer, streamer, input_text, data_collected_event
    if not query:
        yield 'data: {"error": "No query provided"}\n\n'
    else:
        print(f'user query: {query}\n')
        check_query(query)
        
        # Wait for data collection to complete before generating output
        data_collected_event.wait()  # This will block until the event is set
        
        if collected_data:
            for i, chunk in enumerate(collected_data):
                chunk_input_text = input_text.replace("{''.join(data)}", chunk)
                print(f"Final prompt with data (Chunk {i + 1}/{len(collected_data)}): {chunk_input_text}")
                
                inputs = tokenizer([chunk_input_text], return_tensors="pt")
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
                # Run the generation in a separate thread
                generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=512)
                thread = Thread(target=model.generate, kwargs=generation_kwargs)
                thread.start()
    
                try:
                    for new_text in streamer:
                        yield f'data: {json.dumps({"generated_text": new_text.strip()})}\n\n'
                except Exception as e:
                    yield f'data: {json.dumps({"error": str(e)})}\n\n'

        else:
            # Handle the case where no data was collected
            print(f"\nCollected data: {collected_data}")
            inputs = tokenizer([input_text], return_tensors="pt")
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
            # Run the generation in a separate thread
            generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=512)
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
    
            try:
                for new_text in streamer:
                    yield f'data: {json.dumps({"generated_text": new_text.strip()})}\n\n'
            except Exception as e:
                yield f'data: {json.dumps({"error": str(e)})}\n\n'

@require_http_methods(["GET"])
def bgp_llama(request):
    query = request.GET.get('query', '')
    return StreamingHttpResponse(stream_response_generator(query), content_type="text/event-stream")


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