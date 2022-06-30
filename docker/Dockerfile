FROM rust:1.61.0-alpine as rust_builder
RUN apk add build-base git openssh
RUN cargo install --git https://github.com/bytecodealliance/wit-bindgen wit-bindgen-cli
ADD ./ /writ/
RUN rm -rf /writ/examples /writ/.git && \
    git clone https://github.com/bytecodealliance/wasmtime-py.git /wasmtime-py

FROM python:3.9-alpine as base
COPY --from=rust_builder /usr/local/cargo/bin/wit-bindgen /usr/bin
COPY --from=rust_builder /writ /writ
COPY --from=rust_builder /wasmtime-py /wasmtime-py
RUN apk add libgcc libc6-compat gdb && \
    ln -s /lib/libc.musl-x86_64.so.1 /lib/ld-linux-x86-64.so.2
RUN cd wasmtime-py && python3 download-wasmtime.py && python3 setup.py install && \
    cd .. && rm -rf /wasmtime-py
RUN cd writ && python3 setup.py install

ENTRYPOINT ["/writ/bin/writ"]

