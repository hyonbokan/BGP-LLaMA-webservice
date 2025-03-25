import json
import logging
import asyncio
import os

from django.http import JsonResponse, StreamingHttpResponse, FileResponse, Http404, HttpResponse
from django.middleware.csrf import get_token
from django.conf import settings
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Use an asyncio Event for asynchronous waiting
status_update_event = asyncio.Event()

@sync_to_async
def initialize_session(request):
    request.session['initialized'] = True
    request.session.save()

async def get_csrf_token(request):
    if request.method != "GET":
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    token = get_token(request)

    try:
        await initialize_session(request)
    except Exception as e:
        logger.warning("Session data corrupted")
        logger.exception(e)

    response = JsonResponse({'csrfToken': token})
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        token,
        max_age=settings.CSRF_COOKIE_AGE,
        domain=settings.CSRF_COOKIE_DOMAIN,
        secure=settings.CSRF_COOKIE_SECURE,
        httponly=settings.CSRF_COOKIE_HTTPONLY,
        samesite=settings.CSRF_COOKIE_SAMESITE,
    )
    return response

async def status_update_stream():
    """
    Asynchronous generator that yields status messages as SSE.
    """
    while True:
        # Wait asynchronously for the event to be set
        await status_update_event.wait()
        status_message = get_current_status_message()
        yield f"data: {json.dumps({'status': status_message})}\n\n"
        status_update_event.clear()

async def status_updates(request):
    """
    Asynchronously streams status updates.
    """
    if request.method != "GET":
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return StreamingHttpResponse(status_update_stream(), content_type='text/event-stream')

def get_current_status_message():
    """
    Returns a status message.
    """
    if status_update_event.is_set():
        return "Data collection complete, ready for query."
    else:
        return "Data is being collected..."

async def catch_all(request):
    """
    A simple catch-all async view.
    """
    return HttpResponse("Catch-all route executed")

async def download_file(request):
    """
    Async view that returns a file response.
    """
    if request.method != "GET":
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    file_name = request.GET.get('file')
    if not file_name:
        return HttpResponse("No file specified", status=400)

    # Remove leading slashes to prevent absolute paths
    file_name = file_name.lstrip('/')
    # Normalize and build the full file path
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_name))
    logger.info("Constructed file path: %s", full_path)

    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        logger.info("Unauthorized access attempt: %s", full_path)
        raise Http404("Unauthorized access.")

    if os.path.exists(full_path) and os.path.isfile(full_path):
        logger.info("File found, returning response: %s", full_path)
        # FileResponse is a synchronous response; Django will run it in a thread pool if needed.
        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=os.path.basename(full_path))
    else:
        logger.info("File not found: %s", full_path)
        raise Http404("File not found.")
