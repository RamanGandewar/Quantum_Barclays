import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def _find_openssl() -> str:
    custom = os.getenv("OPENSSL_BIN", "")
    if custom and Path(custom).exists():
        return custom
    for candidate in ("/usr/local/bin/openssl", "/home/pb/oqs-install/bin/openssl", "openssl"):
        try:
            subprocess.run([candidate, "version"], capture_output=True, timeout=5, check=True)
            return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            continue
    return "openssl"


def _run_openssl(args: list[str], input_data: bytes = b"") -> subprocess.CompletedProcess:
    openssl = _find_openssl()
    env = os.environ.copy()
    oqs_conf = os.getenv("OPENSSL_CONF", "/home/pb/oqs-install/openssl.cnf")
    if Path(oqs_conf).exists():
        env["OPENSSL_CONF"] = oqs_conf
    ld_path = env.get("LD_LIBRARY_PATH", "")
    for p in ("/home/pb/oqs-install/lib", "/usr/local/lib"):
        if p not in ld_path:
            ld_path = f"{p}:{ld_path}" if ld_path else p
    env["LD_LIBRARY_PATH"] = ld_path
    return subprocess.run(
        [openssl] + args,
        input=input_data,
        capture_output=True,
        timeout=30,
        env=env,
    )


def _oqs_available() -> bool:
    try:
        result = _run_openssl(["list", "-providers"])
        return b"oqs" in result.stdout.lower()
    except Exception:
        return False


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


def create_pqc_chain(output: Path) -> dict[str, int]:
    """Generate real ML-DSA certificate chain using OpenSSL with OQS provider.

    Chain: ML-DSA-87 Root -> ML-DSA-65 Intermediate -> ML-DSA-65 Leaf
    """
    if not _oqs_available():
        print("WARNING: OQS provider not available. Falling back to manifest.")
        return {}

    sizes: dict[str, int] = {}

    root_key_path = output / "pqc_root_ca.key"
    root_cert_path = output / "pqc_root_ca.crt"
    _run_openssl([
        "req", "-x509", "-newkey", "mldsa87",
        "-keyout", str(root_key_path),
        "-out", str(root_cert_path),
        "-days", "7300", "-nodes",
        "-subj", "/C=IN/O=PQC Migration Demo/CN=PQC Demo Root CA (ML-DSA-87)",
    ])
    sizes["pqc_root_ca.key"] = root_key_path.stat().st_size
    sizes["pqc_root_ca.crt"] = root_cert_path.stat().st_size
    print(f"  Root CA (ML-DSA-87): {sizes['pqc_root_ca.crt']} bytes")

    int_csr_path = output / "pqc_intermediate_ca.csr"
    int_key_path = output / "pqc_intermediate_ca.key"
    _run_openssl([
        "req", "-newkey", "mldsa65",
        "-keyout", str(int_key_path),
        "-out", str(int_csr_path),
        "-nodes",
        "-subj", "/C=IN/O=PQC Migration Demo/CN=PQC Demo Intermediate CA (ML-DSA-65)",
    ])

    int_cert_path = output / "pqc_intermediate_ca.crt"
    int_ext_path = output / "_int_ext.cnf"
    write(int_ext_path, b"basicConstraints = critical, CA:TRUE, pathlen:0\nkeyUsage = critical, keyCertSign, cRLSign\n")
    _run_openssl([
        "x509", "-req",
        "-in", str(int_csr_path),
        "-CA", str(root_cert_path),
        "-CAkey", str(root_key_path),
        "-CAcreateserial",
        "-out", str(int_cert_path),
        "-days", "3650",
        "-extfile", str(int_ext_path),
    ])
    sizes["pqc_intermediate_ca.key"] = int_key_path.stat().st_size
    sizes["pqc_intermediate_ca.crt"] = int_cert_path.stat().st_size
    print(f"  Intermediate CA (ML-DSA-65): {sizes['pqc_intermediate_ca.crt']} bytes")

    leaf_csr_path = output / "pqc_server.csr"
    leaf_key_path = output / "pqc_server.key"
    _run_openssl([
        "req", "-newkey", "mldsa65",
        "-keyout", str(leaf_key_path),
        "-out", str(leaf_csr_path),
        "-nodes",
        "-subj", "/C=IN/O=PQC Migration Demo/CN=pqc-demo.local",
    ])

    leaf_cert_path = output / "pqc_server.crt"
    leaf_ext_path = output / "_leaf_ext.cnf"
    write(
        leaf_ext_path,
        b"basicConstraints = critical, CA:FALSE\n"
        b"keyUsage = critical, digitalSignature\n"
        b"extendedKeyUsage = serverAuth\n"
        b"subjectAltName = DNS:pqc-demo.local,DNS:localhost\n",
    )
    _run_openssl([
        "x509", "-req",
        "-in", str(leaf_csr_path),
        "-CA", str(int_cert_path),
        "-CAkey", str(int_key_path),
        "-CAcreateserial",
        "-out", str(leaf_cert_path),
        "-days", "825",
        "-extfile", str(leaf_ext_path),
    ])
    sizes["pqc_server.key"] = leaf_key_path.stat().st_size
    sizes["pqc_server.crt"] = leaf_cert_path.stat().st_size
    print(f"  Leaf cert (ML-DSA-65): {sizes['pqc_server.crt']} bytes")

    chain_pem = (
        leaf_cert_path.read_bytes()
        + int_cert_path.read_bytes()
        + root_cert_path.read_bytes()
    )
    write(output / "pqc_server_chain.crt", chain_pem)
    sizes["pqc_server_chain.crt"] = len(chain_pem)

    for tmp in (int_ext_path, leaf_ext_path, root_cert_path.with_suffix(".srl")):
        if tmp.exists():
            tmp.unlink()

    return sizes


def create_pqc_manifest(output: Path, classical_sizes: dict[str, int], pqc_sizes: dict[str, int]) -> None:
    manifest = {
        "mode": "native-pqc" if pqc_sizes else "oqs-ready-manifest",
        "root": {"algorithm": "ML-DSA-87", "file": "pqc_root_ca.crt"},
        "intermediate": {"algorithm": "ML-DSA-65", "file": "pqc_intermediate_ca.crt"},
        "leaf_tls": {"algorithm": "ML-DSA-65", "file": "pqc_server.crt"},
        "classical": {
            "root": "classical_root_ca.crt",
            "intermediate": "classical_intermediate_ca.crt",
            "leaf": "classical_server.crt",
        },
        "classical_sizes": classical_sizes,
        "pqc_sizes": pqc_sizes,
    }
    write(
        output / "pqc_ca_manifest.json", json.dumps(manifest, indent=2).encode("utf-8")
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate demo CA material and PQC CA chain."
    )
    parser.add_argument("--output", default="certs")
    args = parser.parse_args()
    output = Path(args.output)

    print("Generating classical ECDSA certificate chain...")
    classical_sizes = create_classical_chain(output)

    print("Generating PQC ML-DSA certificate chain...")
    pqc_sizes = create_pqc_chain(output)

    create_pqc_manifest(output, classical_sizes, pqc_sizes)
    print(json.dumps({
        "output": str(output),
        "classical_sizes": classical_sizes,
        "pqc_sizes": pqc_sizes,
    }, indent=2))


if __name__ == "__main__":
    main()
