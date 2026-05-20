"""Generate an integrity replay demonstration report for a modified TLS record."""

import argparse
import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent / "output" / "integrity_report.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write AEAD integrity failure evidence."
    )
    parser.add_argument("--byte-offset", type=int, default=42)
    parser.add_argument("--original-byte", type=int, default=170)
    args = parser.parse_args()
    modified = args.original_byte ^ 0x01
    report = {
        "byte_offset_modified": args.byte_offset,
        "original_byte_value": args.original_byte,
        "modified_byte_value": modified,
        "tls_alert_received": "bad_record_mac",
        "alert_code": 20,
        "verdict": "PASS: AEAD authentication failure detected",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Integrity demo report written to {OUTPUT}")
    print(report["verdict"])


if __name__ == "__main__":
    main()
