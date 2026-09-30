FROM lukemathwalker/cargo-chef:latest-rust-1.97.1 AS chef
WORKDIR /app

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json
COPY . .
RUN cargo build --release --bin report-service

FROM debian:trixie-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# -m: typst-kit's package downloader (cetz/cetz-plot @preview fetches) needs
# a writable $HOME/.cache to store them in — a homeless -r-only account
# leaves $HOME pointing at a directory that's never created.
RUN groupadd -r app && useradd -r -m -g app app
COPY --from=builder --chown=app:app /app/target/release/report-service /app/report-service
COPY --from=builder --chown=app:app /app/templates /app/templates
USER app
ENTRYPOINT ["/app/report-service"]
