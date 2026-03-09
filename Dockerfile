FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-install all Python dependencies (agent + server)
RUN pip install --no-cache-dir \
    agno \
    anthropic \
    "typer[all]" \
    rich \
    python-dotenv \
    sqlalchemy \
    aiosqlite \
    fastapi \
    uvicorn

# PYTHONPATH lets Python find the miguel package from the volume mount
ENV PYTHONPATH=/app
ENV USER_FILES_DIR=/app/user_files

EXPOSE 8420

CMD ["uvicorn", "miguel.agent.server:app", "--host", "0.0.0.0", "--port", "8420"]
