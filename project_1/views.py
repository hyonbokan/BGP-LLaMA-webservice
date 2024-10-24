from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

def index_react(request):
    try:
        with open(os.path.join(settings.BASE_DIR, 'react_frontend', 'build', 'index.html')) as file:
            return HttpResponse(file.read())
    except FileNotFoundError:
        return HttpResponse("Error: The build for React app not found.", status=501)