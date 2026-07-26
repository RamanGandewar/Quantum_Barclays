# Progress Log — Quantum-Secure Communication System

> Maintained by the team to track what's done, who did it, and when.
> One entry per completed task/phase.

---

## Completed

| # | What | Who | When | Notes |
|---|------|-----|------|-------|
| 1 | **Phase 0 — Demo Mode (v0.1.0)** | Team (pre-existing) | Before Jul 2026 | Full working demo: 10 API endpoints, React dashboard, 4 Go services, security demos, benchmarks, Docker Compose, CI pipeline. All telemetry is deterministic/simulated. |
| 2 | **Roadmap + Progress tracking created** | Prajwal + AI | Jul 26, 2026 | ROADMAP.md finalized, PROGRESS.md created. Starting Phase 1. |
| 3 | **Phase 1 Step 1 — Native crypto deps installed (WSL)** | Prajwal + AI | Jul 26, 2026 | liboqs (ML-KEM+ML-DSA), oqs-provider 0.12.0-dev, OpenSSL OQS config, liboqs-python, ML-DSA cert generation verified. All in WSL Ubuntu at /home/pb/oqs-install/. |
| 4 | **Phase 1 Step 2 — NativeScanner implemented** | Prajwal + AI | Jul 26, 2026 | Replaced all NotImplementedError stubs with real TLS probing via openssl s_client. Parses negotiated group, sig algorithm, cert chain, KEX details. Classifies endpoints into SMSM states. Tested: correct X25519/ECDSA/S0_CLASSICAL detection against local TLS server. Added cryptography dep. |
| 5 | **Phase 1 Step 3 — Real ML-DSA certificate chain** | Prajwal + AI | Jul 26, 2026 | Root CA (ML-DSA-87, 10KB) -> Intermediate (ML-DSA-65, 9.6KB) -> Leaf (ML-DSA-65, 7.7KB). Full PQC chain: 27.6KB vs classical 2.2KB. Chain verification passes via openssl verify. Updated generate_pki.py with OQS provider integration. |
| 6 | **Phase 1 Step 4 — Docker images built & tested** | Prajwal + AI | Jul 26, 2026 | Both Dockerfiles updated with multi-stage liboqs + oqs-provider builds. CA Dockerfile fixed: was copying static liboqs.a instead of shared liboqs.so; added OQS_PROVIDER_AVAILABLE env var. CA image generates real ML-DSA cert chain (Root 10KB, Int 9.5KB, Leaf 7.8KB). Verifier-api image verified: env shows OQS_PROVIDER_AVAILABLE=true, PQC_MODE=native. |
| 7 | **Phase 1 — End-to-end native PQC verified** | Prajwal + AI | Jul 26, 2026 | docker-compose up --build verifier-api: NativeScanner loaded ("Selected NativeScanner adapter"). POST /scan against google.com:443 returned S0_CLASSICAL/ECDSA-P256 with scanner_mode=native-openssl-oqs. Real OpenSSL TLS negotiation, cert parsing, and state classification working. |
| 8 | **Phase 2 Step 1 — SSE live scan endpoint** | Prajwal + AI | Jul 26, 2026 | New app/live.py: LiveScanner singleton with background asyncio loop scanning 5 targets every 10s. Per-client asyncio.Queue for SSE broadcast. GET /scan/live streams event:scan\ndata:{json} via StreamingResponse. Lifespan context manager starts/stops scanner on app lifecycle. |
| 9 | **Phase 2 Step 2 — Frontend live EventSource** | Prajwal + AI | Jul 26, 2026 | main.tsx: EventSource connects to /scan/live, liveConnections state accumulates results by endpoint key. Live Connection Evidence table now shows real-time scan data. Pulsing green "LIVE" / red "OFFLINE" indicator in topbar. CSS pulse animation. Removed unused LiveConnection type, static LIVE_CONNECTIONS fallback. |
| 10 | **Phase 4 Step 1 — Backend unit tests (75 tests)** | Prajwal + AI | Jul 26, 2026 | Added test_risk.py (18 tests: crqc_probability, risk_band, recommended_action, compute_risk edge cases), test_state_machine.py (23 tests: classify_evidence, next_state, build_recommendations, migration_plan, verify_transition, data integrity), test_live.py (10 tests: parse_targets, subscribe/unsubscribe, broadcast). All 75 tests passing. |
| 11 | **Phase 4 Step 2 — Go unit tests** | Prajwal + AI | Jul 26, 2026 | Added main_test.go for server-pqc (4 tests: handler response, 404, content-type, profile fields), server-ssh (4 tests: mode profiles, JSON serialization, telemetry endpoint, SSH config), server-kemtls (2 tests: session-info, handshake bytes). Go not installed on host — tests created and ready to run. |
| 12 | **Phase 4 Step 3 — Playwright E2E config + tests** | Prajwal + AI | Jul 26, 2026 | Created tests/e2e/package.json, playwright.config.ts, expanded dashboard.spec.ts to 7 tests (PRD views, toolbar buttons, KPI panels, risk controls, live indicator, state machine SVG, API docs). |
| 13 | **Phase 5 Step 1 — SQLite scan history** | Prajwal + AI | Jul 27, 2026 | New app/db.py: SQLite persistence for scan results with timestamps, auto-trim to 5000 rows, lazy-init. GET /history endpoint returns scans + stats (total_scans, tracked_endpoints, latest_scan). LiveScanner stores every scan to DB after broadcast. Docker volume mount for persistence. 76 tests passing. |
| 14 | **Phase 5 Step 2 — Nginx reverse proxy** | Prajwal + AI | Jul 27, 2026 | Updated infra/nginx/nginx.conf: /api/ proxy to verifier-api, SSE support (proxy_buffering off), gzip compression, try_files SPA fallback. Added nginx service to docker-compose.yml on port 80. |
| 15 | **Phase 5 Step 3 — Frontend dependency cleanup** | Prajwal + AI | Jul 27, 2026 | Removed unused d3, axios, @types/d3 from frontend/dashboard/package.json (3 deps, ~150KB). Confirmed no imports in codebase. |
| 16 | **Phase 5 Step 4 — MIT License** | Prajwal + AI | Jul 27, 2026 | Added MIT license file at project root. |
| 17 | **Phase 5 Step 5 — Simple API key auth** | Prajwal + AI | Jul 27, 2026 | New app/deps.py with verify_api_key dependency. Optional API_KEY env var gates mutating POST endpoints (/scan, /risk-score, /migration-plan, /verify-transition). GET endpoints stay open. Bypassed when API_KEY unset for demo friendliness. 76 tests passing. |
| 18 | **Phase 5 Step 6 — Prometheus alert rules** | Prajwal + AI | Jul 27, 2026 | New infra/prometheus/alerts.yml: 4 rules — VerifierAPIDown (critical, 30s), HighScanFailureRate (warning, 5m), HighScanLatency p95>10s (warning, 5m), MetricsCollectorDown (warning, 1m). Mounted in docker-compose. |

---

## Upcoming

| Phase | Status |
|-------|--------|
| Phase 1 — Native PQC Crypto | ✅ Done |
| Phase 2 — Real-Time Detection | ✅ Done |
| Phase 3 — Attack Demos | ⏸️ Deferred (standalone scripts, wiring to live TLS requires major effort) |
| Phase 4 — Testing & Hardening | ✅ Done (76 Python tests, Go tests, Playwright E2E) |
| Phase 5 — Production Readiness | ✅ Done (history, Nginx, auth, alerts, license, cleanup) |

---

*Format for new entries:*
```
| # | <task description> | <name> | <YYYY-MM-DD HH:MM> | <notes> |
```
