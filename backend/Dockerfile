FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi || \
    pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    sqlalchemy[asyncio]==2.0.25 \
    asyncpg==0.29.0 \
    alembic==1.13.1 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    redis[hiredis]==5.0.1 \
    PyNaCl==1.5.0 \
    cryptography==42.0.0 \
    python-jose[cryptography]==3.3.0 \
    python-multipart==0.0.6 \
    aiosmtplib==3.0.1 \
    minio==7.2.3 \
    prometheus-client==0.19.0

# Copy application code
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn llmsync.main:app --host 0.0.0.0 --port 8000"]
