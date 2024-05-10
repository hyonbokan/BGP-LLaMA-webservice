from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.conf import settings
from .models import *
from .model_loader import ModelContainer
from .serializer import *
import os

def download_file(request, file_path):
    """
    View function to handle file downloads from MEDIA_ROOT.
    
    :param request: The HTTP request object.
    :param file_path: The relative file path inside the MEDIA_ROOT directory.
    :return: FileResponse or Http404 if the file is not found.
    """
    print("Received file path:", file_path)

    # Construct the full file path
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_path))
    print("Constructed file path:", full_path)

    # Ensure the path is within the MEDIA_ROOT to prevent unauthorized access
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        print("Unauthorized access attempt:", full_path)
        raise Http404("Unauthorized access.")

    # Check if the file exists and is a file (not a directory)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        print("File found, returning response:", full_path)
        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=os.path.basename(full_path))
    else:
        print("File not found:", full_path)
        raise Http404("File not found.")

# def test_download_view(request):
#     logger.info("Test download view executed.")
#     return FileResponse(open('/path/to/a/sample/file', 'rb'), as_attachment=True)

def bgp_llama(request):
    if 'query' in request.GET:
        model_pipeline = ModelContainer.load_model()
        instruction = request.GET['query']
        print(f"\n Model Input: {instruction}\n")
        
        # Without langchain
        model_out = model_pipeline(instruction)
        output = model_out[0]['generated_text']
        
        # With langchain
        # output = model_pipeline(prompt=instruction)
        
        print(f"\n Model Output: {output}\n")
        
        query_data = Userquery(instruction=instruction, output=output)
        query_data.save()
        
        # latest_insturctions = Userquery.objects.all().order_by('-id')[:5]
        # instruction_data = [{'instruction': q.instruction, 'output': q.output} for q in latest_insturctions]
        
        data = {'instruction': instruction, 'output': output}
        print(f"\nRequest: {request.GET}\n")
        # print(f"\nData: {data}\n")
        
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'No query provided'}, status=400)

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