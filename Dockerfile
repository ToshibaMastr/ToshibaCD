FROM python:3.14.0a3-slim AS python
WORKDIR /app

########################################################
FROM python AS builder

RUN apt-get update && apt-get install -y build-essential

RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY pyproject.toml pdm.lock ./
RUN pdm install --prod --frozen-lockfile --no-editable --no-self

########################################################
FROM python AS final

COPY --from=builder /app/.venv/lib/ /usr/local/lib/
COPY src src/
COPY pyproject.toml .

ENV VIRTUAL_ENV="/app/venv"
ENV HOST="0.0.0.0"
ENV PORT="5000"

RUN useradd -m appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT} || exit 1

CMD ["python", "-m", "uvicorn", "src.service.app:app", "--host", "$HOST", "--port", "$PORT"]
