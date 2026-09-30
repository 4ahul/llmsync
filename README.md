# LLMSync

**Self-hostable LLM conversation sync service with end-to-end encryption**

LLMSync synchronizes LLM conversation history across devices using email-based identity and zero-knowledge end-to-end encryption. Built for developers using multiple AI coding tools (Claude Code, Cursor, Codex, etc.).

## Features

- 🔒 **End-to-End Encryption**: Zero-knowledge architecture with client-side encryption (AES-256-GCM)
- 🔄 **Real-Time Sync**: WebSocket support with polling fallback
- 📧 **Magic Link Auth**: Email-based authentication (OAuth support included)
- 📦 **File Attachments**: Encrypted file storage up to 100MB per file
- 🐳 **Easy Deployment**: Docker Compose for one-command setup
- 🔌 **REST API**: Full-featured API for building integrations

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### 1. Clone & Setup

```bash
git clone <repository-url> llmsync
cd llmsync
cp .env.example .env
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- **API** (FastAPI): http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **MinIO**: http://localhost:9000 (console: http://localhost:9001)

### 3. Verify Installation

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## API Overview

### Authentication

**Magic Link Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

Check console logs for the magic link, then verify:
```bash
curl "http://localhost:8000/api/auth/verify?token=<TOKEN>"
```

### Threads & Messages

**Create Thread:**
```bash
curl -X POST http://localhost:8000/api/threads \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Conversation"}'
```

**Create Message:**
```bash
curl -X POST http://localhost:8000/api/threads/<THREAD_ID>/messages \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "id":"<UUID>",
    "thread_seq":1,
    "encrypted_content":"<base64>",
    "encrypted_key":"<base64>",
    "nonce":"<base64>",
    "role":"user",
    "timestamp":"2026-09-30T12:00:00Z"
  }'
```

**List Messages:**
```bash
curl "http://localhost:8000/api/threads/<THREAD_ID>/messages?limit=100" \
  -H "Authorization: Bearer <TOKEN>"
```

### File Uploads

```bash
curl -X POST http://localhost:8000/api/files \
  -H "Authorization: Bearer <TOKEN>" \
  -F "message_id=<MESSAGE_ID>" \
  -F "file=@screenshot.png"
```

### WebSocket Sync

Connect to WebSocket for real-time updates:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/sync/ws?token=<TOKEN>');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Sync event:', data);
};

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));
```

### Polling Fallback

```bash
curl "http://localhost:8000/api/sync/events?cursor=0&limit=100" \
  -H "Authorization: Bearer <TOKEN>"
```

## Architecture

```
┌─────────────────────────────────────┐
│     Client Devices (E2EE)           │
│  Claude Code, Cursor, Gemini CLI    │
└─────────────┬───────────────────────┘
              │ HTTPS/WSS
┌─────────────▼───────────────────────┐
│      FastAPI Backend (Stateless)    │
│  - Auth API (Magic Links)           │
│  - Sync API (REST + WebSocket)      │
│  - File API (Encrypted uploads)     │
└──┬────────────────┬─────────────────┘
   │                │
┌──▼──────┐  ┌──────▼────┐  ┌─────────┐
│Postgres │  │   Redis   │  │  MinIO  │
│(Metadata)  │ (Sessions)│  │ (Files) │
└─────────┘  └───────────┘  └─────────┘
```

## Project Structure

```
llmsync/
├── backend/
│   ├── llmsync/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── database.py          # DB connection
│   │   ├── auth.py              # JWT utilities
│   │   ├── crypto.py            # E2EE utilities
│   │   ├── dependencies.py      # Auth dependencies
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/             # API routers
│   │   │   ├── auth.py
│   │   │   ├── threads.py
│   │   │   ├── messages.py
│   │   │   ├── files.py
│   │   │   └── sync.py
│   │   └── services/            # External services
│   │       ├── redis_client.py
│   │       ├── minio_client.py
│   │       └── email.py
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Test suite
│   ├── pyproject.toml           # Dependencies
│   └── Dockerfile
├── docker-compose.yml           # Service orchestration
├── .env.example                 # Environment template
└── README.md
```

## Security

### Encryption Model

- **Master Key**: 256-bit key generated client-side
- **Recovery Phrase**: 12-word BIP39 mnemonic for key recovery
- **Message Encryption**: AES-256-GCM via ephemeral keys
- **File Encryption**: Separate ephemeral keys per file
- **Server Storage**: Only encrypted ciphertext, never plaintext

### Zero-Knowledge Architecture

The server:
- ✅ Stores encrypted content only
- ✅ Cannot read messages or files
- ✅ Cannot recover lost recovery phrases
- ❌ Never sees plaintext data
- ❌ Cannot decrypt without client keys

## Development

### Running Tests

```bash
cd backend
poetry install
poetry run pytest
```

### Database Migrations

Create migration:
```bash
cd backend
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

### Logs

View API logs:
```bash
docker-compose logs -f api
```

## Configuration

Edit `.env` for custom configuration:

- **Ports**: Change `API_PORT`, `POSTGRES_PORT`, etc.
- **Security**: Set strong `SECRET_KEY` in production
- **OAuth**: Add Google/GitHub client credentials
- **SMTP**: Configure for production email delivery

## Production Deployment

1. **Use HTTPS**: Add nginx or Traefik for TLS
2. **Strong Secrets**: Generate random `SECRET_KEY` and database passwords
3. **Backups**: Backup PostgreSQL and MinIO volumes regularly
4. **Monitoring**: Add Prometheus/Grafana for observability
5. **Rate Limiting**: Configure nginx rate limits

## Roadmap

- [ ] Web UI for browsing conversations
- [ ] Python SDK
- [ ] TypeScript SDK
- [ ] Claude Code plugin
- [ ] Cursor extension
- [ ] Mobile apps (iOS/Android)
- [ ] Team/organization support
- [ ] Search & tagging

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please open an issue first to discuss changes.

## Support

- Issues: GitHub Issues
- Docs: See `/docs` directory
- Community: [Discord](#) (coming soon)

---

Built with ❤️ for the AI coding community
