# Research Notes

## Formal SMSM Definition

The Structured Migration State Machine is a tuple:

```text
SMSM = (S, s0, A, T, E, V)
```

Where:

- `S = {S0, S1, S2, S3, S4}` is the finite set of migration states.
- `s0 = S0_CLASSICAL` is the initial state for legacy systems.
- `A` is the set of cryptographic algorithms observed on a channel.
- `T` is the allowed transition relation.
- `E` is the endpoint evidence collected by scanners.
- `V` is the verification predicate for transition gates.

State definitions:

| State | Description | Quantum Security Level |
| --- | --- | --- |
| `S0_CLASSICAL` | RSA/ECDH/ECDSA only | `0.0` |
| `S1_PQC_READY` | PQC providers installed but no PQC negotiated | `0.0` |
| `S2_HYBRID_KX` | Hybrid key exchange with classical certificates | `0.3` |
| `S3_HYBRID_FULL` | Hybrid key exchange with PQC/hybrid certificates | `0.8` |
| `S4_PQC_NATIVE` | PQC-native key exchange and authentication | `1.0` |

Allowed transitions:

```text
S0 -> S1 -> S2 -> S3 -> S4
```

Each transition has preconditions, rollback conditions, and verification criteria encoded in `backend/verifier-api/app/state_machine.py`.

## HNDL Risk Model

The HNDL risk score for data class `D` on channel `C` at time `T` is:

```text
R(D, C, T) = P(CRQC by T + L_D) * (1 - Q_C) * V_D
```

Definitions:

- `L_D`: confidentiality lifetime of data class `D`.
- `Q_C`: quantum-security level of channel state `C`.
- `V_D`: data value multiplier.
- `P(CRQC by T + L_D)`: probability that a cryptographically relevant quantum computer exists before the data expires.

The implementation uses a logistic CRQC arrival distribution:

```text
P(y) = 1 / (1 + e^(-(y - median_year) / spread_years))
```

This lets an operator tune `CRQC_MEDIAN_YEAR` and `CRQC_SPREAD_YEARS` without changing code.

## Comparison Against Existing Work

| Work | Provides PQC Algorithms | Provides TLS Experiments | Provides Migration Decision Framework | Provides HNDL Scoring |
| --- | --- | --- | --- | --- |
| Open Quantum Safe | Yes | Yes | No | No |
| Cloudflare CIRCL | Yes | Partial | No | No |
| Paquin-Stebila-Tamvada 2020 | Benchmarking | Yes | No | No |
| KEMTLS CCS 2020 | Protocol design | Yes | No | No |
| This project | Adapter-ready | Yes, via telemetry/native boundary | Yes | Yes |

## Gap Analysis

Existing tools answer whether PQC algorithms can run. They do not answer which enterprise channel should migrate first, what state that channel is in, or how long-lived sensitive data changes urgency. SMSM and HNDL scoring fill that operational gap by combining endpoint evidence, state verification, data classification, and time-bounded CRQC probability.

## Publication Venues

- IEEE S&P: suitable for migration-state formalization and evidence-driven security operations.
- ACM CCS: suitable for applied cryptography systems evaluation.
- USENIX Security: suitable for deployable security tooling and operational measurement.
- PQCrypto: suitable for the PQC-specific migration and scoring framework.

The publishable contribution is not a new primitive. It is the operational framework that turns PQC capability into measurable migration decisions.
