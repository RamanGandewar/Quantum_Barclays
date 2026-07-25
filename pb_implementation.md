# Post-Quantum Secure Communication System — Implementation Report

**Version:** 0.1.0
**Date:** 2026-07-11
**Status:** Demo Mode — Fully Operational

---

## 1. Project Overview

This is a reference implementation for a **Post-Quantum Secure Communication System** designed to help organizations migrate their communication channels (TLS, KEMTLS, SSH, VPN) to quantum-resistant cryptography.

The project's core contribution is the **Structured Migration State Machine (SMSM)** with **HNDL (Harvest Now, Decrypt Later) Risk Scoring**, which answers three operational questions:
1. Which channels should migrate first?
2. What state is each channel in today?
3. How urgent is the migration given data sensitivity and lifetime?

---

## 2. System Architecture

```
TLS / KEMTLS / SSH / VPN Endpoints (Ports 8443-8447, 2222)
        |
        v
Scanner Adapter Factory → DemoScanner / NativeScanner
        |
        v
Migration Verifier API (FastAPI, Port 8000)
        |
        +---- HNDL Risk Scorer (risk.py)
        +---- SMSM Transition Verifier (state_machine.py)
        +---- Prometheus Metrics
        |
        v
React Dashboard (Vite + Recharts, Port 3000)
```

---

## 3. Components

### 3.1 Go Services (Telemetry Endpoints)

| Service | Port(s) | Mode | Status |
|---------|---------|------|--------|
| server-pqc | 8443, 8444, 8445 | PQC-Native, Hybrid, Classical | Running |
| server-kemtls | 8446 | KEMTLS (KEM-based auth) | Running |
| server-ssh | 2222, 8447 | Classical, Hybrid, PQC-Native SSH | Running |
| client-measurement | CLI tool | Multi-run latency stats | Available |

### 3.2 Python Backend

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| Verifier API | `backend/verifier-api/app/main.py` | FastAPI service with 10 endpoints | Running |
| Scanner | `backend/verifier-api/app/scanner.py` | Public facade, delegates to adapter | Running |
| DemoScanner | `backend/verifier-api/app/adapters/demo.py` | Deterministic port-based profiles | Running |
| NativeScanner | `backend/verifier-api/app/adapters/native.py` | Placeholder for real OpenSSL/OQS | Stub |
| SMSM | `backend/verifier-api/app/state_machine.py` | 5-state migration machine | Running |
| HNDL Scorer | `backend/verifier-api/app/risk.py` | Risk scoring model | Running |
| CA Generator | `backend/ca/generate_pki.py` | Classical ECDSA chain + PQC manifest | Available |
| Metrics Collector | `backend/metrics/collector.py` | Prometheus exporter | Available |

### 3.3 Frontend

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| Dashboard | `frontend/dashboard/src/main.tsx` | React + Recharts + D3 UI | Running |
| Styles | `frontend/dashboard/src/styles.css` | Responsive layout | Running |

---

## 4. Migration States (SMSM)

| State | Label | Quantum Security | Description |
|-------|-------|:---:|-------------|
| S0_CLASSICAL | Classical | 0% | RSA/ECDH/ECDSA only |
| S1_PQC_READY | PQC Ready | 0% | PQC libraries installed, not negotiated |
| S2_HYBRID_KX | Hybrid Key Exchange | 30% | Hybrid key exchange, classical certs |
| S3_HYBRID_FULL | Hybrid Full | 80% | Hybrid KX + PQC/hybrid certificates |
| S4_PQC_NATIVE | PQC Native | 100% | ML-KEM + ML-DSA, no classical fallback |

**Allowed Transitions:** S0 → S1 → S2 → S3 → S4 (no skipping)

---

## 5. HNDL Risk Model

**Formula:** R(D, C, T) = P(CRQC by T + L_D) × (1 - Q_C) × V_D

| Variable | Meaning |
|----------|---------|
| L_D | Confidentiality lifetime of data class D (years) |
| Q_C | Quantum-security level of channel state C |
| V_D | Data value multiplier |
| P(CRQC) | Probability cryptographically relevant quantum computer exists before data expires |

