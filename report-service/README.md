# report-service

Rust worker that generates PDF reports (via [Typst](https://typst.app)) for
the outbox pipeline in the main `saas-catalog-analyzer` project. Reads the
same `requests`/`request_attempts` tables and the same `.env` as the Python
app — see the repo root README/`.env.example` for the full variable list.
Schema migrations are owned entirely by Alembic (Python side); this service
never runs migrations itself.

## Requirements

- Rust toolchain pinned in `rust-toolchain.toml` (installed automatically by
  `rustup` when you run any `cargo` command in this directory).
- Postgres + LocalStack running (`docker compose up -d` from the repo root).

## Running locally

```sh
cd report-service
set -a && source ../.env && set +a
cargo run
```

## Checks

```sh
cargo fmt --check
SQLX_OFFLINE=true cargo clippy --all-targets -- -D warnings
```

Both also run automatically via the repo-root pre-commit hook
(`.pre-commit-config.yaml`) whenever `report-service/**` files change. Install
it once with `uvx pre-commit install` from the repo root.

## sqlx offline mode

`sqlx::query!`/`query_as!` check queries against a live database at compile
time by default. `.sqlx/` holds a cached snapshot of that check so `cargo
build`/`clippy` work with `SQLX_OFFLINE=true` and no database connection —
this is what the pre-commit hook and (later) CI use. Whenever you add or
change a query, regenerate the cache against a running Postgres and commit
the result:

```sh
set -a && source ../.env && set +a
cargo sqlx prepare
git add .sqlx
```

## Lints

`clippy::pedantic` is enabled repo-wide for this crate (see `[lints.clippy]`
in `Cargo.toml`), plus `clippy::excessive_nesting` with a threshold of 4
(`clippy.toml`).
