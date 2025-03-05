
import json
import logging
import asyncio
import traceback
import queue
from threading import Thread

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from app_1.utils.exec_code_util import restricted_import

import pybgpstream
import datetime

logger = logging.getLogger(__name__)

class CodeExecutionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.session = self.scope["session"]
        logger.info("CodeExecutionConsumer connected, session id: %s", self.session.session_key)

    async def disconnect(self, close_code):
        logger.info("CodeExecutionConsumer disconnected, session id: %s", self.session.session_key)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get("command", "")
            if command != "execute":
                await self.send(json.dumps({"status": "error", "message": "Invalid command"}))
                return

            code = self.session.get("generated_code", None)
            if not code:
                await self.send(json.dumps({"status": "error", "message": "No code available to execute."}))
                return

            # Clear code from session to prevent re-execution.
            self.session["generated_code"] = None
            await sync_to_async(self.session.save)()

            # Use a thread and a queue to stream code execution output.
            output_queue = queue.Queue()
            thread = Thread(target=self.run_code_stream, args=(code, output_queue))
            thread.start()

            loop = asyncio.get_event_loop()
            while thread.is_alive() or not output_queue.empty():
                out = await loop.run_in_executor(None, output_queue.get)
                if out is not None:
                    await self.send(json.dumps({"status": "code_output", "code_output": out}))
            thread.join()
            await self.send(json.dumps({"status": "complete"}))
        except Exception as e:
            logger.error("Error in CodeExecutionConsumer: %s", str(e))
            await self.send(json.dumps({"status": "error", "message": str(e)}))

    def run_code_stream(self, code, output_queue):
        import io, sys
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = sys.stdout
        try:
            safe_globals = {
                "__builtins__": __builtins__,
                "pybgpstream": pybgpstream,
                "datetime": datetime,
                "__name__": "__main__",
                "import": restricted_import,
            }
            exec(code, safe_globals)
            output = sys.stdout.getvalue()
            for line in output.splitlines():
                output_queue.put(line)
        except Exception as e:
            output = sys.stdout.getvalue() + "\nError: " + str(e) + "\n" + traceback.format_exc()
            output_queue.put(output)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
