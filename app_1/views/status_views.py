import json
import logging
from threading import Event

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

logger = logging.getLogger(__name__)
status_update_event = Event()

@require_http_methods(["GET"])
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Returns the CSRF token.
    """
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

@require_http_methods(["GET"])
def status_updates(request):
    """
    Streams status updates to the client.
    """
    return StreamingHttpResponse(status_update_stream(), content_type='text/event-stream')

def status_update_stream():
    while True:
        status_update_event.wait()  # Wait until an event is set.
        status_message = get_current_status_message()
        yield f"data: {json.dumps({'status': status_message})}\n\n"
        status_update_event.clear()

def get_current_status_message():
    if status_update_event.is_set():
        return "Data collection complete, ready for query."
    else:
        return "Data is being collected..."