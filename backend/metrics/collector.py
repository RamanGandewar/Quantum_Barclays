import random
import time

from prometheus_client import Gauge, start_http_server

HANDSHAKE_BYTES = Gauge(
    "pqc_demo_handshake_bytes", "Demo handshake byte count", ["profile"]
)
LATENCY_MS = Gauge("pqc_demo_latency_ms", "Demo handshake latency", ["profile"])
RISK_SCORE = Gauge("pqc_demo_hndl_risk_score", "Demo HNDL risk score", ["data_class"])


def update_metrics() -> None:
    HANDSHAKE_BYTES.labels("classical").set(5100)
    HANDSHAKE_BYTES.labels("hybrid").set(18400)
    HANDSHAKE_BYTES.labels("pqc_native").set(18100)
    HANDSHAKE_BYTES.labels("kemtls").set(15800)

    LATENCY_MS.labels("classical").set(18 + random.random() * 3)
    LATENCY_MS.labels("hybrid").set(31 + random.random() * 5)
    LATENCY_MS.labels("pqc_native").set(34 + random.random() * 5)
    LATENCY_MS.labels("kemtls").set(39 + random.random() * 5)

    RISK_SCORE.labels("internal").set(0.42)
    RISK_SCORE.labels("confidential").set(2.1)
    RISK_SCORE.labels("secret").set(10.5)


if __name__ == "__main__":
    start_http_server(9090)
    while True:
        update_metrics()
        time.sleep(5)