**Default Parameters:**
- CRQC Median Year: 2038 (configurable via `CRQC_MEDIAN_YEAR` env var)
- CRQC Spread: 5 years (configurable via `CRQC_SPREAD_YEARS` env var)

**Data Class Value Multipliers:**

| Data Class | Value Multiplier (V_D) |
|------------|:---:|
| public | 0.1 |
| internal | 1.0 |
| confidential | 5.0 |
| secret | 25.0 |
| top-secret | 50.0 |

**Risk Bands:**

| Score Range | Band |
|-------------|------|
| 0 - 1 | low |
| 1 - 3 | medium |
| 3 - 10 | high |
| 10+ | critical |

---

## 6. API Endpoints

### 6.1 GET /health
Returns API health status.
**Response:** `{"status": "ok"}`

### 6.2 POST /scan
Scans a TLS, KEMTLS, SSH, or demo endpoint and returns SMSM state.
**Request:** `{"hostname": "localhost", "port": 8444, "timeout_seconds": 2.0}`
**Response:** Endpoint, state, state_label, evidence (negotiated_group, certificate_algorithm, handshake_bytes, latency_ms), recommendations

### 6.3 POST /risk-score
Computes HNDL risk for a state and data class.
**Request:** `{"state": "S3_HYBRID_FULL", "data_class": "confidential", "lifetime_years": 30}`
**Response:** crqc_probability, quantum_security_level, value_multiplier, risk_score, risk_band, recommended_action

### 6.4 POST /migration-plan
Returns target state, next state, preconditions, rollback conditions, and verification criteria.
**Request:** `{"current_state": "S2_HYBRID_KX", "target_state": "S4_PQC_NATIVE"}`
**Response:** current_state, target_state, next_state, preconditions, rollback_conditions, verification_criteria

### 6.5 POST /verify-transition
Validates whether evidence satisfies transition rules.
**Request:** `{"current_state": "S0_CLASSICAL", "target_state": "S4_PQC_NATIVE", "evidence": {"negotiated_group": "ML-KEM-768", "certificate_algorithm": "ML-DSA-65"}}`
**Response:** allowed (boolean), missing_preconditions, verification_criteria

### 6.6 GET /handshake-comparison
Returns comparison data for Classical, Hybrid, PQC-Native, and KEMTLS profiles.

### 6.7 GET /certificates
Returns the expected CA chain model (Root, Intermediate, Leaf TLS, Leaf KEMTLS).

### 6.8 GET /connections
Returns connection evidence for dashboard tables.

### 6.9 GET /state-machine
Returns SMSM nodes and transitions.

### 6.10 GET /metrics
Prometheus-compatible metrics (pqc_scans_total, pqc_risk_scores_total, pqc_scan_latency_seconds).

---

## 7. Implementation Steps

### Step 1: Install Dependencies

**Python (Verifier API):**
```powershell
cd backend\verifier-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Node.js (Dashboard):**
```powershell
cd frontend\dashboard
npm install
```

**Go (Services):**
```powershell
winget install Go
```

### Step 2: Start Go Telemetry Services

Open separate PowerShell windows for each:

```powershell
# Window 1 — PQC TLS
cd D:\barclays_qs\Quantum_Barclays\services\server-pqc
go run .
# Output: serving classical profile on :8445, hybrid on :8444, pqc-native on :8443

# Window 2 — KEMTLS
cd D:\barclays_qs\Quantum_Barclays\services\server-kemtls
go run .
# Output: serving KEMTLS telemetry profile on :8446

# Window 3 — SSH
cd D:\barclays_qs\Quantum_Barclays\services\server-ssh
go mod tidy
go run .
# Output: ssh telemetry listening on :8447, pqc ssh server listening on :22 in hybrid mode
```

### Step 3: Start Python Verifier API

```powershell
cd D:\barclays_qs\Quantum_Barclays\backend\verifier-api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Output: Selected DemoScanner adapter, Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Start React Dashboard

```powershell
cd D:\barclays_qs\Quantum_Barclays\frontend\dashboard
npm run dev
# Output: VITE ready, Local: http://localhost:3000/
```

