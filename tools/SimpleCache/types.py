from typing import Callable, Tuple, Dict, Any, Awaitable, Union
from typing_extensions import Protocol

_Func = Callable[..., Any]

class KeyGen(Protocol):
    def __call__(
        self,
        __function: _Func,
        *,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[str], str]:
        ...

class Coder:
    @classmethod
    def encode(cls, value: Any) -> bytes:
        raise NotImplementedError
    
    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise NotImplementedError