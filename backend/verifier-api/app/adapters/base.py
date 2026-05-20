"""Abstract scanner contract shared by demo and native endpoint scanners."""

from abc import ABC, abstractmethod

from app.models import ScanResult


class BaseScanner(ABC):
    @abstractmethod
    def scan(self, hostname: str, port: int) -> ScanResult:
        """Connect to endpoint, detect negotiated algorithms, return ScanResult."""

    @abstractmethod
    def get_cert_chain(self, hostname: str, port: int) -> list[dict]:
        """Return list of certs in chain with algorithm OID, size, subject."""

    @abstractmethod
    def get_kex_info(self, hostname: str, port: int) -> dict:
        """Return key exchange details: algorithm name, key sizes, shared secret size."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this scanner's native dependencies are installed."""
