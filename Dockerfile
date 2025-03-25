FROM python:3.13-slim AS python
WORKDIR /app

########################################################
FROM python AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-editable

########################################################
FROM python AS final

COPY --from=builder /app/.venv .venv

COPY src src/
COPY pyproject.toml .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080
CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8080"]
