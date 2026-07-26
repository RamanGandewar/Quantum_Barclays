# Quantum-Secure Communication System

Post-quantum cryptography (PQC) migration demonstrator for Barclays. Detects, classifies, and scores TLS/SSH endpoints against the NIST SMSM (Structured Migration State Machine) framework — from classical all the way to pure PQC.

The system performs **real post-quantum cryptographic handshakes** against live TLS endpoints using OpenSSL + liboqs, classifies them into migration states (S0–S4), scores Harvest-Now-Decrypt-Later (HNDL) risk, and streams results to a live dashboard.

## What This Project Does

Given any TLS/SSH endpoint, the system answers:

1. **What state is this endpoint in?** — Classical, PQC-ready, hybrid key exchange, hybrid full, or pure PQC
2. **What evidence proves that state?** — Negotiated key exchange group, certificate signature algorithm, chain size, handshake bytes
3. **How urgent is migration?** — HNDL risk score based on data class, lifetime, and quantum computer arrival probability
4. **What's the migration path?** — Step-by-step plan from current state to target with preconditions and rollback gates

### The Research Contribution

The SMSM + HNDL risk model is the publishable contribution:

```
R(D, C, T) = P(CRQC by T + L_D) * (1 - Q_C) * V_D
```

Where P is the probability a Cryptographically Relevant Quantum Computer exists by year T+L_D, Q_C is the quantum security level of state C, and V_D is the data class value multiplier. This answers the operational question: **which channel should move first, and why?**

## How It Works

```
TLS/SSH Endpoint
       |
       v
  NativeScanner ── openssl s_client ── parses key exchange, cert sig, chain bytes
       |
       v
  classify_evidence() ── maps evidence to S0-S4 state
       |
       +── build_recommendations() ── next steps + preconditions
       +── compute_risk() ── HNDL risk score with sigmoid CRQC model
       +── migration_plan() ── full transition plan between states
       |
       v
  FastAPI ── /scan, /scan/live (SSE), /history, /risk-score, /migration-plan
       |
       v
  React Dashboard ── KPI panels, risk gauge, state diagram, live connections
```

### Migration States (S0–S4)

| State | What It Means | Quantum Security |
|---|---|---|
| **S0_CLASSICAL** | RSA/ECDH/ECDSA only | None |
| **S1_PQC_READY** | PQC library installed, not negotiated | None |
| **S2_HYBRID_KX** | Hybrid key exchange (X25519MLKEM768), classical certs | Partial (0.3) |
| **S3_HYBRID_FULL** | Hybrid KX + ML-DSA certificates | Strong (0.8) |
| **S4_PQC_NATIVE** | Pure ML-KEM + ML-DSA, no classical fallback | Maximum (1.0) |

## Project Structure

```
backend/
  verifier-api/          FastAPI API — scanning, risk, state machine, SSE live streaming
    app/main.py          Endpoints: /scan, /scan/live, /history, /risk-score, /migration-plan
    app/live.py          Background scanner loop, SSE broadcast to dashboard
    app/db.py            SQLite scan history persistence
    app/deps.py          API key auth (optional)
    app/risk.py          HNDL risk scoring with sigmoid CRQC model
    app/state_machine.py SMSM classification, transitions, recommendations
    app/adapters/
      native.py          Real OpenSSL/OQS TLS probing (440 lines)
      demo.py            Deterministic demo profiles
      factory.py         Selects adapter based on PQC_MODE env var
    tests/               76 Python tests (risk, state machine, live scanner, API)
  ca/                    ML-DSA certificate chain generator (Root-Int-Leaf)
  metrics/               Prometheus exporter (demo handshake metrics)

frontend/
  dashboard/             React + TypeScript + Recharts single-file dashboard

services/
  server-pqc/            Go TLS server (ports 8443-8445)
  server-kemtls/         Go KEMTLS server (port 8446)
  server-ssh/            Go SSH + HTTP telemetry (port 22/8447)

infra/
  nginx/nginx.conf       Reverse proxy (port 80 → API + dashboard)
  prometheus/            Scrape config + alert rules

tests/
  e2e/                   Playwright E2E (7 scenarios)
```

## Running the Project

### Prerequisites

- Docker Desktop running
- Python 3.12+ (for local dev only)
- Node.js 20+ (for local dev only)
- Git

### Option 1: Full Stack with Docker (recommended)

```powershell
# Build and start everything
docker compose up --build

# Or start just the API
docker compose up --build verifier-api
```

