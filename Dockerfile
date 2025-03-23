FROM python:3.14.0a3-slim AS python
WORKDIR /app

########################################################
FROM python AS builder

RUN apt-get update && apt-get install -y build-essential curl

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY pyproject.toml ./

########################################################
FROM python AS final

COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY src src/
COPY pyproject.toml .

ENV HOST="0.0.0.0"
ENV PORT="5000"

RUN useradd -m appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT} || exit 1

CMD ["python", "-m", "uvicorn", "src.service.app:app", "--host", "${HOST}", "--port", "${PORT}"]
