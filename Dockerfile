FROM python:3.14.0a3-slim AS python

FROM python AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY src src/
COPY pyproject.toml pdm.lock ./

RUN pdm install --prod --frozen-lockfile --no-editable --no-self

FROM python AS final
WORKDIR /app

COPY --from=builder /app/.venv/lib/ /usr/local/lib/
COPY --from=builder /app/src /app/src
COPY pyproject.toml .

ENV VIRTUAL_ENV="/app/venv"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

RUN useradd -m appuser
USER appuser

CMD ["python", "-m", "uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "5001"]
