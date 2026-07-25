# Post-Quantum Secure Communication System

Production-oriented reference implementation for a post-quantum secure communication stack based on the PRD in `PQC_Project_Plan.docx`.

The project implements the migration-verification plane, HNDL risk scoring model, dashboard, service contracts, container layout, certificate automation, TLS/KEMTLS/SSH telemetry profiles, benchmark tooling, security demonstrations, and deployment documentation for a quantum-resilient migration framework.

This repository has two modes:

- **Runnable demo mode:** works on a normal development machine and exercises the full architecture with deterministic PQC telemetry adapters.
- **Native production mode:** swaps adapters for real OpenSSL/OQS, CIRCL, OQS-Go, and StrongSwan integrations.

## Novel Contribution

The project's publishable contribution is the **Structured Migration State Machine (SMSM) with HNDL Risk Scoring**. Existing PQC projects such as Open Quantum Safe, Cloudflare CIRCL, and the Paquin-Stebila-Tamvada 2020 benchmarking work show that PQC algorithms can run in protocols. They do not answer the operational migration question: which channel should move first, what state is it in today, what evidence proves that state, and how does data lifetime change urgency?

SMSM solves that gap by combining endpoint evidence, migration-state verification, rollback gates, and time-bounded Harvest Now, Decrypt Later risk scoring:

```text
R(D, C, T) = P(CRQC by T + L_D) * (1 - Q_C) * V_D
```

This is the research contribution suitable for IEEE S&P, ACM CCS, USENIX Security, or PQCrypto as an applied cryptography and systems-security migration framework. See `docs/research-notes.md` for the formal SMSM definition, HNDL risk model mathematical derivation, gap analysis vs existing work (OQS, Cloudflare CIRCL, Paquin-Stebila-Tamvada 2020), and target publication venue justification.

## Environment Requirements

| Tool | Version | Required For |
| --- | --- | --- |
| Python | 3.12+ | All backend services |
| Go | 1.22+ | TLS/KEMTLS/SSH services |
| Node.js | 20+ | Dashboard |
| Docker | 24+ | Full stack deployment |
| OpenSSL | 3.3+ | Native mode only |
| liboqs | 0.10+ | Native mode only |
| oqs-provider | 0.6+ | Native mode only |
| Cloudflare CIRCL | latest | Native mode only |
| StrongSwan | 6.x | Native mode only (Linux) |

## What This Repository Contains

| Area | Path | Status |
| --- | --- | --- |
| Migration Verifier API | `backend/verifier-api` | Implemented FastAPI service |
| HNDL Risk Scorer | `backend/verifier-api/app/risk.py` | Implemented mathematical model |
| SMSM State Machine | `backend/verifier-api/app/state_machine.py` | Implemented S0-S4 transition logic |
| Scanner Adapters | `backend/verifier-api/app/adapters` | Demo and native adapter boundary |
| PQC CA Automation | `backend/ca` | Classical chain generator plus OpenSSL/OQS-ready PQC manifest |
| Metrics Collector | `backend/metrics` | Prometheus exporter |
| PQC TLS Service | `services/server-pqc` | Go service contract and telemetry adapter for ports 8443/8444/8445 |
| KEMTLS Service | `services/server-kemtls` | Go service contract and KEMTLS telemetry adapter |
| SSH Service | `services/server-ssh` | Go SSH server and telemetry endpoint |
| Measurement Client | `services/client-measurement` | Go multi-run latency/statistics client |
| Benchmarks | `benchmarks` | Network profile definitions and benchmark runner |
| Security Demos | `demos/security` | Confidentiality, authenticity, integrity, and HNDL scripts |
| VPN Configuration | `infra/vpn` | StrongSwan/OQS config templates |
| Dashboard | `frontend/dashboard` | React + TypeScript + Recharts + D3 UI |
| Container Orchestration | `docker-compose.yml` | Full service map |
| CI | `.github/workflows/ci.yml` | Python, frontend, and Docker checks |
| Docs | `docs` | Architecture, API, research, limitations, and traceability |

