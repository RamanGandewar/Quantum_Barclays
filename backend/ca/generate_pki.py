import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def name(common_name: str) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PQC Migration Demo"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def cert_builder(
    subject: x509.Name, issuer: x509.Name, public_key, serial: int, days: int
) -> x509.CertificateBuilder:
    now = datetime.now(timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(serial)
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=days))
    )


def create_classical_chain(output: Path) -> dict[str, int]:
    root_key = ec.generate_private_key(ec.SECP256R1())
    int_key = ec.generate_private_key(ec.SECP256R1())
    leaf_key = ec.generate_private_key(ec.SECP256R1())

    root_subject = name("Demo Classical Root CA")
    int_subject = name("Demo Classical Intermediate CA")
    leaf_subject = name("pqc-demo.local")

    root_cert = (
        cert_builder(root_subject, root_subject, root_key.public_key(), 1001, 365 * 20)
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .add_extension(
            x509.KeyUsage(True, True, False, False, False, False, False, False, False),
            critical=True,
        )
        .sign(root_key, hashes.SHA256())
    )
    int_cert = (
        cert_builder(int_subject, root_subject, int_key.public_key(), 1002, 365 * 10)
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(True, True, False, False, False, False, False, False, False),
            critical=True,
        )
        .sign(root_key, hashes.SHA256())
    )
    leaf_cert = (
        cert_builder(leaf_subject, int_subject, leaf_key.public_key(), 1003, 825)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("pqc-demo.local"), x509.DNSName("localhost")]
            ),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(int_key, hashes.SHA256())
    )

    files = {
        "classical_root_ca.crt": root_cert.public_bytes(serialization.Encoding.PEM),
        "classical_intermediate_ca.crt": int_cert.public_bytes(
            serialization.Encoding.PEM
        ),
        "classical_server.crt": leaf_cert.public_bytes(serialization.Encoding.PEM),
        "classical_server.key": leaf_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    }
    for filename, data in files.items():
        write(output / filename, data)
    write(
        output / "classical_server_chain.crt",
        files["classical_server.crt"]
        + files["classical_intermediate_ca.crt"]
        + files["classical_root_ca.crt"],
    )
    return {filename: len(data) for filename, data in files.items()}


def create_pqc_manifest(output: Path, classical_sizes: dict[str, int]) -> None:
    # Placeholder metadata for native liboqs/oqs-provider generation.
    manifest = {
        "mode": "oqs-ready-manifest",
        "root": {"algorithm": "ML-DSA-87", "expected_size_bytes": 7000},
        "intermediate": {"algorithm": "ML-DSA-65", "expected_size_bytes": 5000},
        "leaf_tls": {"algorithm": "ML-DSA-65", "expected_size_bytes": 5000},
        "leaf_kemtls": {"algorithm": "ML-KEM-768", "expected_size_bytes": 4000},
        "classical_sizes": classical_sizes,
        "instructions": [
            "Install OpenSSL 3.3+, liboqs, and oqs-provider.",
            "Use openssl req/x509 with oqs-provider algorithms to create real ML-DSA chains.",
            "Replace this manifest with generated PEM material in production mode.",
        ],
    }
    write(
        output / "pqc_ca_manifest.json", json.dumps(manifest, indent=2).encode("utf-8")
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate demo CA material and PQC CA manifest."
    )
    parser.add_argument("--output", default="certs")
    args = parser.parse_args()
    output = Path(args.output)
    sizes = create_classical_chain(output)
    create_pqc_manifest(output, sizes)
    print(json.dumps({"output": str(output), "classical_sizes": sizes}, indent=2))


if __name__ == "__main__":
    main()
