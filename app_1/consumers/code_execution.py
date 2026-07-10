
import json
import logging
import asyncio
import os
import sys
import queue
import tempfile
import threading
import subprocess

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Hard wall-clock limit for a single code run.
CODE_EXEC_TIMEOUT = int(os.getenv("CODE_EXEC_TIMEOUT", "300"))

# Env var name prefixes/substrings that must never leak into executed code.
_SENSITIVE_ENV_MARKERS = ("SECRET", "TOKEN", "KEY", "PASSWORD", "OPENAI", "HF_", "DB_", "POSTGRES", "AWS")


def _child_env():
    """A copy of the environment with secrets removed, for the child process."""
    return {
        k: v
        for k, v in os.environ.items()
        if not any(marker in k.upper() for marker in _SENSITIVE_ENV_MARKERS)
    }


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

            # Stream code execution output from an isolated subprocess.
            output_queue = queue.Queue()
            thread = threading.Thread(target=self.run_code_stream, args=(code, output_queue))
            thread.start()

            loop = asyncio.get_running_loop()
            while thread.is_alive() or not output_queue.empty():
                out = await loop.run_in_executor(None, output_queue.get)
                if out is None:
                    break
                await self.send(json.dumps({"status": "code_output", "code_output": out}))
            thread.join()
            await self.send(json.dumps({"status": "complete"}))
        except Exception as e:
            logger.error("Error in CodeExecutionConsumer: %s", str(e))
            await self.send(json.dumps({"status": "error", "message": str(e)}))

    def run_code_stream(self, code, output_queue):
        """Run model-generated code in a separate Python process.

        This is NOT a full security sandbox (the child can still reach the
        network and read world-readable files), but it is a real boundary
        compared to the previous in-process ``exec()``: the child cannot touch
        the Django/ASGI process, secrets are scrubbed from its environment, it
        runs in a throwaway working directory, and it is force-killed after
        ``CODE_EXEC_TIMEOUT`` seconds. For untrusted input, run this inside a
        locked-down container (no network beyond BGP collectors, seccomp, etc.).
        """
        proc = None
        try:
            with tempfile.TemporaryDirectory() as workdir:
                script_path = os.path.join(workdir, "generated.py")
                with open(script_path, "w") as f:
                    f.write(code)

                proc = subprocess.Popen(
                    [sys.executable, "-I", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=workdir,
                    env=_child_env(),
                )

                # Watchdog: kill the process if it exceeds the time budget.
                timer = threading.Timer(CODE_EXEC_TIMEOUT, proc.kill)
                timer.start()
                try:
                    for line in proc.stdout:
                        line = line.rstrip("\n")
                        if line.strip():
                            output_queue.put(line)
                    proc.wait()
                finally:
                    timer.cancel()

                if proc.returncode not in (0, None):
                    output_queue.put(
                        f"Error: process exited with code {proc.returncode} "
                        f"(may have exceeded the {CODE_EXEC_TIMEOUT}s limit)."
                    )
        except Exception as e:
            output_queue.put(f"Error: {e}")
            if proc is not None:
                proc.kill()
        finally:
            # Sentinel so the reader loop can stop promptly.
            output_queue.put(None)
