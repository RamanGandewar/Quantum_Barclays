from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MigrationState(str, Enum):
    S0_CLASSICAL = "S0_CLASSICAL"
    S1_PQC_READY = "S1_PQC_READY"
    S2_HYBRID_KX = "S2_HYBRID_KX"
    S3_HYBRID_FULL = "S3_HYBRID_FULL"
    S4_PQC_NATIVE = "S4_PQC_NATIVE"


class DataClass(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    secret = "secret"
    top_secret = "top-secret"


class ScanRequest(BaseModel):
    hostname: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    timeout_seconds: float = Field(default=2.0, gt=0, le=30)


class Evidence(BaseModel):
    negotiated_group: str
    certificate_algorithm: str
    certificate_chain_bytes: int
    handshake_bytes: int
    latency_ms: float
    pqc_library_detected: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ScanResponse(BaseModel):
    endpoint: str
    state: MigrationState
    state_label: str
    evidence: Evidence
    recommendations: list[str]


class ScanResult(BaseModel):
    endpoint: str
    state: MigrationState
    evidence: Evidence
    recommendations: list[str]


class RiskScoreRequest(BaseModel):
    state: MigrationState
    data_class: DataClass
    lifetime_years: int = Field(..., ge=0, le=100)
    current_year: int | None = None


class RiskScoreResponse(BaseModel):
    state: MigrationState
    data_class: DataClass
    lifetime_years: int
    crqc_probability: float
    quantum_security_level: float
    value_multiplier: float
    risk_score: float
    risk_band: str
    recommended_action: str


class MigrationPlanRequest(BaseModel):
    current_state: MigrationState
    target_state: MigrationState | None = None


class MigrationPlanResponse(BaseModel):
    current_state: MigrationState
    target_state: MigrationState
    next_state: MigrationState | None
    preconditions: list[str]
    rollback_conditions: list[str]
    verification_criteria: list[str]


class TransitionVerificationRequest(BaseModel):
    current_state: MigrationState
    target_state: MigrationState
    evidence: dict[str, Any] = Field(default_factory=dict)


class TransitionVerificationResponse(BaseModel):
    allowed: bool
    missing_preconditions: list[str]
    verification_criteria: list[str]
