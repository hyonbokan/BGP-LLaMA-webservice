from django.http import JsonResponse, FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from .models import *
from .serializer import *
import json
from threading import Thread, Event
import os
from django.conf import settings
from .bgp_utils import extract_asn, extract_times, collect_historical_data, collect_real_time_data, process_dataframe
from .model_loader import model, tokenizer, streamer
import re

status_update_event = Event()
collected_data = []
scenario = ""
input_text = ""

SYSTEM_PROMPT = """
You are an AI assistant and your task is to answer the user query on the given BGP data. Here are some rules you always follow:
- Generate only the requested output, don't include any other language before or after the requested output.
- Your answers should be direct and include relevant timestamps when analyzing BGP data features.
- Check the collected BGP data given below. Each row represents the features collected over a specific period.
- Never say thank you, that you are happy to help, that you are an AI agent, and additional suggestions. Just answer directly.
"""



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

def generate_llm_response(prompt, streamer):
    inputs = tokenizer([prompt], return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    generation_kwargs = dict(
        inputs=inputs["input_ids"],
        streamer=streamer,
        max_new_tokens=756,
        do_sample=True,
    )
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text.strip()

    thread.join()
    
def generate_input_text(query, scenario="regular query", data=None):
    if scenario == "real-time":
        return f"{SYSTEM_PROMPT}Answer this user query: {query}\n{''.join(data)}"
    elif scenario == "historical":
        return f"{SYSTEM_PROMPT}Answer this user query: {query}\n{''.join(data)}"
    elif scenario == "error":
        return f"{SYSTEM_PROMPT}First state that due to an error, BGP data cannot be collected. Then address the query."
    else:
        return f"You are an AI assistant and your task is to answer the user query on the given BGP data. Here are some rules you always follow:\n- Generate only the requested output, don't include any other language before or after the requested output.\n- Never say thank you, that you are happy to help, that you are an AI agent, and additional suggestions. Just answer directly.\nAnswer this user query: {query}"

    
def check_query(query):
    global collected_data, status_update_event, input_text, scenario
    status_update_event.clear()
    
    asn = extract_asn(query)
    from_time, until_time = extract_times(query)
    
    def collect_historical_wrapper():
        global collected_data, input_text, scenario
        df = collect_historical_data(asn, from_time, until_time)
        collected_data = process_dataframe(df)
        scenario = 'historical' if collected_data else 'error'
        input_text = generate_input_text(query=query, scenario=scenario, data=collected_data)
        status_update_event.set()

    def collect_real_time_wrapper():
        global collected_data, input_text, scenario
        df = collect_real_time_data(asn)
        collected_data = process_dataframe(df)
        scenario = 'real-time' if collected_data else 'error'
        input_text = generate_input_text(query=query, scenario=scenario, data=collected_data)
        status_update_event.set()
        
    if "real-time" in query.lower():
        print("\n Begin real-time collection and analysis")
        scenario = "real-time"
        Thread(target=collect_real_time_wrapper).start()
        
    elif re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', query):
        print("\n Begin historical data collection and analysis")
        scenario = "historical"
        Thread(target=collect_historical_wrapper).start()
    else:
        print("regular query")
        scenario = "regular query"
        input_text = generate_input_text(query=query)
        status_update_event.set()
        

    
def stream_response_generator(query):
    global model, tokenizer, streamer, input_text, status_update_event, scenario
    if not query:
        yield 'data: {"status": "error", "message": "No query provided"}\n\n'
        return  # Exit early

    print(f'user query: {query}\n')
    check_query(query)
    
    # Notify frontend that data collection has started only for real-time or historical scenarios
    if scenario in ["real-time", "historical"]:
        yield 'data: {"status": "collecting", "message": "Collecting BGP messages..."}\n\n'
        
    # Wait for data collection to complete before generating output
    status_update_event.wait()
    
    try:
        # Check if the scenario involves data collection (real-time or historical)
        if scenario in ["real-time", "historical"]:
            print(f"\n Scenario: {scenario}\n")
            # print(f"\n Input text before split: {input_text}\n")
            for i, chunk in enumerate(collected_data):
                chunk_input_text = input_text.replace("{''.join(data)}", chunk)
                print(f"Final prompt with data (Chunk {i + 1}/{len(collected_data)}): {chunk_input_text}\n")
                generated_output = ""
                for new_text in generate_llm_response(prompt=chunk_input_text, streamer=streamer):
                    generated_output += new_text
                    yield f'data: {json.dumps({"status": "generating", "generated_text": new_text})}\n\n'
                print(generated_output)
                yield f'data: {json.dumps({"status": "complete", "generated_text": generated_output})}\n\n'
                
        else:
            # Handle the case where no data was collected
            print(f"\n Scenario: {scenario}\n")
            print(f"\n\nNo collected data available: \n{input_text}\n\n")
            for new_text in generate_llm_response(prompt=input_text, streamer=streamer):
                yield f'data: {json.dumps({"status": "generating", "generated_text": new_text})}\n\n'
            yield f'data: {json.dumps({"status": "complete", "generated_text": generated_output})}\n\n'
            
    except Exception as e:
        error_message = f"An error occurred during text generation: {str(e)}"
        print(error_message)
        yield f'data: {json.dumps({"error": error_message})}\n\n'
    
    finally:
        status_update_event.clear()

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