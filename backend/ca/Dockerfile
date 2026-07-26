FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git ca-certificates \
    libssl-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ── Build liboqs ───────────────────────────────────────────────────────────
FROM base AS liboqs-builder

RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs \
    && cd /tmp/liboqs \
    && mkdir build && cd build \
    && cmake -DCMAKE_INSTALL_PREFIX=/opt/oqs \
        -DOQS_MINIMAL_BUILD="KEM_ml_kem;SIG_ml_dsa" \
        -DCMAKE_BUILD_TYPE=Release \
        .. \
    && make -j$(nproc) \
    && make install

# ── Build oqs-provider ─────────────────────────────────────────────────────
FROM base AS oqs-provider-builder

COPY --from=liboqs-builder /opt/oqs /opt/oqs

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/open-quantum-safe/oqs-provider.git /tmp/oqs-provider \
    && cd /tmp/oqs-provider \
    && mkdir build && cd build \
    && cmake -DCMAKE_PREFIX_PATH=/opt/oqs \
        -DCMAKE_INSTALL_PREFIX=/opt/oqs \
        -DOPENSSL_LIB_DIR=/opt/oqs/lib \
        .. \
    && make -j$(nproc) \
    && mkdir -p /opt/oqs/lib/ossl-modules \
    && cp lib/oqsprovider.so /opt/oqs/lib/ossl-modules/

# ── Runtime ────────────────────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=liboqs-builder /opt/oqs/lib/liboqs.so* /opt/oqs/lib/
COPY --from=oqs-provider-builder /opt/oqs/lib/ossl-modules/oqsprovider.so /opt/oqs/lib/ossl-modules/
COPY --from=liboqs-builder /opt/oqs/include/oqs /opt/oqs/include/oqs

RUN printf 'openssl_conf = openssl_init\n\
\n\
[openssl_init]\n\
providers = provider_sect\n\
\n\
[provider_sect]\n\
default = default_sect\n\
oqs = oqs_sect\n\
\n\
[default_sect]\n\
activate = 1\n\
\n\
[oqs_sect]\n\
module = /opt/oqs/lib/ossl-modules/oqsprovider.so\n\
activate = 1\n' > /opt/oqs/openssl.cnf

ENV OPENSSL_CONF=/opt/oqs/openssl.cnf
ENV LD_LIBRARY_PATH=/opt/oqs/lib
ENV OQS_PROVIDER_AVAILABLE=true

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "generate_pki.py", "--output", "/app/certs"]
