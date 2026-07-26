# AGENTS.md — Project Context for AI Assistants

## Project: Quantum-Secure Communication System

Barclays-oriented PQC (Post-Quantum Cryptography) migration demonstrator.
Detects, classifies, and scores post-quantum readiness of TLS/SSH endpoints
using the SMSM (State-based Migration Security Model) framework.

## Architecture

```
backend/verifier-api/    FastAPI REST API + SSE live scanning (Python)
backend/ca/              Certificate authority — generates ML-DSA cert chains
frontend/dashboard/      React + Recharts single-file dashboard (TypeScript)
services/server-pqc/     Go TLS profile demo server (ports 8443-8445)
services/server-kemtls/  Go KEMTLS profile demo server (port 8446)
services/server-ssh/     Go SSH + HTTP telemetry server (port 22/8447)
demos/security/          Standalone security demo report generators
tests/e2e/               Playwright E2E tests
```

## Key Commands

```bash
# Run verifier-api tests (75 tests)
cd backend/verifier-api && python -m pytest tests/ -v

# Lint Python code
python -m ruff check backend/verifier-api/app/

# Build & run Docker (native PQC mode)
docker-compose up --build verifier-api

# Build individual images
docker build -t pqc-verifier-api:native ./backend/verifier-api
docker build -t pqc-ca:native ./backend/ca

# Test SSE endpoint (from host)
curl http://localhost:8000/scan/live

# Generate ML-DSA certs (needs Docker or WSL with OQS)
docker run --rm -v $(pwd)/certs:/app/certs pqc-ca:native
```

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `PQC_MODE` | `native` | `demo` or `native` — selects scanner adapter |
| `SCAN_TARGETS` | `localhost:8443,8444,8445,8446,2222` | Comma-separated scan targets for live scanner |
| `LIVE_SCAN_INTERVAL` | `10` | Seconds between live scan cycles |
| `CRQC_MEDIAN_YEAR` | `2038` | CRQC probability sigmoid center |
| `CRQC_SPREAD_YEARS` | `5` | CRQC probability sigmoid spread |
| `OPENSSL_CONF` | `/opt/oqs/openssl.cnf` | OpenSSL config loading OQS provider |
| `LD_LIBRARY_PATH` | `/opt/oqs/lib` | Path to liboqs shared library |

## SMSM States (S0–S4)

| State | Meaning | Quantum Security |
|---|---|---|
| S0_CLASSICAL | Classical TLS (X25519 + ECDSA) | 0.0 |
| S1_PQC_READY | PQC library installed but unused | 0.0 |
| S2_HYBRID_KX | Hybrid key exchange (X25519MLKEM768) | 0.3 |
| S3_HYBRID_FULL | Hybrid full (PQC KEX + ML-DSA cert) | 0.8 |
| S4_PQC_NATIVE | Pure PQC (ML-KEM + ML-DSA) | 1.0 |

## OQS Dependencies (WSL)

liboqs + oqs-provider installed at `/home/pb/oqs-install/` in WSL Ubuntu (user `pb`).
OpenSSL config at `/home/pb/oqs-install/openssl.cnf`.
Only ML-KEM and ML-DSA algorithms built (minimal build).

## Git Conventions

- Work on `main` branch directly (no feature branches per user preference)
- Commit messages: `type: description` format
- Always update PROGRESS.md with dated entries
- Update ROADMAP.md when phases complete

## User: Prajwal

- Prefers one step at a time
- Runs terminal commands when needed
- Approves AI running commands after review

## Completed Phases

- **Phase 1** (commit 8586995): Native PQC — NativeScanner, ML-DSA certs, Docker builds
- **Phase 2** (commit 26b54f3): Real-time — SSE live scanning, EventSource frontend
- **Phase 4** (commit 60b099e): Testing — 75 Python tests, Go tests, Playwright E2E
- **Phase 3**: Deferred (demos are standalone report generators)
- **Phase 5**: Pending (production readiness)
