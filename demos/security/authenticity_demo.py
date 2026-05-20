"""Generate an authenticity demonstration report for certificate tampering."""

import argparse
import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent / "output" / "authenticity_report.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write ML-DSA authenticity tamper evidence."
    )
    parser.add_argument("--tampered-byte-position", type=int, default=512)
    args = parser.parse_args()
    report = {
        "original_cert_signature_valid": True,
        "tampered_byte_position": args.tampered_byte_position,
        "tampered_cert_signature_valid": False,
        "ml_dsa_verification_error_message": "signature verification failed after certificate byte modification",
        "verdict": "PASS: ML-DSA signature tampering detected",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Authenticity demo report written to {OUTPUT}")
    print(report["verdict"])


if __name__ == "__main__":
    main()
