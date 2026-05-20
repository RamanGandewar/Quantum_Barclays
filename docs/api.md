# Verifier API

Base URL: `http://localhost:8000`

All JSON errors use FastAPI's standard validation shape:

```json
{
  "detail": [
    {
      "loc": ["body", "field"],
      "msg": "error message",
      "type": "validation_error"
    }
  ]
}
```

Common error codes:

| Code | Meaning |
| --- | --- |
| `200` | Request succeeded |
| `422` | Request schema validation failed |
| `500` | Unexpected server error or native adapter failure |

## `GET /health`

Health check.

Response:

```json
{"status": "ok"}
```

## `POST /scan`

Scans a TLS, KEMTLS, SSH, or demo endpoint and returns SMSM state.

Request:

```json
{
  "hostname": "localhost",
  "port": 8444,
  "timeout_seconds": 2.0
}
```

Response:

```json
{
  "endpoint": "localhost:8444",
  "state": "S3_HYBRID_FULL",
  "state_label": "Hybrid Full",
  "evidence": {
    "negotiated_group": "X25519MLKEM768",
    "certificate_algorithm": "ML-DSA-65",
    "certificate_chain_bytes": 13200,
    "handshake_bytes": 18400,
    "latency_ms": 31.02,
    "pqc_library_detected": true,
    "details": {
      "scanner_mode": "deterministic-demo-adapter",
      "protocol": "tls"
    }
  },
  "recommendations": [
    "Advance to PQC Native after passing transition gates.",
    "Prioritize channels carrying long-lived confidential or regulated data."
  ]
}
```

## `POST /risk-score`

Computes HNDL risk for a state and data class.

Request:

```json
{
  "state": "S3_HYBRID_FULL",
  "data_class": "confidential",
  "lifetime_years": 30,
  "current_year": 2026
}
```

Response:

```json
{
  "state": "S3_HYBRID_FULL",
  "data_class": "confidential",
  "lifetime_years": 30,
  "crqc_probability": 0.973403,
  "quantum_security_level": 0.8,
  "value_multiplier": 5.0,
  "risk_score": 0.973403,
  "risk_band": "low",
  "recommended_action": "Track in migration backlog and re-score when data lifetime changes."
}
```

## `POST /migration-plan`

Returns target state, next state, preconditions, rollback conditions, and verification criteria.

Request:

```json
{
  "current_state": "S2_HYBRID_KX",
  "target_state": "S4_PQC_NATIVE"
}
```

Response:

```json
{
  "current_state": "S2_HYBRID_KX",
  "target_state": "S4_PQC_NATIVE",
  "next_state": "S3_HYBRID_FULL",
  "preconditions": [
    "ML-KEM key exchange enabled without classical fallback",
    "ML-DSA certificate chain deployed",
    "Legacy client exception list approved"
  ],
  "rollback_conditions": [
    "Client compatibility failure exceeds configured threshold"
  ],
  "verification_criteria": [
    "Negotiated group is ML-KEM-768",
    "Certificate algorithm contains ML-DSA",
    "No classical fallback was negotiated"
  ]
}
```

## `POST /verify-transition`

Validates whether evidence satisfies transition rules.

Request:

```json
{
  "current_state": "S2_HYBRID_KX",
  "target_state": "S3_HYBRID_FULL",
  "evidence": {
    "negotiated_group": "X25519MLKEM768",
    "certificate_algorithm": "ML-DSA-65"
  }
}
```

Response:

```json
{
  "allowed": true,
  "missing_preconditions": [],
  "verification_criteria": [
    "Negotiated group is X25519MLKEM768",
    "Certificate algorithm contains ML-DSA"
  ]
}
```

## `GET /handshake-comparison`

Returns comparison data for Classical, Hybrid, PQC-Native, and KEMTLS.

Response:

```json
[
  {
    "profile": "Hybrid",
    "key_exchange": "X25519MLKEM768",
    "client_hello_key_share": 1216,
    "server_hello_key_share": 1120,
    "signature_algorithm": "ML-DSA-65",
    "certificate_verify": 3293,
    "certificate_chain": 13200,
    "total_handshake": 18400,
    "latency_ms": 31
  }
]
```

## `GET /certificates`

Returns the expected CA chain model.

Response:

```json
{
  "root": {
    "common_name": "PQC Demo Root CA",
    "algorithm": "ML-DSA-87",
    "validity_years": 20,
    "expected_size_bytes": 7000
  }
}
```

## `GET /connections`

Returns connection evidence for dashboard tables.

Response:

```json
[
  {
    "endpoint": "localhost:2222",
    "state": "S3_HYBRID_FULL",
    "negotiated_group": "X25519MLKEM768",
    "certificate_algorithm": "ML-DSA-65 host key",
    "handshake_bytes": 4200,
    "latency_ms": 12
  }
]
```

## `GET /state-machine`

Returns SMSM nodes and transitions.

Response:

```json
{
  "states": [
    {"id": "S0_CLASSICAL", "label": "Classical", "quantum_security": 0.0}
  ],
  "transitions": [
    {"from": "S0_CLASSICAL", "to": "S1_PQC_READY"}
  ]
}
```

## `GET /metrics`

Prometheus-compatible metrics.

Response format: `text/plain; version=0.0.4`
