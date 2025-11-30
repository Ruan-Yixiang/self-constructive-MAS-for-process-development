from typing import Callable

def bind_function(worker, func_name: str):

    def decorator(func: Callable):
        setattr(worker, func_name, func)
        return func
    return decorator
