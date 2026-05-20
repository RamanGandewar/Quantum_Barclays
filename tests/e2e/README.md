# E2E Test Plan

Production E2E tests should start the Docker Compose stack, open the dashboard, and verify:

- Overview tab renders current migration state.
- Risk score changes within two seconds after data-class or lifetime input changes.
- State machine highlights the state returned by `/scan`.
- Handshake comparison includes Classical, Hybrid, PQC-Native, and KEMTLS.
- API documentation is reachable at `/docs`.
