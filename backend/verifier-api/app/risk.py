import math
import os
from datetime import datetime

from app.models import DataClass, MigrationState
from app.state_machine import QUANTUM_SECURITY_LEVEL

VALUE_MULTIPLIER = {
    DataClass.public: 0.1,
    DataClass.internal: 1.0,
    DataClass.confidential: 5.0,
    DataClass.secret: 25.0,
    DataClass.top_secret: 50.0,
}


def crqc_probability(target_year: int) -> float:
    median = float(os.getenv("CRQC_MEDIAN_YEAR", "2038"))
    spread = float(os.getenv("CRQC_SPREAD_YEARS", "5"))
    exponent = -(target_year - median) / max(spread, 0.1)
    return 1.0 / (1.0 + math.exp(exponent))


def risk_band(score: float) -> str:
    if score >= 10:
        return "critical"
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def recommended_action(band: str, state: MigrationState) -> str:
    if state == MigrationState.S4_PQC_NATIVE:
        return "Maintain PQC-native posture and revalidate cryptographic inventory quarterly."
    if band in {"critical", "high"}:
        return "Prioritize immediate migration to hybrid-full or PQC-native protection."
    if band == "medium":
        return "Schedule migration and monitor CRQC assumptions."
    return "Track in migration backlog and re-score when data lifetime changes."


def compute_risk(
    state: MigrationState,
    data_class: DataClass,
    lifetime_years: int,
    current_year: int | None = None,
) -> dict:
    year = current_year or datetime.utcnow().year
    probability = crqc_probability(year + lifetime_years)
    quantum_security = QUANTUM_SECURITY_LEVEL[state]
    multiplier = VALUE_MULTIPLIER[data_class]
    score = probability * (1.0 - quantum_security) * multiplier
    band = risk_band(score)
    return {
        "crqc_probability": round(probability, 6),
        "quantum_security_level": quantum_security,
        "value_multiplier": multiplier,
        "risk_score": round(score, 6),
        "risk_band": band,
        "recommended_action": recommended_action(band, state),
    }