## Architecture

```text
TLS / KEMTLS / SSH / VPN Endpoints
       |
       v
Scanner Adapter Factory ---- DemoScanner / NativeScanner
       |
       v
Migration Verifier API  <---- CA metadata / server telemetry
       |
       +---- HNDL Risk Scorer
       +---- SMSM Transition Verifier
       +---- Prometheus Metrics
       |
       v
React Dashboard
```

## Migration States

| State | Meaning | Classical Security | Quantum Security |
| --- | --- | --- | --- |
| `S0_CLASSICAL` | RSA/ECDH/ECDSA only | Full | None |
| `S1_PQC_READY` | PQC libraries present, no PQC negotiated | Full | None |
| `S2_HYBRID_KX` | Hybrid key exchange, classical certs | Full | Partial |
| `S3_HYBRID_FULL` | Hybrid KX and hybrid/PQC certificates | Full | Strong |
| `S4_PQC_NATIVE` | ML-KEM + ML-DSA without classical fallback | Reduced | Maximum |

## Quick Start

Run the verifier API:

```powershell
cd backend/verifier-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

<details>
<summary>Linux / macOS</summary>

```bash
cd backend/verifier-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

</details>

API docs: `http://localhost:8000/docs`

Run the dashboard:

```powershell
cd frontend/dashboard
npm install
npm run dev
```

Dashboard: `http://localhost:3000`

Run the full stack:

```powershell
docker compose up --build
```

| Service | URL / Port |
| --- | --- |
| Dashboard | `http://localhost:3000` |
| Verifier API | `http://localhost:8000/docs` |
| PQC TLS demo | `8443`, `8444`, `8445` |
| KEMTLS demo | `8446` |
| SSH demo | `2222`, telemetry `8447` |
| Metrics | `http://localhost:9090/metrics` |
| Prometheus | `http://localhost:9091` |
| VPN | `500/udp`, `4500/udp` |

## API Examples

Scan an endpoint:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/scan `
  -ContentType "application/json" `
  -Body '{"hostname":"localhost","port":8444}'
```

<details>
<summary>Linux / macOS</summary>

```bash
# Scan an endpoint
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"hostname":"localhost","port":8444}'
```

</details>

Compute risk:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/risk-score `
  -ContentType "application/json" `
  -Body '{"state":"S3_HYBRID_FULL","data_class":"confidential","lifetime_years":30}'
```

<details>
<summary>Linux / macOS</summary>

```bash
# Compute risk
curl -X POST http://localhost:8000/risk-score \
  -H "Content-Type: application/json" \
  -d '{"state":"S3_HYBRID_FULL","data_class":"confidential","lifetime_years":30}'
```

</details>

Get a migration plan:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/migration-plan `
  -ContentType "application/json" `
  -Body '{"current_state":"S2_HYBRID_KX","target_state":"S4_PQC_NATIVE"}'
```

<details>
<summary>Linux / macOS</summary>

```bash
# Get a migration plan
curl -X POST http://localhost:8000/migration-plan \
  -H "Content-Type: application/json" \
  -d '{"current_state":"S2_HYBRID_KX","target_state":"S4_PQC_NATIVE"}'
