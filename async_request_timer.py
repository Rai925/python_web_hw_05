import asyncio
import time


def request_logger(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"Request {func.__name__} executed in {end_time - start_time} seconds")
        return result

    return wrapper
