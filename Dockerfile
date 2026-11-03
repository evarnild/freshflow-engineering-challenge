FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.6.10 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app

# Dependencies first, so this layer is cached until the lockfile changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY data/ ./data/
RUN uv sync --frozen --no-dev

RUN useradd --system --no-create-home app
USER app

ENV PATH="/app/.venv/bin:$PATH" DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn", "freshflow.api:app", "--host", "0.0.0.0", "--port", "8000"]
