"""Deterministic scanner adapter used by demo mode and local development."""

from time import perf_counter
from urllib.error import URLError
from urllib.request import urlopen
import json

from app.adapters.base import BaseScanner
from app.models import Evidence, ScanResult
from app.state_machine import build_recommendations, classify_evidence

DEMO_PORT_PROFILES = {
    2222: {
        "negotiated_group": "X25519MLKEM768",
        "certificate_algorithm": "ML-DSA-65 host key",
        "certificate_chain_bytes": 0,
        "handshake_bytes": 4200,
        "latency_ms": 12.0,
        "protocol": "ssh",
    },
    8443: {
        "negotiated_group": "ML-KEM-768",
        "certificate_algorithm": "ML-DSA-65",
        "certificate_chain_bytes": 13200,
        "handshake_bytes": 18100,
        "latency_ms": 34.0,
        "protocol": "tls",
    },
    8444: {
        "negotiated_group": "X25519MLKEM768",
        "certificate_algorithm": "ML-DSA-65",
        "certificate_chain_bytes": 13200,
        "handshake_bytes": 18400,
        "latency_ms": 31.0,
        "protocol": "tls",
    },
    8445: {
        "negotiated_group": "X25519",
        "certificate_algorithm": "ECDSA-P256",
        "certificate_chain_bytes": 2600,
        "handshake_bytes": 5100,
        "latency_ms": 18.0,
        "pqc_library_detected": False,
        "protocol": "tls",
    },
    8446: {
        "negotiated_group": "ML-KEM-768",
        "certificate_algorithm": "ML-KEM-768 leaf authentication",
        "certificate_chain_bytes": 11800,
        "handshake_bytes": 15800,
        "latency_ms": 39.0,
        "protocol": "kemtls",
    },
    8447: {
        "negotiated_group": "X25519MLKEM768",
        "certificate_algorithm": "ML-DSA-65 host key",
        "certificate_chain_bytes": 0,
        "handshake_bytes": 4200,
        "latency_ms": 12.0,
        "protocol": "ssh-telemetry",
    },
}


class DemoScanner(BaseScanner):
    def scan(self, hostname: str, port: int) -> ScanResult:
        started = perf_counter()
        profile = self._profile(hostname, port)
        measured_latency = profile["latency_ms"] + ((perf_counter() - started) * 1000)
        evidence = Evidence(
            negotiated_group=profile["negotiated_group"],
            certificate_algorithm=profile["certificate_algorithm"],
            certificate_chain_bytes=profile["certificate_chain_bytes"],
            handshake_bytes=profile["handshake_bytes"],
            latency_ms=round(measured_latency, 3),
            pqc_library_detected=bool(profile.get("pqc_library_detected", True)),
            details={
                "scanner_mode": "deterministic-demo-adapter",
                "protocol": profile.get("protocol", "tls"),
                "native_scanner_hint": (
                    "Set PQC_MODE=native and provide OpenSSL/OQS/CIRCL adapters "
                    "for production evidence."
                ),
            },
        )
        state = classify_evidence(evidence)
        return ScanResult(
            endpoint=f"{hostname}:{port}",
            state=state,
            evidence=evidence,
            recommendations=build_recommendations(state),
        )

    def get_cert_chain(self, hostname: str, port: int) -> list[dict]:
        profile = self._profile(hostname, port)
        protocol = profile.get("protocol", "tls")
        if protocol.startswith("ssh"):
            return [
                {
                    "subject": f"ssh://{hostname}:{port}",
                    "algorithm_oid": "experimental-ml-dsa-65-host-key",
                    "size_bytes": profile["certificate_chain_bytes"],
                }
            ]
        return [
            {
                "subject": "CN=pqc-demo.local",
                "algorithm_oid": profile["certificate_algorithm"],
                "size_bytes": profile["certificate_chain_bytes"],
            }
        ]

    def get_kex_info(self, hostname: str, port: int) -> dict:
        profile = self._profile(hostname, port)
        return {
            "algorithm": profile["negotiated_group"],
            "client_key_share_bytes": self._client_key_share_size(
                profile["negotiated_group"]
            ),
            "server_key_share_bytes": self._server_key_share_size(
                profile["negotiated_group"]
            ),
            "shared_secret_size_bytes": 32,
        }

    def is_available(self) -> bool:
        return True

    def _profile(self, hostname: str, port: int) -> dict:
        if port in {2222, 8447}:
            telemetry = self._ssh_telemetry(hostname)
            if telemetry:
                return telemetry
        return DEMO_PORT_PROFILES.get(
            port,
            {
                "negotiated_group": "X25519",
                "certificate_algorithm": "ECDSA-P256",
                "certificate_chain_bytes": 2600,
                "handshake_bytes": 5100,
                "latency_ms": 22.0,
                "pqc_library_detected": False,
                "protocol": "unknown",
            },
        )

    def _ssh_telemetry(self, hostname: str) -> dict | None:
        try:
            with urlopen(f"http://{hostname}:8447", timeout=0.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError):
            return None
        return {
            "negotiated_group": payload.get("kex_algorithm", "X25519MLKEM768"),
            "certificate_algorithm": payload.get("host_key_algorithm", "ml-dsa-65"),
            "certificate_chain_bytes": 0,
            "handshake_bytes": int(payload.get("session_bytes", 4200)),
            "latency_ms": float(payload.get("handshake_ms", 12)),
            "protocol": "ssh",
        }

    @staticmethod
    def _client_key_share_size(algorithm: str) -> int:
        if "X25519MLKEM768" in algorithm:
            return 1216
        if "ML-KEM" in algorithm:
            return 1184
        return 32

    @staticmethod
    def _server_key_share_size(algorithm: str) -> int:
        if "X25519MLKEM768" in algorithm:
            return 1120
        if "ML-KEM" in algorithm:
            return 1088
        return 32


class DemoTelemetryAdapter(DemoScanner):
    """Compatibility name for the demo scanner described in project docs."""