```

</details>

## Switching To Native Mode

Native mode is selected by environment variables:

```powershell
$env:PQC_MODE="native"
$env:OQS_PROVIDER_PATH="/usr/local/lib/ossl-modules/oqsprovider.so"
$env:CIRCL_ENABLED="true"
```

<details>
<summary>Linux / macOS</summary>

```bash
export PQC_MODE=native
export OQS_PROVIDER_PATH=/usr/local/lib/ossl-modules/oqsprovider.so
export CIRCL_ENABLED=true
source .venv/bin/activate
```

</details>

Replace or extend these files:

| File | Function/Class | Native replacement |
| --- | --- | --- |
| `backend/verifier-api/app/scanner.py` | `scan_endpoint(request: ScanRequest) -> dict` | Keep facade, use factory-selected native adapter |
| `backend/verifier-api/app/adapters/demo.py` | `class DemoTelemetryAdapter(DemoScanner)` / `class DemoScanner(BaseScanner)` | Demo implementation only |
| `backend/verifier-api/app/adapters/native.py` | `class NativeScanner(BaseScanner)` | Implement OpenSSLScanner-compatible logic |
| `backend/verifier-api/app/adapters/base.py` | `scan(self, hostname: str, port: int) -> ScanResult` | Preserve interface |
| `services/server-pqc/main.go` | `main()` | Replace telemetry HTTP profile with CIRCL/OQS TLS listener |
| `services/server-kemtls/main.go` | `main()` | Replace telemetry HTTP profile with OQS-Go KEMTLS fork |
| `services/server-ssh/main.go` | `sshConfig(profile Telemetry)` | Replace experimental labels with finalized PQC SSH algorithms when available |

Specifically, replace the `DemoTelemetryAdapter` behavior with a real `OpenSSLScanner` that implements the same `BaseScanner` interface:

```python
scan(self, hostname: str, port: int) -> ScanResult
get_cert_chain(self, hostname: str, port: int) -> list[dict]
get_kex_info(self, hostname: str, port: int) -> dict
is_available(self) -> bool
```

Set `PQC_MODE=native`. Set `OQS_PROVIDER_PATH` to the oqs-provider `.so` path. Set `CIRCL_ENABLED=true` for Go services.

Copy `.env.example` to `.env` and edit before running Docker Compose:

```powershell
Copy-Item .env.example .env
```

<details>
<summary>Linux / macOS</summary>

```bash
cp .env.example .env
```

</details>

## Adapter Interface Contract

Any scanner replacing demo mode must implement `BaseScanner` in `backend/verifier-api/app/adapters/base.py`:

```python
class BaseScanner(ABC):
    def scan(self, hostname: str, port: int) -> ScanResult: ...
    def get_cert_chain(self, hostname: str, port: int) -> list[dict]: ...
    def get_kex_info(self, hostname: str, port: int) -> dict: ...
    def is_available(self) -> bool: ...
