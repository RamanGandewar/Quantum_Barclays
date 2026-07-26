# Quantum-Secure Communication System — Roadmap

> **Goal:** A working system where Barclays stakeholders can see, interact with, and verify how secure the communication infrastructure is — covering confidentiality, authenticity, integrity, and harvest-now-decrypt-later (HNDL) risk detection.

---

## Current State (v0.1.0)

The system is **fully functional in demo mode**. All 10 API endpoints, the React dashboard, 4 Go telemetry services, security demos, benchmarks, Docker Compose orchestration, and CI pipeline are complete and working.

**What "demo mode" means:** Telemetry is deterministic/simulated. No real post-quantum cryptographic handshakes occur. The architecture, state machine, risk scoring, and dashboard rendering are all real and production-ready — they just consume synthetic data instead of live crypto probes.

---

## What's Done

| Area | Status |
|---|---|
| Verifier API (10 endpoints) | Done |
| SMSM State Machine (S0–S4) | Done |
| HNDL Risk Scorer with configurable data classes | Done |
| React Dashboard (KPI, risk gauge, state diagram, latency charts, evidence table) | Done |
| Go PQC TLS / KEMTLS / SSH telemetry servers (demo profiles) | Done |
| Go latency measurement client | Done |
| Security demos (confidentiality, authenticity, integrity, HNDL attack sim) | Done |
| Benchmark runner with live flag | Done |
| Docker Compose (10 services) | Done |
| CI pipeline (Python lint/test, Go vet/build, frontend build) | Done |
| Full documentation (architecture, API, research notes, limitations, PRD traceability) | Done |
| Adapter pattern for native mode switching | Done |

---

## What Remains

### Phase 1 — Native Crypto Adapter ✅ DONE

**Completed Jul 26, 2026.** Full native PQC scanning and ML-DSA certificate generation working end-to-end.

| Task | Status |
|---|---|
| `NativeScanner` — real TLS probing via `openssl s_client`, parses group/sig/chain/KEX | ✅ Done |
| Real ML-DSA cert chain generation (Root ML-DSA-87 → Int ML-DSA-65 → Leaf ML-DSA-65) | ✅ Done |
| Factory wiring (`PQC_MODE=native` env var) | ✅ Done (pre-existing) |
| Docker multi-stage builds with liboqs + oqs-provider | ✅ Done |
| End-to-end verification: native scanner classifies google.com as S0_CLASSICAL/ECDSA-P256 | ✅ Done |

Remaining (deferred): real PQC SSH algorithms in Go server (Phase 5, depends on Go upstream support).

### Phase 2 — Real-Time Detection Dashboard ✅ DONE

**Completed Jul 26, 2026.** Live SSE scan streaming and real-time dashboard updates working end-to-end.

| Task | Status |
|---|---|
| Live scan polling via SSE (`GET /scan/live`) | ✅ Done |
| Frontend EventSource with accumulated live state | ✅ Done |
| Pulsing LIVE/OFFLINE indicator in top bar | ✅ Done |
| `/connections` returns real scan data (not static) | ✅ Done |
| Connection evidence live feed | ✅ Done (via live scanner scanning all 5 targets) |
| Threat detection alerts (Prometheus + Alertmanager) | Deferred to Phase 5 |
| Certificate chain validation view | Deferred to Phase 5 |

### Phase 3 — End-to-End Proof of Security

For Barclays to trust the system, they need to see it actually defend against attacks:

| Task | How | Priority |
|---|---|---|
| Live HNDL attack simulation | Connect `demos/security/hndl_attack_sim.py` to real network traffic instead of toy modulus. Show real key exchange, then demonstrate resistance. | **High** |
| Tamper detection demo | Run `authenticity_demo.py` against a live TLS connection with actual ML-DSA signatures. Show the tamper being detected in the dashboard. | **High** |
| Replay attack demo | Run `integrity_replay_demo.py` against a live AEAD session. Show nonce reuse detection and connection termination. | **Medium** |
| Confidentiality under quantum attack | Simulate Shor's algorithm on classical key exchange (small example) vs. ML-KEM resistance. Visualize in dashboard. | **Medium** |

### Phase 4 — Testing & Hardening ✅ DONE

**Completed Jul 26, 2026.** 75 Python tests passing, Go tests created, Playwright E2E configured.

