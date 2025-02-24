import json
import logging
import sys
import queue
import traceback
from threading import Thread

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from app_1.utils.exec_code_util import StreamToQueue, restricted_import
import pybgpstream
import datetime

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def execute_code(request):
    """
    Executes the Python code stored in the session and streams back the output.
    """
    session_id = request.session.session_key
    logger.info(f"execute_code - Session ID: {session_id}")

    try:
        code = request.session.get('generated_code', None)
        if not code:
            return JsonResponse({"status": "error", "message": "No code available to execute."}, status=400)

        # Clear the code from session to prevent re-execution.
        request.session['generated_code'] = None
        request.session.modified = True

        def event_stream():
            output_q = queue.Queue()

            def run_code():
                try:
                    sys_stdout = sys.stdout
                    sys_stderr = sys.stderr
                    sys.stdout = StreamToQueue(output_q)
                    sys.stderr = sys.stdout

                    logger.info("Starting code execution.")
                    # Prepare a safe globals namespace.
                    safe_globals = {
                        "__builtins__": __builtins__,
                        "pybgpstream": pybgpstream,
                        "datetime": datetime,
                        "__name__": "__main__",
                        "import": restricted_import,
                    }
                    exec(code, safe_globals)
                    logger.info("Code execution completed successfully.")
                except Exception as e:
                    error_output = traceback.format_exc()
                    output_q.put(f"\nError while executing the code:\n{error_output}")
                    logger.error(f"Error during code execution: {e}")
                finally:
                    sys.stdout = sys_stdout
                    sys.stderr = sys_stderr

            code_thread = Thread(target=run_code)
            code_thread.start()

            try:
                while True:
                    try:
                        output = output_q.get(timeout=10)
                        yield f"data: {json.dumps({'status': 'code_output', 'code_output': output})}\n\n"
                    except queue.Empty:
                        if not code_thread.is_alive():
                            break
                        yield f"data: {json.dumps({'status': 'keep_alive'})}\n\n"

                while not output_q.empty():
                    output = output_q.get()
                    yield f"data: {json.dumps({'status': 'code_output', 'code_output': output})}\n\n"

                yield f"data: {json.dumps({'status': 'complete'})}\n\n"
            except Exception as e:
                logger.error(f"Error in execute_code event_stream: {str(e)}")
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response

    except Exception as e:
        logger.error(f"Error in execute_code view: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
