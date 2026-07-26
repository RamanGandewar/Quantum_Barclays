import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response, StreamingResponse

from app.live import LIVE_SCANNER
from app.models import (
    MigrationPlanRequest,
    MigrationPlanResponse,
    RiskScoreRequest,
    RiskScoreResponse,
    ScanRequest,
    ScanResponse,
    TransitionVerificationRequest,
    TransitionVerificationResponse,
)
from app.risk import compute_risk
from app.scanner import scan_endpoint
from app.state_machine import STATE_LABELS, migration_plan, verify_transition
from app.telemetry import (
    CERTIFICATE_CHAIN,
    HANDSHAKE_COMPARISON,
    STATE_MACHINE_DEFINITION,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    LIVE_SCANNER.start()
    yield
    LIVE_SCANNER.stop()


app = FastAPI(
    title="PQC Migration Verifier API",
    version="1.0.0",
    description="SMSM state detection and HNDL risk scoring for PQC migration.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCAN_COUNTER = Counter("pqc_scans_total", "Total endpoint scans")
RISK_COUNTER = Counter("pqc_risk_scores_total", "Total risk score computations")
SCAN_LATENCY = Histogram("pqc_scan_latency_seconds", "Endpoint scan latency")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/handshake-comparison")
def handshake_comparison() -> list[dict]:
    return HANDSHAKE_COMPARISON


@app.get("/certificates")
def certificates() -> dict:
    return CERTIFICATE_CHAIN


@app.get("/connections")
def connections() -> list[dict]:
    live = LIVE_SCANNER.latest_connections
    return live if live else []


@app.get("/scan/live")
async def scan_live():
    queue = LIVE_SCANNER.subscribe()
    uid = LIVE_SCANNER._counter

    async def event_stream():
        try:
            while True:
                data = await queue.get()
                yield f"event: scan\ndata: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            LIVE_SCANNER.unsubscribe(uid)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/state-machine")
def state_machine() -> dict:
    return STATE_MACHINE_DEFINITION


@app.post("/scan", response_model=ScanResponse)
def scan(request: ScanRequest) -> ScanResponse:
    SCAN_COUNTER.inc()
    with SCAN_LATENCY.time():
        result = scan_endpoint(request)
    return ScanResponse(
        endpoint=result["endpoint"],
        state=result["state"],
        state_label=STATE_LABELS[result["state"]],
        evidence=result["evidence"],
        recommendations=result["recommendations"],
    )


@app.post("/risk-score", response_model=RiskScoreResponse)
def risk_score(request: RiskScoreRequest) -> RiskScoreResponse:
    RISK_COUNTER.inc()
    result = compute_risk(
        state=request.state,
        data_class=request.data_class,
        lifetime_years=request.lifetime_years,
        current_year=request.current_year,
    )
    return RiskScoreResponse(
        state=request.state,
        data_class=request.data_class,
        lifetime_years=request.lifetime_years,
        **result,
    )


@app.post("/migration-plan", response_model=MigrationPlanResponse)
def plan(request: MigrationPlanRequest) -> MigrationPlanResponse:
    result = migration_plan(request.current_state, request.target_state)
    return MigrationPlanResponse(current_state=request.current_state, **result)


@app.post("/verify-transition", response_model=TransitionVerificationResponse)
def transition(
    request: TransitionVerificationRequest,
) -> TransitionVerificationResponse:
    allowed, missing = verify_transition(
        request.current_state, request.target_state, request.evidence
    )
    plan_data = migration_plan(request.current_state, request.target_state)
    return TransitionVerificationResponse(
        allowed=allowed,
        missing_preconditions=missing,
        verification_criteria=plan_data["verification_criteria"],
    )


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
