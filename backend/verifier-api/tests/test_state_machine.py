"""Unit tests for app.state_machine module."""

from app.models import Evidence, MigrationState
from app.state_machine import (
    ORDERED_STATES,
    PRECONDITIONS,
    QUANTUM_SECURITY_LEVEL,
    ROLLBACK_CONDITIONS,
    STATE_LABELS,
    VERIFICATION_CRITERIA,
    build_recommendations,
    classify_evidence,
    migration_plan,
    next_state,
    verify_transition,
)


def _evidence(group: str, cert: str, pqc: bool = False) -> Evidence:
    return Evidence(
        negotiated_group=group,
        certificate_algorithm=cert,
        certificate_chain_bytes=1000,
        handshake_bytes=5000,
        latency_ms=20.0,
        pqc_library_detected=pqc,
    )


class TestClassifyEvidence:
    def test_s0_classical(self):
        e = _evidence("x25519", "ECDSA-P256")
        assert classify_evidence(e) == MigrationState.S0_CLASSICAL

    def test_s1_pqc_ready(self):
        e = _evidence("x25519", "ECDSA-P256", pqc=True)
        assert classify_evidence(e) == MigrationState.S1_PQC_READY

    def test_s2_hybrid_kx(self):
        e = _evidence("X25519MLKEM768", "ECDSA-P256")
        assert classify_evidence(e) == MigrationState.S2_HYBRID_KX

    def test_s3_hybrid_full(self):
        e = _evidence("X25519MLKEM768", "ML-DSA-65")
        assert classify_evidence(e) == MigrationState.S3_HYBRID_FULL

    def test_s4_pqc_native(self):
        e = _evidence("ML-KEM-768", "ML-DSA-65")
        assert classify_evidence(e) == MigrationState.S4_PQC_NATIVE

    def test_s4_case_insensitive(self):
        e = _evidence("ml-kem-768", "mldsa65")
        assert classify_evidence(e) == MigrationState.S4_PQC_NATIVE

    def test_s3_case_insensitive(self):
        e = _evidence("x25519mlkem768", "ML-DSA-87")
        assert classify_evidence(e) == MigrationState.S3_HYBRID_FULL

    def test_hybrid_without_mldsa_is_s2(self):
        e = _evidence("X25519MLKEM768", "RSA-PSS-SHA256")
        assert classify_evidence(e) == MigrationState.S2_HYBRID_KX

    def test_unknown_group_is_s0(self):
        e = _evidence("unknown", "unknown")
        assert classify_evidence(e) == MigrationState.S0_CLASSICAL

    def test_ml_kem_without_mldsa_is_s0(self):
        e = _evidence("ml-kem-768", "ECDSA-P256")
        assert classify_evidence(e) == MigrationState.S0_CLASSICAL


class TestNextState:
    def test_s0_to_s1(self):
        assert next_state(MigrationState.S0_CLASSICAL) == MigrationState.S1_PQC_READY

    def test_s3_to_s4(self):
        assert next_state(MigrationState.S3_HYBRID_FULL) == MigrationState.S4_PQC_NATIVE

    def test_s4_is_terminal(self):
        assert next_state(MigrationState.S4_PQC_NATIVE) is None

    def test_sequential_chain(self):
        for i in range(len(ORDERED_STATES) - 1):
            assert next_state(ORDERED_STATES[i]) == ORDERED_STATES[i + 1]


class TestBuildRecommendations:
    def test_s4_maintains(self):
        recs = build_recommendations(MigrationState.S4_PQC_NATIVE)
        assert len(recs) == 1
        assert "Maintain" in recs[0]

    def test_s0_advances_to_s1(self):
        recs = build_recommendations(MigrationState.S0_CLASSICAL)
        assert len(recs) == 2
        assert "PQC Ready" in recs[0]

    def test_s3_advances_to_s4(self):
        recs = build_recommendations(MigrationState.S3_HYBRID_FULL)
        assert "PQC Native" in recs[0]

    def test_all_states_have_recommendations(self):
        for state in ORDERED_STATES:
            recs = build_recommendations(state)
            assert isinstance(recs, list)
            assert len(recs) >= 1