### Step 5: Verify All Services

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Scan TLS hybrid port
Invoke-RestMethod -Method Post "http://localhost:8000/scan" -ContentType "application/json" -Body '{"hostname":"localhost","port":8444}'

# Scan SSH port
Invoke-RestMethod -Method Post "http://localhost:8000/scan" -ContentType "application/json" -Body '{"hostname":"localhost","port":2222}'

# Compute risk score
Invoke-RestMethod -Method Post "http://localhost:8000/risk-score" -ContentType "application/json" -Body '{"state":"S3_HYBRID_FULL","data_class":"confidential","lifetime_years":30}'

# Verify transition (should fail — can't skip states)
Invoke-RestMethod -Method Post "http://localhost:8000/verify-transition" -ContentType "application/json" -Body '{"current_state":"S0_CLASSICAL","target_state":"S4_PQC_NATIVE","evidence":{"negotiated_group":"ML-KEM-768","certificate_algorithm":"ML-DSA-65"}}'

# Migration plan
Invoke-RestMethod -Method Post "http://localhost:8000/migration-plan" -ContentType "application/json" -Body '{"current_state":"S2_HYBRID_KX","target_state":"S4_PQC_NATIVE"}'
```

### Step 6: Run Tests

```powershell
cd backend\verifier-api
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
```

### Step 7: Run Security Demos

```powershell
cd demos\security
python hndl_attack_sim.py
python confidentiality_demo.py --profile pqc-native
python integrity_replay_demo.py --byte-offset 42
python authenticity_demo.py
```

### Step 8: Run Benchmarks

```powershell
cd benchmarks
python run_benchmarks.py --runs 100
# Output: benchmarks/results/latest.json
```

### Step 9: Generate CA Certificates

```powershell
cd backend\ca
pip install -r requirements.txt
python generate_pki.py --output certs-demo
```

### Step 10: Full Docker Stack (Optional)

```powershell
Copy-Item .env.example .env
docker compose up --build
```

---

## 8. Test Results

### 8.1 Health Check
**Command:** `Invoke-RestMethod -Uri "http://localhost:8000/health"`
**Result:** `{"status": "ok"}"` — PASS

### 8.2 Scan TLS Hybrid Port (8444)
**Command:** `Invoke-RestMethod -Method Post "http://localhost:8000/scan" -Body '{"hostname":"localhost","port":8444}'`
**Result:**
- State: `S3_HYBRID_FULL`
- Negotiated Group: `X25519MLKEM768`
- Certificate Algorithm: `ML-DSA-65`
- Handshake Bytes: 18,400
- Latency: 31ms
- PASS

### 8.3 Scan SSH Port (2222)
**Command:** `Invoke-RestMethod -Method Post "http://localhost:8000/scan" -Body '{"hostname":"localhost","port":2222}'`
**Result:**
- State: `S3_HYBRID_FULL`
- Negotiated Group: `X25519MLKEM768`
- Certificate Algorithm: `ml-dsa-65`
- Handshake Bytes: 4,200
- Latency: 16ms
- PASS

### 8.4 Risk Score Computation
**Command:** `Invoke-RestMethod -Method Post "http://localhost:8000/risk-score" -Body '{"state":"S3_HYBRID_FULL","data_class":"confidential","lifetime_years":30}'`
**Result:**
- CRQC Probability: 0.973403 (97.34%)
- Quantum Security Level: 0.8
- Value Multiplier: 5.0
- Risk Score: 0.973403
- Risk Band: low
- PASS

### 8.5 Transition Verification (S0 → S4)
**Command:** `Invoke-RestMethod -Method Post "http://localhost:8000/verify-transition" -Body '{"current_state":"S0_CLASSICAL","target_state":"S4_PQC_NATIVE","evidence":{"negotiated_group":"ML-KEM-768","certificate_algorithm":"ML-DSA-65"}}'`
**Result:**
- Allowed: `False`
- Missing Preconditions: `["Transitions must pass through each intermediate SMSM state."]`
- PASS — State skipping is correctly blocked

