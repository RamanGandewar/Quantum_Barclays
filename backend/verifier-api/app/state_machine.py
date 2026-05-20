from app.models import Evidence, MigrationState

STATE_LABELS = {
    MigrationState.S0_CLASSICAL: "Classical",
    MigrationState.S1_PQC_READY: "PQC Ready",
    MigrationState.S2_HYBRID_KX: "Hybrid Key Exchange",
    MigrationState.S3_HYBRID_FULL: "Hybrid Full",
    MigrationState.S4_PQC_NATIVE: "PQC Native",
}

QUANTUM_SECURITY_LEVEL = {
    MigrationState.S0_CLASSICAL: 0.0,
    MigrationState.S1_PQC_READY: 0.0,
    MigrationState.S2_HYBRID_KX: 0.3,
    MigrationState.S3_HYBRID_FULL: 0.8,
    MigrationState.S4_PQC_NATIVE: 1.0,
}

ORDERED_STATES = [
    MigrationState.S0_CLASSICAL,
    MigrationState.S1_PQC_READY,
    MigrationState.S2_HYBRID_KX,
    MigrationState.S3_HYBRID_FULL,
    MigrationState.S4_PQC_NATIVE,
]

PRECONDITIONS = {
    MigrationState.S1_PQC_READY: [
        "OpenSSL 3.x, liboqs, and oqs-provider installed",
        "PQC algorithms listed by the local crypto provider",
        "Rollback to classical TLS verified",
    ],
    MigrationState.S2_HYBRID_KX: [
        "Hybrid X25519MLKEM768 key exchange enabled",
        "Classical certificate chain remains valid",
        "Handshake telemetry confirms hybrid key share",
    ],
    MigrationState.S3_HYBRID_FULL: [
        "Hybrid or PQC certificate chain issued",
        "ML-DSA certificate signatures verify successfully",
        "Clients validate the chain without policy override",
    ],
    MigrationState.S4_PQC_NATIVE: [
        "ML-KEM key exchange enabled without classical fallback",
        "ML-DSA certificate chain deployed",
        "Legacy client exception list approved",
    ],
}

ROLLBACK_CONDITIONS = [
    "Client compatibility failure exceeds configured threshold",
    "Handshake error rate increases above service SLO",
    "Certificate validation failure detected in production telemetry",
]

VERIFICATION_CRITERIA = {
    MigrationState.S1_PQC_READY: [
        "Provider lists ML-KEM-512, ML-KEM-768, ML-KEM-1024",
        "Provider lists ML-DSA-44, ML-DSA-65, ML-DSA-87",
    ],
    MigrationState.S2_HYBRID_KX: [
        "Negotiated group is X25519MLKEM768",
        "Certificate chain is classical or hybrid",
    ],
    MigrationState.S3_HYBRID_FULL: [
        "Negotiated group is X25519MLKEM768",
        "Certificate algorithm contains ML-DSA",
    ],
    MigrationState.S4_PQC_NATIVE: [
        "Negotiated group is ML-KEM-768",
        "Certificate algorithm contains ML-DSA",
        "No classical fallback was negotiated",
    ],
}


def classify_evidence(evidence: Evidence) -> MigrationState:
    group = evidence.negotiated_group.lower()
    cert = evidence.certificate_algorithm.lower()

    has_mlkem = "ml-kem" in group or "mlkem" in group
    has_hybrid = "x25519" in group and has_mlkem
    has_mldsa_cert = "ml-dsa" in cert or "mldsa" in cert
    has_classical_group = group in {"x25519", "secp256r1", "p-256"}

    if has_mlkem and not has_hybrid and has_mldsa_cert:
        return MigrationState.S4_PQC_NATIVE
    if has_hybrid and has_mldsa_cert:
        return MigrationState.S3_HYBRID_FULL
    if has_hybrid:
        return MigrationState.S2_HYBRID_KX
    if evidence.pqc_library_detected and has_classical_group:
        return MigrationState.S1_PQC_READY
    return MigrationState.S0_CLASSICAL


def next_state(current: MigrationState) -> MigrationState | None:
    index = ORDERED_STATES.index(current)
    if index == len(ORDERED_STATES) - 1:
        return None
    return ORDERED_STATES[index + 1]


def build_recommendations(state: MigrationState) -> list[str]:
    if state == MigrationState.S4_PQC_NATIVE:
        return ["Maintain PQC-native posture and monitor client compatibility."]
    planned = next_state(state)
    if planned is None:
        return []
    return [
        f"Advance to {STATE_LABELS[planned]} after passing transition gates.",
        "Prioritize channels carrying long-lived confidential or regulated data.",
    ]


def migration_plan(
    current: MigrationState, target: MigrationState | None = None
) -> dict:
    planned = target or next_state(current) or current
    immediate = next_state(current)
    return {
        "target_state": planned,
        "next_state": immediate,
        "preconditions": PRECONDITIONS.get(planned, []),
        "rollback_conditions": ROLLBACK_CONDITIONS,
        "verification_criteria": VERIFICATION_CRITERIA.get(planned, []),
    }


def verify_transition(
    current: MigrationState, target: MigrationState, evidence: dict
) -> tuple[bool, list[str]]:
    current_index = ORDERED_STATES.index(current)
    target_index = ORDERED_STATES.index(target)
    if target_index <= current_index:
        return True, []

    missing: list[str] = []
    if target_index > current_index + 1:
        missing.append("Transitions must pass through each intermediate SMSM state.")

    if target in {MigrationState.S2_HYBRID_KX, MigrationState.S3_HYBRID_FULL}:
        group = str(evidence.get("negotiated_group", "")).lower()
        if "x25519" not in group or ("ml-kem" not in group and "mlkem" not in group):
            missing.append("Hybrid X25519MLKEM768 negotiation evidence is required.")

    if target in {MigrationState.S3_HYBRID_FULL, MigrationState.S4_PQC_NATIVE}:
        cert = str(evidence.get("certificate_algorithm", "")).lower()
        if "ml-dsa" not in cert and "mldsa" not in cert:
            missing.append("ML-DSA certificate evidence is required.")

    if target == MigrationState.S4_PQC_NATIVE:
        group = str(evidence.get("negotiated_group", "")).lower()
        if "x25519" in group or ("ml-kem" not in group and "mlkem" not in group):
            missing.append("Pure ML-KEM negotiation evidence is required.")

    return not missing, missing
