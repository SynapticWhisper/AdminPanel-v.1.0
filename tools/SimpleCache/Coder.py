import pickle
from typing import Any
from tools.SimpleCache.types import Coder


class PickleCoder(Coder):
    """A coder for pickling and unpickling data."""

    @classmethod
    def encode(cls, value: Any) -> bytes:
        """Encode data using pickle."""
        return pickle.dumps(value)
    
    @classmethod
    def decode(cls, value: bytes) -> Any:
        """Decode data using pickle."""
        return pickle.loads(value)