### 8.6 Migration Plan (S2 → S4)
**Command:** `Invoke-RestMethod -Method Post "http://localhost:8000/migration-plan" -Body '{"current_state":"S2_HYBRID_KX","target_state":"S4_PQC_NATIVE"}'`
**Result:**
- Next State: `S3_HYBRID_FULL`
- Preconditions: ML-KEM without classical fallback, ML-DSA cert chain deployed, legacy client exception list approved
- Rollback Conditions: Client compatibility failure exceeds threshold, handshake error rate increases, certificate validation failure
- Verification Criteria: Negotiated group is ML-KEM-768, certificate contains ML-DSA, no classical fallback
- PASS

---

## 9. Handshake Comparison

| Profile | Key Exchange | Signature Algorithm | Client Key Share | Server Key Share | Cert Chain | Total Handshake | Latency |
|---------|-------------|-------------------|-----------------|-----------------|------------|----------------|---------|
| Classical | X25519 | ECDSA P-256 | 32 bytes | 32 bytes | 2,600 bytes | 5,100 bytes | 18ms |
| Hybrid | X25519MLKEM768 | ML-DSA-65 | 1,216 bytes | 1,120 bytes | 13,200 bytes | 18,400 bytes | 31ms |
| PQC-Native | ML-KEM-768 | ML-DSA-65 | 1,184 bytes | 1,088 bytes | 13,200 bytes | 18,100 bytes | 34ms |
| KEMTLS | ML-KEM-768 | KEM decapsulation | 1,184 bytes | 1,088 bytes | 11,800 bytes | 15,800 bytes | 39ms |

---

## 10. Port Mapping

| Service | Port(s) | Protocol | State |
|---------|---------|----------|-------|
| PQC TLS — Classical | 8445 | TLS | S0_CLASSICAL |
| PQC TLS — Hybrid | 8444 | TLS | S3_HYBRID_FULL |
| PQC TLS — PQC-Native | 8443 | TLS | S4_PQC_NATIVE |
| KEMTLS | 8446 | TLS (KEM auth) | S4_PQC_NATIVE |
| SSH — Server | 2222 | SSH | S3_HYBRID_FULL |
| SSH — Telemetry | 8447 | HTTP | S3_HYBRID_FULL |
| Verifier API | 8000 | HTTP | — |
| Dashboard | 3000 | HTTP | — |
| Metrics | 9090 | HTTP | — |
| Prometheus | 9091 | HTTP | — |

---

## 11. What Works vs What Needs Work

### Working (Demo Mode)
- Verifier API with all 10 endpoints
- SMSM state classification (S0-S4)
- HNDL risk scoring with configurable parameters
- DemoScanner with deterministic port profiles
- React Dashboard with all 6 views
- Migration plan generation with preconditions
- Transition verification with rollback gates
- Go telemetry services (HTTP JSON endpoints)
- Security demo scripts (4 scripts with JSON output)
- Benchmark runner with PRD schema
- CA generator (classical ECDSA chain)
- Prometheus metrics exporter
- CI pipeline (Python, Go, Frontend)

### Stub / Placeholder
- NativeScanner — raises NotImplementedError, needs real OpenSSL/OQS
- Go services — serve hardcoded JSON, need CIRCL/OQS for real TLS
- CA PQC manifest — metadata only, real ML-DSA certs need OpenSSL+oqs-provider
- VPN configuration — template only, needs StrongSwan on Linux

### Not Implemented
- Mutual TLS with ML-DSA client certs
- OCSP/CRL for PQC certificate revocation
- Postgres scan history persistence
- HSM-backed CA keys
- Multi-tenant verifier API with SSO

---

## 12. Environment Requirements

| Tool | Version | Used For |
|------|---------|----------|
| Python | 3.12+ | All backend services |
| Go | 1.22+ | TLS/KEMTLS/SSH services |
| Node.js | 20+ | Dashboard |
| Docker | 24+ | Full stack deployment |
| OpenSSL | 3.3+ | Native mode only |
| liboqs | 0.10+ | Native mode only |
| oqs-provider | 0.6+ | Native mode only |
| Cloudflare CIRCL | latest | Native mode only |
| StrongSwan | 6.x | Native mode only (Linux) |

---

## 13. Key Files Reference

