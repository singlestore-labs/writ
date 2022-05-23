FROM debian as builder

RUN apt-get clean
RUN apt-get update
RUN apt-get install -y \
    build-essential \
    curl

# Update new packages
RUN apt-get update

# Get Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

# Get Python
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN pip install wasmtime 

ENV PATH="/root/.cargo/bin:${PATH}"

RUN rustup target add wasm32-wasi

RUN cargo install cargo-wasi cargo-expand && \
    cargo install --git https://github.com/bytecodealliance/wit-bindgen wit-bindgen-cli

ENV WASI_SDK_VERSION=14.0
RUN cd /opt && curl -L https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-14/wasi-sdk-${WASI_SDK_VERSION}-linux.tar.gz \
    | tar -xz

ENV WASMTIME_VERSION=0.33.0
RUN curl -L https://github.com/bytecodealliance/wasmtime/releases/download/v${WASMTIME_VERSION}/wasmtime-v${WASMTIME_VERSION}-x86_64-linux.tar.xz \ 
    | tar -xJ --wildcards --no-anchored --strip-components 1 -C /usr/bin wasmtime

COPY src/ /usr/bin/ 
COPY test test/

ENTRYPOINT ["/usr/bin/writ"]
