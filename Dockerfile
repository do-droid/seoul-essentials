FROM python:3.13-slim

WORKDIR /app

# Pinned: `uv:latest` plus a Dockerfile that never copied uv.lock let every
# build resolve fresh — production drifted from fastmcp 3.0.1 (the lock) to
# 4.0.5 unnoticed, fixing one client bug and hiding rejected-argument logs by
# accident. Upgrades are now a uv.lock change, reviewed like code.
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/

LABEL io.modelcontextprotocol.server.name="io.github.do-droid/seoul-essentials"

ENV PORT=8081
EXPOSE ${PORT}

# Run the venv's python directly. `uv run` re-synced and rebuilt the project on
# every cold start ("Building seoul-essentials @ file:///app" in the logs).
CMD [".venv/bin/python", "-m", "src.server"]
