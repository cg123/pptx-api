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

RUN mkdir -p /usr/share/fonts/truetype/
RUN install -m644 /app/app/font_files/calibri.ttf /usr/share/fonts/truetype/

# Create necessary directories
RUN mkdir -p /app/app/storage/files /app/app/storage/metadata

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHON_PPTX_FONT_DIRECTORY="/app/font_files/"

# Run the application
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
