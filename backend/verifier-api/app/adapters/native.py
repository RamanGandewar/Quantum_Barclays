"""Native scanner adapter boundary for OpenSSL/OQS-backed production scans."""

import os
from pathlib import Path

from app.adapters.base import BaseScanner
from app.models import ScanResult

NATIVE_ERROR = "Install liboqs + oqs-provider and set PQC_MODE=native"


class NativeScanner(BaseScanner):
    def scan(self, hostname: str, port: int) -> ScanResult:
        # NATIVE-ONLY: replace with OpenSSL/OQS or CIRCL probing in native deployments.
        raise NotImplementedError(NATIVE_ERROR)

    def get_cert_chain(self, hostname: str, port: int) -> list[dict]:
        # NATIVE-ONLY: parse real X.509 chains and OIDs from the scanned endpoint.
        raise NotImplementedError(NATIVE_ERROR)

    def get_kex_info(self, hostname: str, port: int) -> dict:
        # NATIVE-ONLY: inspect negotiated groups and key-share sizes from live handshakes.
        raise NotImplementedError(NATIVE_ERROR)

    def is_available(self) -> bool:
        provider_path = os.getenv("OQS_PROVIDER_PATH", "")
        if provider_path and Path(provider_path).exists():
            return True
        return bool(os.getenv("OQS_PROVIDER_AVAILABLE", "").lower() == "true")
