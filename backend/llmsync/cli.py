"""
LLMSync CLI - Command-line interface for LLMSync server
"""
import sys
import argparse
from pathlib import Path

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLMSync - E2E encrypted conversation sync service"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="llmsync 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new LLMSync instance"
    )
    init_parser.add_argument(
        "--path",
        default=".",
        help="Directory to initialize (default: current directory)"
    )

    # Start command
    start_parser = subparsers.add_parser(
        "start",
        help="Start LLMSync server"
    )
    start_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    start_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    if args.command == "init":
        init_llmsync(args.path)
    elif args.command == "start":
        start_server(args.host, args.port, args.reload)
    else:
        parser.print_help()

def init_llmsync(path: str):
    """Initialize LLMSync in the given directory."""
    import shutil

    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Initializing LLMSync in {path_obj.absolute()}")

    # Create .env file
    env_content = """# LLMSync Configuration

# Database
DATABASE_URL=postgresql+asyncpg://llmsync:llmsync@localhost:5432/llmsync

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=llmsync
MINIO_SECRET_KEY=llmsync123
MINIO_BUCKET=llmsync-files
MINIO_SECURE=false

# API
SECRET_KEY=change-this-to-a-random-32-character-string
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Optional: Sentry
# SENTRY_DSN=

# Optional: SMTP
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=
# SMTP_PASSWORD=
"""

    (path_obj / ".env").write_text(env_content)
    print("✓ Created .env configuration file")

    # Create docker-compose.yml
    compose_content = """# This is a simplified docker-compose.yml
# For full version, see: https://github.com/4ahul/llmsync

version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: llmsync
      POSTGRES_USER: llmsync
      POSTGRES_PASSWORD: llmsync
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: llmsync
      MINIO_ROOT_PASSWORD: llmsync123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
"""

    (path_obj / "docker-compose.yml").write_text(compose_content)
    print("✓ Created docker-compose.yml")

    print("\n✅ LLMSync initialized!")
    print("\nNext steps:")
    print("  1. Edit .env and set SECRET_KEY to a random string")
    print("  2. Start services: docker-compose up -d")
    print("  3. Start LLMSync: llmsync start")
    print("\nDocumentation: https://github.com/4ahul/llmsync")

def start_server(host: str, port: int, reload: bool):
    """Start the LLMSync server."""
    import uvicorn

    print(f"🚀 Starting LLMSync server on {host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    print(f"   Health: http://{host}:{port}/api/health")

    uvicorn.run(
        "llmsync.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
