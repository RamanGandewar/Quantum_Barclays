from app.models import MigrationState

HANDSHAKE_COMPARISON = [
    {
        "profile": "Classical",
        "key_exchange": "X25519",
        "client_hello_key_share": 32,
        "server_hello_key_share": 32,
        "signature_algorithm": "ECDSA P-256",
        "certificate_verify": 64,
        "certificate_chain": 2600,
        "total_handshake": 5100,
        "latency_ms": 18,
    },
    {
        "profile": "Hybrid",
        "key_exchange": "X25519MLKEM768",
        "client_hello_key_share": 1216,
        "server_hello_key_share": 1120,
        "signature_algorithm": "ML-DSA-65",
        "certificate_verify": 3293,
        "certificate_chain": 13200,
        "total_handshake": 18400,
        "latency_ms": 31,
    },
    {
        "profile": "PQC-Native",
        "key_exchange": "ML-KEM-768",
        "client_hello_key_share": 1184,
        "server_hello_key_share": 1088,
        "signature_algorithm": "ML-DSA-65",
        "certificate_verify": 3293,
        "certificate_chain": 13200,
        "total_handshake": 18100,
        "latency_ms": 34,
    },
    {
        "profile": "KEMTLS",
        "key_exchange": "ML-KEM-768",
        "client_hello_key_share": 1184,
        "server_hello_key_share": 1088,
        "signature_algorithm": "KEM decapsulation",
        "certificate_verify": 0,
        "client_kem_ciphertext": 1088,
        "certificate_chain": 11800,
        "total_handshake": 15800,
        "latency_ms": 39,
    },
]

CERTIFICATE_CHAIN = {
    "root": {
        "common_name": "PQC Demo Root CA",
        "algorithm": "ML-DSA-87",
        "validity_years": 20,
        "expected_size_bytes": 7000,
        "extensions": [
            "BasicConstraints CA:TRUE PathLen:1",
            "KeyUsage keyCertSign,cRLSign",
        ],
    },
    "intermediate": {
        "common_name": "PQC Demo Intermediate CA",
        "algorithm": "ML-DSA-65",
        "validity_years": 10,
        "expected_size_bytes": 5000,
        "extensions": [
            "BasicConstraints CA:TRUE PathLen:0",
            "KeyUsage keyCertSign,cRLSign",
        ],
    },
    "leaf_tls": {
        "common_name": "pqc-demo.local",
        "algorithm": "ML-DSA-65",
        "expected_size_bytes": 5000,
        "san": ["pqc-demo.local", "localhost"],
    },
    "leaf_kemtls": {
        "common_name": "kemtls-demo.local",
        "algorithm": "ML-KEM-768 public key",
        "expected_size_bytes": 4000,
        "san": ["kemtls-demo.local", "localhost"],
    },
}

LIVE_CONNECTIONS = [
    {
        "endpoint": "localhost:8445",
        "state": MigrationState.S0_CLASSICAL,
        "negotiated_group": "X25519",
        "certificate_algorithm": "ECDSA-P256",
        "handshake_bytes": 5100,
        "latency_ms": 18,
    },
    {
        "endpoint": "localhost:8444",
        "state": MigrationState.S3_HYBRID_FULL,
        "negotiated_group": "X25519MLKEM768",
        "certificate_algorithm": "ML-DSA-65",
        "handshake_bytes": 18400,
        "latency_ms": 31,
    },
    {
        "endpoint": "localhost:8443",
        "state": MigrationState.S4_PQC_NATIVE,
        "negotiated_group": "ML-KEM-768",
        "certificate_algorithm": "ML-DSA-65",
        "handshake_bytes": 18100,
        "latency_ms": 34,
    },
    {
        "endpoint": "localhost:8446",
        "state": MigrationState.S4_PQC_NATIVE,
        "negotiated_group": "ML-KEM-768",
        "certificate_algorithm": "ML-KEM-768 leaf authentication",
        "handshake_bytes": 15800,
        "latency_ms": 39,
    },
    {
        "endpoint": "localhost:2222",
        "state": MigrationState.S3_HYBRID_FULL,
        "negotiated_group": "X25519MLKEM768",
        "certificate_algorithm": "ML-DSA-65 host key",
        "handshake_bytes": 4200,
        "latency_ms": 12,
    },
]

STATE_MACHINE_DEFINITION = {
    "states": [
        {"id": "S0_CLASSICAL", "label": "Classical", "quantum_security": 0.0},
        {"id": "S1_PQC_READY", "label": "PQC Ready", "quantum_security": 0.0},
        {"id": "S2_HYBRID_KX", "label": "Hybrid Key Exchange", "quantum_security": 0.3},
        {"id": "S3_HYBRID_FULL", "label": "Hybrid Full", "quantum_security": 0.8},
        {"id": "S4_PQC_NATIVE", "label": "PQC Native", "quantum_security": 1.0},
    ],
    "transitions": [
        {"from": "S0_CLASSICAL", "to": "S1_PQC_READY"},
        {"from": "S1_PQC_READY", "to": "S2_HYBRID_KX"},
        {"from": "S2_HYBRID_KX", "to": "S3_HYBRID_FULL"},
        {"from": "S3_HYBRID_FULL", "to": "S4_PQC_NATIVE"},
    ],
}
