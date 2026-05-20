"""Public scanner facade used by FastAPI routes."""

from app.adapters.factory import build_scanner
from app.models import ScanRequest

SCANNER = build_scanner()


def scan_endpoint(request: ScanRequest) -> dict:
    result = SCANNER.scan(request.hostname, request.port)
    return result.model_dump()
