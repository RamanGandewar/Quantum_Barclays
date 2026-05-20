# PRD Traceability Matrix

| Phase / Requirement | Files | Status |
| --- | --- | --- |
| Phase 0: Toolchain and skeleton | `docker-compose.yml`, `.env.example`, `backend/`, `frontend/`, `services/` | Implemented |
| Phase 0: React scaffold | `frontend/dashboard` | Implemented |
| Phase 0: Go workspace | `services/server-pqc`, `services/server-kemtls`, `services/server-ssh`, `services/client-measurement` | Implemented |
| Phase 1: Classical CA comparison chain | `backend/ca/generate_pki.py` | Implemented |
| Phase 1: PQC CA Root/Intermediate/Leaf manifest | `backend/ca/generate_pki.py`, `backend/verifier-api/app/telemetry.py` | Adapter-Ready |
| Phase 1: Native ML-DSA certificate issuance | `backend/ca/generate_pki.py` | Native-Only |
| Phase 2: PQC-TLS server ports 8443/8444/8445 | `services/server-pqc` | Adapter-Ready |
| Phase 2: Handshake telemetry endpoint | `services/server-pqc/main.go`, `/handshake-comparison` | Implemented |
| Phase 2: Measurement client | `services/client-measurement` | Implemented |
| Phase 2: Native CIRCL TLS handshakes | `services/server-pqc` | Native-Only |
| Phase 3: KEMTLS profile and comparison | `services/server-kemtls`, `backend/verifier-api/app/telemetry.py` | Adapter-Ready |
| Phase 3: OQS-Go KEMTLS handshake | `services/server-kemtls` | Native-Only |
| Phase 4: IKEv2/IPsec VPN config | `infra/vpn/swanctl.conf` | Adapter-Ready |
| Phase 4: StrongSwan RFC 9370/9242 tunnel | `infra/vpn/swanctl.conf`, `docker-compose.yml` | Native-Only |
| Phase 5: SMSM state machine | `backend/verifier-api/app/state_machine.py` | Implemented |
| Phase 5: HNDL risk scorer | `backend/verifier-api/app/risk.py` | Implemented |
| Phase 5: Scanner API | `backend/verifier-api/app/main.py`, `backend/verifier-api/app/scanner.py` | Implemented |
| Phase 5: Scanner adapter contract | `backend/verifier-api/app/adapters/base.py` | Implemented |
| Phase 5: Native scanner boundary | `backend/verifier-api/app/adapters/native.py` | Adapter-Ready |
| Phase 6: Confidentiality demo | `demos/security/confidentiality_demo.py` | Implemented |
| Phase 6: Authenticity tamper demo | `demos/security/authenticity_demo.py` | Implemented |
| Phase 6: Integrity replay demo | `demos/security/integrity_replay_demo.py` | Implemented |
| Phase 6: HNDL attack simulation | `demos/security/hndl_attack_sim.py` | Implemented |
| Phase 7: Overview dashboard | `frontend/dashboard/src/main.tsx` | Implemented |
| Phase 7: Risk analysis controls | `frontend/dashboard/src/main.tsx`, `/risk-score` | Implemented |
| Phase 7: Handshake comparison chart | `frontend/dashboard/src/main.tsx`, `/handshake-comparison` | Implemented |
| Phase 7: State machine visualizer | `frontend/dashboard/src/main.tsx`, `/state-machine` | Implemented |
| Phase 7: Certificate chain data | `/certificates`, `backend/verifier-api/app/telemetry.py` | Implemented |
| Phase 7: Live connection evidence | `/connections`, `frontend/dashboard/src/main.tsx` | Implemented |
| Phase 7: SSH migration state | `services/server-ssh`, `/scan` port `2222`, dashboard overview | Implemented |
| Phase 8: Docker Compose deployment | `docker-compose.yml` | Implemented |
| Phase 8: Prometheus config | `infra/prometheus/prometheus.yml`, `backend/metrics` | Implemented |
| Phase 8: CI pipeline | `.github/workflows/ci.yml` | Implemented |
| Documentation: Production README | `README.md` | Implemented |
| Documentation: API contract | `docs/api.md` | Implemented |
| Documentation: Architecture | `docs/architecture.md` | Implemented |
| Documentation: Research notes | `docs/research-notes.md` | Implemented |
| Documentation: Known limitations | `docs/known-limitations.md` | Implemented |
| Documentation: Contribution guide | `CONTRIBUTING.md` | Implemented |

## Native Integration Boundary

Demo mode validates system behavior with deterministic adapters. Native production evidence requires:

- OpenSSL 3.3+, liboqs 0.10+, and oqs-provider 0.6+ for certificate and TLS evidence.
- CIRCL-backed Go TLS for real hybrid key exchange.
- OQS-Go fork for KEMTLS.
- Linux StrongSwan 6.x deployment for RFC 9370/9242 IPsec.
- Finalized PQC SSH standards before claiming production PQC SSH interoperability.
