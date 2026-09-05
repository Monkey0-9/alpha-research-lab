FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for C/C++/Rust
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Compile native extensions for Linux
RUN gcc -O3 -shared -fPIC native/c_engine/rolling_ops.c \
    -o native/c_engine/c_engine.so || true
RUN g++ -O3 -shared -fPIC native/cpp_engine/execution_sim.cpp \
    -o native/cpp_engine/cpp_engine.so || true
WORKDIR /app/native/rust_engine
RUN cargo build --release \
    && cp target/release/librust_engine.so ./rust_engine.so \
    || true
WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
