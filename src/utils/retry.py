import time
from functools import wraps
from typing import Callable, Type, Tuple


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator
