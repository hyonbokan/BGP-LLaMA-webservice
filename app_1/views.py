from django.http import JsonResponse, FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import *
from .model_loader import ModelContainer
from .serializer import *
import json
from threading import Thread
import os
import torch

def stream_response_generator(query):
    model, tokenizer, streamer = ModelContainer.load_model()
    if not query:
        yield 'data: {"error": "No query provided"}\n\n'
    else:
        print(f'user query: {query}\n')
        inputs = tokenizer([query], return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}  # Move inputs to the model's device


        # Run the generation in a separate thread
        generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=20)
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

    # Check if the path starts with the MEDIA_ROOT directory to prevent directory traversal
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