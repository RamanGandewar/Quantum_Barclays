# Security Policy

## Scope

This project is a research and demonstration implementation. It is not a production cryptographic library. Do not use demo-mode telemetry as a substitute for real cryptographic implementation.

## Reporting a Vulnerability

If you find a vulnerability in the SMSM logic, HNDL risk model, or any adapter implementation, open a GitHub issue marked with the `security` label. For sensitive disclosures, contact the maintainer directly before public disclosure.

## Native Mode Security Notes

- oqs-provider and liboqs implement NIST FIPS 203/204/205 algorithms. Report vulnerabilities in those libraries to the Open Quantum Safe project directly.
- StrongSwan vulnerabilities should be reported to the StrongSwan security team.
- This project does not implement its own cryptographic primitives.

## Demo Mode Disclaimer

Demo mode uses deterministic adapters. It provides no cryptographic security guarantees. See `docs/known-limitations.md` for the full audit disclaimer.