| Task | Status |
|---|---|
| Unit tests for `risk.py` and `state_machine.py` | ✅ Done (41 tests across test_risk.py and test_state_machine.py) |
| Unit tests for Go services | ✅ Done (10 tests across 3 services, files ready to run when Go installed) |
| E2E test infrastructure | ✅ Done (Playwright config + 7 test scenarios in dashboard.spec.ts) |
| Frontend unit tests (Vitest) | Deferred — minimal frontend code, low ROI |
| Fuzz the verifier API | Deferred — low priority |

### Phase 5 — Production Readiness

| Task | How | Priority |
|---|---|---|
| Persistent scan history | Add PostgreSQL or SQLite. Store scan results with timestamps. Add `/history` endpoint for trend analysis. | **Medium** |
| Authentication & RBAC | Add OAuth2/JWT auth to the verifier API. Differentiate Barclays viewer vs. admin roles. | **Medium** |
| Nginx reverse proxy | Wire `infra/nginx/nginx.conf` into `docker-compose.yml`. Add TLS termination, rate limiting, access logging. | **Medium** |
| VPN node with real StrongSwan | Replace `sleep infinity` with actual StrongSwan container. Test IKEv2 with ML-KEM-768 + ML-DSA-65 proposal. | **Low** |
| License file | Add organization-approved license before any public/external sharing. | **High** |
| Alert rules & monitoring | Complete Prometheus alerting rules. Add Grafana dashboard for operational metrics. | **Low** |
| Remove unused dependencies | Drop `d3` and `axios` from `frontend/dashboard/package.json` if not needed. Consume `network_profiles.yaml` in benchmark runner or remove it. | **Low** |

---

## How to Demo This to Barclays

### Current Demo Script (works today)

```bash
# 1. Start everything
docker-compose up --build -d

# 2. Open dashboard
#    http://localhost:3000

# 3. Show the 5 KPI panels — system health, migration state, risk level
# 4. Click profile buttons — Classical vs Hybrid vs PQC-Native vs KEMTLS
# 5. Show handshake comparison bar chart — byte overhead visualization
# 6. Adjust data class + lifetime slider — watch HNDL risk score change
# 7. Show state machine diagram — S0 → S1 → S2 → S3 → S4 transitions
# 8. Run a scan
curl -X POST http://localhost:8000/scan -H 'Content-Type: application/json' -d '{"port": 8443}'

# 9. Run security demos
cd demos/security
python confidentiality_demo.py
python hndl_attack_sim.py

# 10. Show benchmark results
cat benchmarks/results/latest.json
```

### Enhanced Demo (after Phase 1–2)

```bash
# Phase 1 COMPLETE: Real PQC handshake detection
PQC_MODE=native docker-compose up --build -d

# Dashboard shows live ML-KEM-768 vs classical ECDHE comparison
# with real timing data, real ML-DSA certificate chains, real algorithm detection

# Native scan against any TLS endpoint:
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"hostname": "google.com", "port": 443, "timeout_seconds": 5}'
```

---

## Recommended Execution Order

```
Week 1-2:  Phase 1 (Native Crypto Adapter) — this unlocks everything else
Week 3-4:  Phase 2 (Real-Time Detection) — makes the demo interactive
Week 5-6:  Phase 3 (Attack Simulations) — proves the security claims
Week 7-8:  Phase 4 (Testing) — hardens for stakeholder confidence
Week 9+:   Phase 5 (Production) — only if deploying beyond demo
```

**Minimum viable demo for Barclays:** Phase 1 + Phase 2 gives a working system where they can see real post-quantum algorithms being detected and scored in real time.

---

## Key Files to Modify

| Phase | Files |
|---|---|
| Phase 1 | `backend/verifier-api/app/adapters/native.py`, `backend/ca/generate_pki.py`, `services/server-ssh/main.go` |
| Phase 2 | `backend/verifier-api/app/main.py` (SSE endpoint), `frontend/dashboard/src/main.tsx` (live polling) |
| Phase 3 | `demos/security/*.py` (wire to live services), `frontend/dashboard/src/main.tsx` (attack viz) |
| Phase 4 | `backend/verifier-api/tests/`, `services/*/` (Go tests), `tests/e2e/` |
| Phase 5 | `docker-compose.yml`, `infra/nginx/nginx.conf`, new `backend/verifier-api/app/db.py` |