```

Return contract:

- `scan` returns `ScanResult(endpoint, state, evidence, recommendations)`.
- `evidence` must include negotiated group, certificate or host-key algorithm, chain size, handshake bytes, latency, PQC dependency detection, and details.
- `get_cert_chain` returns dictionaries containing `subject`, `algorithm_oid`, and `size_bytes`.
- `get_kex_info` returns `algorithm`, `client_key_share_bytes`, `server_key_share_bytes`, and `shared_secret_size_bytes`.
- Missing native dependencies must not crash API startup. `is_available()` returns `False`, factory logs a warning, and demo mode is used.
- Runtime scan failures should raise a clear exception in native mode or return deterministic fallback evidence in demo mode.

## Security Demo Outputs

| Script | Output file | Format | Key fields |
| --- | --- | --- | --- |
| `demos/security/confidentiality_demo.py` | `demos/security/output/confidentiality_report.json` | JSON | `profile_used`, `captured_packet_count`, `ciphertext_bytes_visible`, `plaintext_bytes_visible`, `verdict` |
| `demos/security/integrity_replay_demo.py` | `demos/security/output/integrity_report.json` | JSON | `byte_offset_modified`, `original_byte_value`, `modified_byte_value`, `tls_alert_received`, `alert_code`, `verdict` |
| `demos/security/hndl_attack_sim.py` | `demos/security/output/hndl_report.json` | JSON | `classical_session_key_share_bytes_captured`, `ecdlp_simulation_result_on_test_curve`, `pqc_session_key_share_bytes_captured`, `mlwe_attack_result`, `verdict` |
| `demos/security/authenticity_demo.py` | `demos/security/output/authenticity_report.json` | JSON | `original_cert_signature_valid`, `tampered_byte_position`, `tampered_cert_signature_valid`, `ml_dsa_verification_error_message`, `verdict` |

## Benchmark Output Format

`benchmarks/run_benchmarks.py` writes `benchmarks/results/latest.json`.

```json
{   
  "run_id": "uuid-string",
  "timestamp": "ISO-8601",
  "network_profile": {
    "rtt_ms": 100,
    "bandwidth_mbps": 10,
    "packet_loss_pct": 1.0
  },
  "results": [
    {
      "mode": "classical | hybrid | pqc-native | kemtls",
      "runs": 100,
      "handshake_bytes": {
        "client_hello_key_share": 32,
        "server_hello_key_share": 32,
        "certificate_chain": 3000,
        "certificate_verify": 64,
        "finished": 52,
        "total": 5200
      },
      "latency_ms": {
        "mean": 12.4,
        "p50": 11.8,
        "p95": 18.2,
        "p99": 24.1,
        "min": 9.1,
        "max": 31.0
      },
      "migration_state": "S0_CLASSICAL",
      "hndl_risk_score": 0.87
    }
  ]
}
```

Field meanings:

- `run_id`: unique benchmark run UUID.
- `timestamp`: UTC ISO-8601 timestamp.
- `network_profile`: test condition metadata.
- `handshake_bytes`: per-message and total handshake byte counts.
- `latency_ms`: aggregate latency statistics.
- `migration_state`: SMSM state assigned to the mode.
- `hndl_risk_score`: representative HNDL score for the mode.

## Known Limitations

- KEMTLS requires an OQS-Go fork, not mainline Go.
- StrongSwan native mode is Linux-only.
- Mutual TLS is outside current scope.
- OCSP/CRL for PQC certificate revocation is not implemented.
- Demo telemetry is not valid for production security audits.
- PQC SSH has no finalized RFC yet. The hybrid SSH mode in this project uses experimental algorithm labels (X25519MLKEM768 for key exchange, ml-dsa-65 for host keys) that may change when an IETF standard is finalized. Do not treat SSH migration state as authoritative until a standard is published.

See `docs/known-limitations.md` for full detail.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a new scanner adapter, migration state, or data classification to the HNDL scorer. Includes code style requirements, test rules, and PR checklist.

## PRD Coverage

The full traceability matrix is in `docs/prd-traceability.md`. Every phase from the PRD has a designated folder and runnable or adapter-ready implementation:

- Phase 0: Toolchain, Docker, React, Go, Python structure.
- Phase 1: CA lifecycle automation and PQC manifest.
- Phase 2: PQC-TLS profiles, telemetry endpoints, measurement client.
- Phase 3: KEMTLS profile and size comparison.
- Phase 4: StrongSwan/OQS VPN configuration template.
- Phase 5: Migration verifier, SMSM, HNDL risk scorer.
- Phase 6: Security property and HNDL demonstration scripts.
- Phase 7: Dashboard views for overview, comparison, risk, state machine, SSH, and connections.
- Phase 8: Compose, Prometheus config, and CI pipeline.

## Test Commands

```powershell
cd backend/verifier-api
pip install -r requirements-dev.txt
pytest
```

<details>
<summary>Linux / macOS</summary>

```bash
cd backend/verifier-api
pip install -r requirements-dev.txt
pytest
```

</details>

```powershell
cd frontend/dashboard
npm install
npm run build
```

<details>
<summary>Linux / macOS</summary>

```bash
cd frontend/dashboard
npm install
npm run build
```

</details>

Run CA generation:

```powershell
cd backend/ca
pip install -r requirements.txt
python generate_pki.py --output certs-demo
```

<details>
<summary>Linux / macOS</summary>

```bash
cd backend/ca
pip install -r requirements.txt
python generate_pki.py --output certs-demo
```

</details>

Run security demos:

```powershell
python demos/security/hndl_attack_sim.py
```

<details>
<summary>Linux / macOS</summary>

```bash
python demos/security/hndl_attack_sim.py
```

</details>

```powershell
python demos/security/confidentiality_demo.py --profile pqc-native
```

<details>
<summary>Linux / macOS</summary>

```bash
python demos/security/confidentiality_demo.py --profile pqc-native
```

</details>

```powershell
python demos/security/integrity_replay_demo.py --byte-offset 42
```

<details>
<summary>Linux / macOS</summary>

```bash
python demos/security/integrity_replay_demo.py --byte-offset 42
```

</details>

```powershell
python demos/security/authenticity_demo.py
```

<details>
<summary>Linux / macOS</summary>

```bash
python demos/security/authenticity_demo.py
```

</details>

Run benchmarks:

```powershell
python benchmarks/run_benchmarks.py --runs 100
```

<details>
<summary>Linux / macOS</summary>

```bash
python benchmarks/run_benchmarks.py --runs 100
```

</details>

Run a measurement client after starting the Go telemetry services:

```powershell
cd services/client-measurement
go run . --endpoint http://127.0.0.1:8444/session-info --runs 100
```

<details>
<summary>Linux / macOS</summary>

```bash
# Same command on Linux/macOS
cd services/client-measurement
go run . --endpoint http://127.0.0.1:8444/session-info --runs 100
```

</details>

## Repository Layout

```text
CONTRIBUTING.md          How to extend adapters, states, and data classes
backend/
  ca/                    PQC/classical CA automation
  metrics/               Prometheus metrics collector
  verifier-api/          FastAPI verifier, scorer, SMSM
