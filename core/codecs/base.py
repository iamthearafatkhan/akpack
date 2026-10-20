from abc import ABC, abstractmethod

class Codec(ABC):
    id: int
    name: str

    @abstractmethod
    def compress(self, data: bytes) -> bytes: ...

    @abstractmethod
    def decompress(self, data: bytes, expected_len: int) -> bytes: ...