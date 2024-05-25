import hashlib
import pickle

from typing import Callable, Tuple, Dict, Any


def pickle_keygen(
    func: Callable,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any]
) -> str:
    """Generate a cache key using pickling."""
    
    args_tuple = tuple(sorted(args))
    kwargs_tuple = tuple(sorted(kwargs.items()))
    combined = {
        "module": func.__module__,
        "name": func.__name__, 
        "args": args_tuple,
        "kwargs": kwargs_tuple
    }
    
    return hashlib.md5(pickle.dumps(combined)).hexdigest()

def str_keygen(
    func: Callable,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any]
) -> str:
    """Generate a cache key using string formatting."""
    combined = f"{func.__module__}:{func.__name__}:{args}:{kwargs}".encode()
    return hashlib.md5(combined).hexdigest()

def from_string(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest()