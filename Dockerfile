FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
CMD ["uv", "run", "app-start"]