| Service | URL / Port |
|---|---|
| Dashboard | `http://localhost:3000` |
| Nginx (unified entry) | `http://localhost:80` |
| Verifier API docs | `http://localhost:8000/docs` |
| Live SSE stream | `http://localhost:8000/scan/live` |
| PQC TLS servers | `8443`, `8444`, `8445` |
| KEMTLS server | `8446` |
| SSH server | `2222` (SSH), `8447` (telemetry) |
| Prometheus | `http://localhost:9091` |
| Metrics | `http://localhost:9090/metrics` |

### Option 2: Local Development (no Docker)

**Start the API:**

```powershell
cd backend/verifier-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PQC_MODE="demo"
uvicorn app.main:app --reload --port 8000
```

**Start the dashboard:**

```powershell
cd frontend/dashboard
npm install
npm run dev
```

Open `http://localhost:3000`.

### Option 3: Native PQC Mode (real crypto)

Requires liboqs + oqs-provider built with OpenSSL. The Docker image builds these automatically:

```powershell
$env:PQC_MODE="native"
docker compose up --build verifier-api
```

The NativeScanner will probe real TLS endpoints using `openssl s_client` with the OQS provider and detect actual ML-KEM/ML-DSA negotiations.

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `PQC_MODE` | `demo` | `demo` or `native` — selects scanner adapter |
| `SCAN_TARGETS` | `localhost:8443,8444,8445,8446,2222` | Comma-separated live scan targets |
| `LIVE_SCAN_INTERVAL` | `10` | Seconds between live scan cycles |
| `API_KEY` | (empty) | When set, POST endpoints require `X-API-Key` header |
| `SCAN_HISTORY_DB` | `scan_history.db` | SQLite database file path |
| `CRQC_MEDIAN_YEAR` | `2038` | CRQC probability sigmoid center |
| `CRQC_SPREAD_YEARS` | `5` | CRQC probability sigmoid spread |

## API

### Scan an endpoint (real TLS probe)

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/scan `
  -ContentType "application/json" `
  -Body '{"hostname":"localhost","port":8444}'
```

### Get live scan stream (SSE)

```powershell
curl http://localhost:8000/scan/live
```

### Get scan history

```powershell
Invoke-RestMethod "http://localhost:8000/history?limit=50"
```

### Compute HNDL risk

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/risk-score `
  -ContentType "application/json" `
  -Body '{"state":"S3_HYBRID_FULL","data_class":"confidential","lifetime_years":30}'
```

### Get migration plan

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/migration-plan `
  -ContentType "application/json" `
  -Body '{"current_state":"S2_HYBRID_KX","target_state":"S4_PQC_NATIVE"}'
```

### Full API reference

Open `http://localhost:8000/docs` for interactive Swagger UI.

## Running Tests

```powershell
# Python tests (76 tests)
cd backend/verifier-api
pip install -r requirements-dev.txt
python -m pytest tests/ -v

# Frontend build check
cd frontend/dashboard
npm install
npm run build
```

### Test Coverage

| File | Tests | What |
|---|---|---|
| `test_risk.py` | 18 | CRQC probability, risk bands, recommended actions, compute_risk |
| `test_state_machine.py` | 23 | State classification, transitions, recommendations, migration plans, verification |
| `test_live.py` | 10 | Target parsing, subscriber management, broadcast, scan failure handling |
| `test_api.py` | 6 | Endpoint integration, history stats |
| Go `*_test.go` | 10 | Server handlers, JSON serialization, SSH config |
| Playwright E2E | 7 | Dashboard views, KPI panels, risk controls, live indicator |

## Prometheus Alerts

| Alert | Severity | Condition |
|---|---|---|
| VerifierAPIDown | critical | API unreachable for 30s |
| HighScanFailureRate | warning | Scan rate < 0.01/sec for 5 min |
| HighScanLatency | warning | p95 latency > 10s for 5 min |
| MetricsCollectorDown | warning | Metrics collector unreachable for 1 min |

## Known Limitations

- KEMTLS requires an OQS-Go fork, not mainline Go
- StrongSwan native mode is Linux-only
- Mutual TLS is outside current scope
- OCSP/CRL for PQC certificate revocation is not implemented
- PQC SSH has no finalized RFC yet — uses experimental algorithm labels
- Phase 3 (attack demos) are standalone report generators, not connected to live traffic

## License

MIT — see [LICENSE](LICENSE).
