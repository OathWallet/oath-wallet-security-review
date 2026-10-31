"""Bound a harness and its own children without touching unrelated builds."""
import os
import signal
import subprocess

def logged_command(command, *, stream, timeout, cwd=None, env=None):
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                               stderr=subprocess.STDOUT, start_new_session=True)
    try:
        return process.wait(timeout=timeout), False
    except subprocess.TimeoutExpired:
        # Killing just Python leaves its Swift compiler children behind. This
        # private session contains only processes started by this invocation.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        stream.write(f'\nAUDIT TEST TIMEOUT after {timeout} seconds\n')
        stream.flush()
        return 124, True
