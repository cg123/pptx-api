FROM python:3.10 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

# Create necessary directories
RUN mkdir -p /app/app/storage/files /app/app/storage/metadata

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
