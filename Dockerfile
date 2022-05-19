# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.209.6/containers/rust/.devcontainer/base.Dockerfile

# [Choice] Debian OS version (use bullseye on local arm64/Apple Silicon): buster, bullseye
# ARG VARIANT="buster"
# FROM mcr.microsoft.com/vscode/devcontainers/rust:0-${VARIANT}
FROM debian

RUN apt-get clean
RUN apt-get update
RUN apt-get install -y \
    build-essential \
    curl

# Update new packages
RUN apt-get update

# Get Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN rustup target add wasm32-wasi
# RUN rustup component add rustfmt rust-src clippy

RUN cargo install cargo-wasi cargo-expand && \
    cargo install --git https://github.com/bytecodealliance/wit-bindgen wit-bindgen-cli

#RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
#    apt-get -y install --no-install-recommends lsb-release wget software-properties-common

#RUN bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)" && \
#    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-13 100 && \
#    update-alternatives --install /usr/bin/wasm-ld wasm-ld /usr/bin/wasm-ld-13 100

#RUN cd /opt && wget -c https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-14/wasi-sysroot-14.0.tar.gz -O - | tar -xz
ENV WASI_SDK_VERSION=14.0
RUN cd /opt && curl -L https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-14/wasi-sdk-${WASI_SDK_VERSION}-linux.tar.gz \
    | tar -xz

ENV WASMTIME_VERSION=0.33.0
RUN curl -L https://github.com/bytecodealliance/wasmtime/releases/download/v${WASMTIME_VERSION}/wasmtime-v${WASMTIME_VERSION}-x86_64-linux.tar.xz \ 
    | tar -xJ --wildcards --no-anchored --strip-components 1 -C /usr/bin wasmtime

