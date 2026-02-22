FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .python-version ./
RUN uv sync --no-dev --no-editable

COPY src/ src/

ENV PORT=8081
EXPOSE ${PORT}

CMD ["uv", "run", "python", "-m", "src.server"]
