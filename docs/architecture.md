# Architecture

## System Diagram

```text
                 +---------------------+
                 | React Dashboard     |
                 | 3000                |
                 +----------+----------+
                            |
                            v
                 +----------+----------+
                 | Migration Verifier  |
                 | FastAPI 8000        |
                 +----+-----------+----+
                      |           |
        +-------------+           +----------------+
        v                                          v
+-------+--------+                         +-------+--------+
| HNDL Scorer    |                         | SMSM Verifier  |
| risk.py        |                         | state_machine  |
+----------------+                         +----------------+
        ^
        |
+-------+--------------------------------------------------------------+
| Scanner Adapters                                                     |
| DemoScanner / NativeScanner                                          |
+---+--------------+--------------+----------------+------------------+
    |              |              |                |
    v              v              v                v
PQC TLS        KEMTLS         SSH Service       StrongSwan VPN
8443-8445      8446           2222/8447         500/4500 UDP
```

## Components

- PQC Certificate Authority: creates classical demo certificate material and PQC CA manifests for native OpenSSL/OQS mode.
- PQC TLS Service: exposes classical, hybrid, and PQC-native telemetry profiles.
- KEMTLS Service: exposes KEMTLS comparison telemetry and the absence of `CertificateVerify`.
- SSH Service: exposes experimental classical, hybrid, and PQC-native SSH migration telemetry.
- VPN Node: stores StrongSwan/OQS configuration for RFC 9370 and RFC 9242 deployment.
- Measurement Client: runs repeated measurements and emits JSON statistics.
- Migration Verifier API: scans endpoints, classifies SMSM state, computes HNDL risk, and validates transition gates.
- Dashboard: visualizes migration state, risk, handshake cost, latency, and connection evidence.
- Security Demos: produce JSON reports for confidentiality, authenticity, integrity, and HNDL behavior.

## Data Flow

1. A service exposes telemetry or a native cryptographic endpoint.
2. A scanner adapter collects negotiated group, authentication algorithm, chain size, handshake bytes, and latency.
3. The verifier maps evidence into `S0` through `S4`.
4. The HNDL scorer combines channel state with data class and lifetime.
5. The dashboard renders overview, comparison, risk, state machine, and live connection evidence.
6. Prometheus scrapes verifier and metrics endpoints.

## Demo Mode

Demo mode uses deterministic telemetry adapters. It runs on a normal development machine and validates architecture, API contracts, dashboard behavior, risk scoring, transition logic, reports, and benchmark schemas.

## Native Mode

Native mode replaces deterministic adapters with real cryptographic probes:

- `backend/verifier-api/app/adapters/native.py`
- `backend/ca/generate_pki.py`
- `services/server-pqc`
- `services/server-kemtls`
- `services/server-ssh`
- `infra/vpn/swanctl.conf`

Native mode requires OpenSSL 3.3+, liboqs, oqs-provider, CIRCL, OQS-Go forks for KEMTLS, and StrongSwan on Linux.