class TestMigrationPlan:
    def test_default_target_is_next(self):
        plan = migration_plan(MigrationState.S0_CLASSICAL)
        assert plan["target_state"] == MigrationState.S1_PQC_READY
        assert plan["next_state"] == MigrationState.S1_PQC_READY

    def test_explicit_target(self):
        plan = migration_plan(
            MigrationState.S0_CLASSICAL, MigrationState.S3_HYBRID_FULL
        )
        assert plan["target_state"] == MigrationState.S3_HYBRID_FULL

    def test_s4_has_no_next(self):
        plan = migration_plan(MigrationState.S4_PQC_NATIVE)
        assert plan["next_state"] is None

    def test_has_preconditions(self):
        plan = migration_plan(MigrationState.S0_CLASSICAL)
        assert isinstance(plan["preconditions"], list)

    def test_has_rollback_conditions(self):
        plan = migration_plan(MigrationState.S0_CLASSICAL)
        assert plan["rollback_conditions"] == ROLLBACK_CONDITIONS

    def test_has_verification_criteria(self):
        plan = migration_plan(MigrationState.S0_CLASSICAL)
        assert isinstance(plan["verification_criteria"], list)


class TestVerifyTransition:
    def test_same_state_always_allowed(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S0_CLASSICAL,
            {},
        )
        assert allowed is True
        assert missing == []

    def test_backward_transition_allowed(self):
        allowed, missing = verify_transition(
            MigrationState.S3_HYBRID_FULL,
            MigrationState.S0_CLASSICAL,
            {},
        )
        assert allowed is True

    def test_skip_states_blocked(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S4_PQC_NATIVE,
            {
                "negotiated_group": "ML-KEM-768",
                "certificate_algorithm": "ML-DSA-65",
            },
        )
        assert allowed is False
        assert any("intermediate" in m.lower() for m in missing)

    def test_s0_to_s2_requires_hybrid_evidence(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S2_HYBRID_KX,
            {},
        )
        assert allowed is False
        assert any("hybrid" in m.lower() or "x25519" in m.lower() for m in missing)

    def test_s0_to_s2_blocked_skips_s1(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S2_HYBRID_KX,
            {"negotiated_group": "X25519MLKEM768"},
        )
        assert allowed is False
        assert any("intermediate" in m.lower() for m in missing)

    def test_s1_to_s2_with_hybrid_evidence(self):
        allowed, missing = verify_transition(
            MigrationState.S1_PQC_READY,
            MigrationState.S2_HYBRID_KX,
            {"negotiated_group": "X25519MLKEM768"},
        )
        assert allowed is True

    def test_s0_to_s3_requires_mldsa(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S3_HYBRID_FULL,
            {"negotiated_group": "X25519MLKEM768"},
        )
        assert allowed is False
        assert any("ml-dsa" in m.lower() for m in missing)

    def test_s0_to_s4_requires_pure_mlkem(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S4_PQC_NATIVE,
            {
                "negotiated_group": "X25519MLKEM768",
                "certificate_algorithm": "ML-DSA-65",
            },
        )
        assert allowed is False
        assert any("pure" in m.lower() or "ml-kem" in m.lower() for m in missing)

    def test_s0_to_s4_blocked_skips_intermediates(self):
        allowed, missing = verify_transition(
            MigrationState.S0_CLASSICAL,
            MigrationState.S4_PQC_NATIVE,
            {
                "negotiated_group": "ML-KEM-768",
                "certificate_algorithm": "ML-DSA-65",
            },
        )
        assert allowed is False
        assert any("intermediate" in m.lower() for m in missing)

    def test_s3_to_s4_with_complete_evidence(self):
        allowed, missing = verify_transition(
            MigrationState.S3_HYBRID_FULL,
            MigrationState.S4_PQC_NATIVE,
            {
                "negotiated_group": "ML-KEM-768",
                "certificate_algorithm": "ML-DSA-65",
            },
        )
        assert allowed is True
        assert missing == []


class TestDataIntegrity:
    def test_all_states_have_labels(self):
        for state in MigrationState:
            assert state in STATE_LABELS

    def test_all_states_have_quantum_security(self):
        for state in MigrationState:
            assert state in QUANTUM_SECURITY_LEVEL
            assert 0.0 <= QUANTUM_SECURITY_LEVEL[state] <= 1.0

    def test_quantum_security_increases_monotonically(self):
        levels = [QUANTUM_SECURITY_LEVEL[s] for s in ORDERED_STATES]
        for i in range(len(levels) - 1):
            assert levels[i] <= levels[i + 1]

    def test_s1_through_s4_have_preconditions(self):
        for state in list(MigrationState)[1:]:
            assert state in PRECONDITIONS
            assert len(PRECONDITIONS[state]) > 0

    def test_s1_through_s4_have_verification_criteria(self):
        for state in list(MigrationState)[1:]:
            assert state in VERIFICATION_CRITERIA
            assert len(VERIFICATION_CRITERIA[state]) > 0

    def test_rollback_conditions_nonempty(self):
        assert len(ROLLBACK_CONDITIONS) > 0
