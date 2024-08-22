from functools import wraps
import signal

def interrupt_handler(signum, frame):
    raise IOError(f"Timed out (signum {signum}, frame {frame})")

def interruptable(timeout: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, interrupt_handler)
            signal.alarm(timeout)
            return_val = func(*args, **kwargs)
            signal.alarm(0)
            return return_val
        return wrapper
    return decorator