"""Factory for selecting the active scanner adapter from environment settings."""

import logging
import os

from app.adapters.base import BaseScanner
from app.adapters.demo import DemoScanner
from app.adapters.native import NativeScanner

LOGGER = logging.getLogger(__name__)


def build_scanner() -> BaseScanner:
    mode = os.getenv("PQC_MODE", "demo").lower()
    if mode == "native":
        native = NativeScanner()
        if native.is_available():
            LOGGER.warning("Selected NativeScanner adapter")
            return native
        LOGGER.warning(
            "PQC_MODE=native requested, but native dependencies are unavailable; using DemoScanner"
        )
    else:
        LOGGER.warning("Selected DemoScanner adapter")
    return DemoScanner()