benchmarks/              Network-condition benchmark runner
demos/
  security/              Security property and HNDL demo scripts
docs/
  api.md                 API contract
  architecture.md        System architecture
  known-limitations.md   Native and standards limitations
  prd-traceability.md    Requirement-to-file mapping
  research-notes.md      SMSM and HNDL research framing
frontend/
  dashboard/             React monitoring dashboard
infra/
  nginx/                 Reverse proxy config
  prometheus/            Prometheus scrape config
  vpn/                   StrongSwan/OQS templates
services/
  client-measurement/    Multi-run measurement client
  server-pqc/            Go PQC TLS telemetry service
  server-kemtls/         Go KEMTLS telemetry service
  server-ssh/            Go SSH telemetry service
tests/
  e2e/                   E2E placeholders
```

## Production Readiness Checklist

- Configure real TLS scanners through OpenSSL/OQS or CIRCL adapters.
- Replace demo CA material with hardware-backed or KMS-backed CA keys.
- Store scan history in Postgres instead of process memory.
- Protect the verifier API with SSO, mTLS, or a service mesh policy.
- Export metrics to Prometheus and alert on high HNDL scores.
- Run native StrongSwan/OQS containers on Linux hosts with required kernel capabilities.
- Attach packet captures and native provider logs for audit evidence.

## Roadmap

| Item | Priority | Depends On |
| --- | --- | --- |
| Native OpenSSL/OQS scanner adapter | High | liboqs + oqs-provider install |
| Native CIRCL Go TLS scanner | High | Go 1.22 + CIRCL |
| Mutual TLS with ML-DSA client certs | Medium | Native CA + client cert distribution |
| OCSP/CRL when IETF standard finalizes | Medium | IETF PQC revocation RFC |
| SSH native mode when RFC finalizes | Medium | draft-kampanakis-curdle-ssh-pq-ke RFC |
| Postgres scan history backend | Medium | Production deployment |
| KEMTLS mainline Go support | Low | Upstream Go pluggable handshake |
| Hardware Security Module (HSM) CA keys | Low | Production deployment |
| Alert rules for high HNDL risk scores | Low | Prometheus + Alertmanager |
| Multi-tenant verifier API with SSO | Low | Production deployment |

## Versioning

This project uses [Semantic Versioning](https://semver.org). The current version is tracked in `VERSION` file at the repository root.

- **Major version** bumps when a migration state definition changes or the HNDL risk model formula changes — these are breaking changes to audit evidence.
- **Minor version** bumps when a new scanner adapter, service, or data classification is added.
- **Patch version** bumps for bug fixes, documentation updates, and dependency upgrades.

See `CHANGELOG.md` for the full history.

## License

This project is intended as an academic and industry project reference implementation. Add an organization-approved license before public release.
