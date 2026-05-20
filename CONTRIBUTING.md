# Contributing

## Adding A New Scanner Adapter

1. Create a new file in `backend/verifier-api/app/adapters/`.
2. Implement `BaseScanner` from `base.py`; all four methods are required:
   - `scan(self, hostname: str, port: int)`
   - `get_cert_chain(self, hostname: str, port: int)`
   - `get_kex_info(self, hostname: str, port: int)`
   - `is_available(self)`
3. Register the adapter in `factory.py` with an environment variable trigger.
4. Add unit tests in `backend/verifier-api/tests/` with a mock that does not require native dependencies.
5. Update `docs/prd-traceability.md`.

## Adding A New Migration State

1. Add the state to the `MigrationState` enum in `backend/verifier-api/app/state_machine.py`.
2. Add transition rules: which states can transition to it, what evidence is required, and what the rollback condition is.
3. Add the state to the dashboard `STATE_DEFINITIONS` constant in `frontend/dashboard/src/constants/states.ts`.
4. Add the state node to the D3 state machine diagram in `frontend/dashboard/src/components/StateMachineView.tsx`.
5. Add transition tests covering: valid transition succeeds, invalid transition returns the correct error, and rollback condition triggers correctly.

## Adding A New Data Classification To The HNDL Scorer

1. Add to the `DataClass` enum in `backend/verifier-api/app/risk.py`.
2. Add `V_D` value multiplier to the `VALUE_MULTIPLIERS` dict.
3. Add default `L_D` lifetime in years to the `DEFAULT_LIFETIMES` dict.
4. Add at least one test case in `backend/verifier-api/tests/test_risk.py` verifying the new class scores higher than a lower-sensitivity class.

## Code Style

- Python: `black --check` and `ruff check` must pass.
- Go: `gofmt` and `go vet` must pass.
- TypeScript: `tsc --noEmit` and `prettier --check` must pass.

## PR Checklist

- [ ] All existing tests pass.
- [ ] New code has unit tests.
- [ ] `docs/prd-traceability.md` updated.
- [ ] No native-only code without `# NATIVE-ONLY` comment and graceful fallback.
- [ ] `docker-compose.yml` updated if a new service was added.
- [ ] README updated if a new capability was added.
