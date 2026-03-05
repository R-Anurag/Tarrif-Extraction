import time
from collections import deque
from threading import Lock


class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = Lock()
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                while self.calls and self.calls[0] <= now - self.period:
                    self.calls.popleft()
                
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.period - (now - self.calls[0])
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    self.calls.popleft()
                
                self.calls.append(time.time())
            
            return func(*args, **kwargs)
        return wrapper
    
    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.calls.popleft()
            
            self.calls.append(time.time())