| File | Purpose |
|------|---------|
| `backend/verifier-api/app/main.py` | FastAPI routes and Prometheus metrics |
| `backend/verifier-api/app/models.py` | Pydantic models (ScanRequest, RiskScoreRequest, etc.) |
| `backend/verifier-api/app/state_machine.py` | SMSM logic, classify_evidence(), migration_plan() |
| `backend/verifier-api/app/risk.py` | HNDL risk model, crqc_probability(), risk_band() |
| `backend/verifier-api/app/scanner.py` | Public scanner facade |
| `backend/verifier-api/app/adapters/demo.py` | DemoScanner with port profiles |
| `backend/verifier-api/app/adapters/native.py` | NativeScanner stub |
| `backend/verifier-api/app/adapters/factory.py` | Adapter selection from env var |
| `backend/verifier-api/app/telemetry.py` | Static telemetry data (handshake comparison, connections) |
| `frontend/dashboard/src/main.tsx` | React dashboard component |
| `services/server-pqc/main.go` | PQC TLS telemetry endpoints |
| `services/server-kemtls/main.go` | KEMTLS telemetry endpoint |
| `services/server-ssh/main.go` | SSH server + telemetry |
| `services/server-ssh/telemetry.go` | SSH telemetry HTTP endpoint |
| `services/client-measurement/main.go` | Multi-run latency measurement client |
| `backend/ca/generate_pki.py` | Classical CA chain + PQC manifest |
| `backend/metrics/collector.py` | Prometheus metrics exporter |
| `benchmarks/run_benchmarks.py` | Benchmark runner |
| `infra/prometheus/prometheus.yml` | Prometheus scrape config |
| `docker-compose.yml` | Full service orchestration |

---

## 14. Presentation Demo Script

1. **Open Dashboard** — Navigate to `http://localhost:3000`
   - Show the 5 KPI panels at the top
   - Point out the status pill showing current migration state

2. **Click Profile Buttons** — Click "Classical", "Hybrid", "PQC Native", "KEMTLS"
   - Watch the state machine diagram highlight the active state
   - Watch the KPI panels update with new evidence

3. **Change Data Class** — Select "secret" or "top-secret" in Risk Analysis panel
   - Watch the risk score increase
   - Watch the risk band change from low → medium → high

4. **Slide Lifetime** — Drag the lifetime slider to 60 years
   - Watch CRQC probability increase
   - Watch the recommended action change

5. **Show Handshake Comparison** — Point to the bar chart
   - Classical: 5,100 bytes vs Hybrid: 18,400 bytes
   - Explain the ~3.6x overhead of adding PQC

6. **Show SSH State** — Point to the SSH State KPI panel
   - Explain that SSH is tracked separately with lower handshake overhead

7. **Run API Commands** — Open PowerShell and run the 3 commands from Section 8
   - Show scan on port 2222 (SSH)
   - Show verify-transition failure (state skipping blocked)
   - Show migration plan with preconditions

8. **Show API Docs** — Navigate to `http://localhost:8000/docs`
   - Demonstrate interactive Swagger UI
   - Show all 10 endpoints with request/response schemas

---

## 15. Known Limitations

1. **Demo telemetry** — Deterministic adapters do not reflect real cryptographic negotiation. Not valid for production security audits.
2. **KEMTLS** — Requires OQS-Go fork, not mainline Go.
3. **StrongSwan VPN** — Linux-only, requires kernel capabilities (NET_ADMIN).
4. **Mutual TLS** — Out of scope; client-side PQC authentication not implemented.
5. **OCSP/CRL** — PQC certificate revocation not implemented; no finalized IETF standard.
6. **PQC SSH** — No finalized RFC for ML-KEM SSH key exchange; uses experimental algorithm labels.

---

## 16. Next Steps for Production

1. Install liboqs 0.10+, oqs-provider 0.6+, OpenSSL 3.3+
2. Set `PQC_MODE=native` in `.env`
3. Implement `NativeScanner` in `adapters/native.py` with real OpenSSL/OQS probing
4. Generate real ML-DSA certificates using OpenSSL+oqs-provider
5. Replace Go services with CIRCL/OQS-backed real TLS listeners
6. Deploy StrongSwan on Linux for VPN mode
7. Add Postgres for scan history persistence
8. Set up Prometheus alerting for high HNDL risk scores
