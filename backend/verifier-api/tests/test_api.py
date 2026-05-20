from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_scan_classifies_demo_ports():
    expected = {
        8445: "S0_CLASSICAL",
        8444: "S3_HYBRID_FULL",
        8443: "S4_PQC_NATIVE",
    }
    for port, state in expected.items():
        response = client.post("/scan", json={"hostname": "localhost", "port": port})
        assert response.status_code == 200
        assert response.json()["state"] == state


def test_risk_orders_lifetime_and_data_value():
    trade = client.post(
        "/risk-score",
        json={
            "state": "S0_CLASSICAL",
            "data_class": "confidential",
            "lifetime_years": 7,
            "current_year": 2026,
        },
    ).json()
    patient = client.post(
        "/risk-score",
        json={
            "state": "S0_CLASSICAL",
            "data_class": "confidential",
            "lifetime_years": 30,
            "current_year": 2026,
        },
    ).json()
    secret = client.post(
        "/risk-score",
        json={
            "state": "S0_CLASSICAL",
            "data_class": "secret",
            "lifetime_years": 30,
            "current_year": 2026,
        },
    ).json()

    assert patient["risk_score"] > trade["risk_score"]
    assert secret["risk_score"] > patient["risk_score"]


def test_transition_requires_intermediate_states():
    response = client.post(
        "/verify-transition",
        json={
            "current_state": "S0_CLASSICAL",
            "target_state": "S4_PQC_NATIVE",
            "evidence": {
                "negotiated_group": "ML-KEM-768",
                "certificate_algorithm": "ML-DSA-65",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is False


def test_prd_supporting_endpoints_exist():
    for path in [
        "/handshake-comparison",
        "/certificates",
        "/connections",
        "/state-machine",
        "/metrics",
    ]:
        response = client.get(path)
        assert response.status_code == 200
