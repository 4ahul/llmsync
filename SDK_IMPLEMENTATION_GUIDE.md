# SDK & MCP Implementation Guide

Complete guide to implementing the Python SDK, TypeScript SDK, and MCP server for LLMSync.

---

## 📦 Python SDK (llmsync-sdk)

### Structure
```
sdk/python/
├── pyproject.toml                 ✅ Created
├── README.md
├── llmsync_sdk/
│   ├── __init__.py               ✅ Created
│   ├── client.py                 📝 Need to implement
│   ├── crypto.py                 📝 Need to implement
│   ├── websocket.py              📝 Need to implement
│   ├── models.py                 📝 Need to implement
│   └── exceptions.py             📝 Need to implement
└── tests/
    ├── test_client.py
    ├── test_crypto.py
    └── test_websocket.py
```

### Usage Example
```python
from llmsync_sdk import LLMSyncClient

# Initialize
client = LLMSyncClient("https://api.llmsync.io")

# Login with magic link
await client.request_magic_link("user@example.com")
# User receives email, extracts token
await client.verify_magic_link(token)

# Setup encryption (first time)
recovery_phrase = await client.generate_recovery_phrase()
# Returns: "word1 word2 ... word12"
await client.setup_encryption(recovery_phrase)

# Register device
device_id = await client.register_device("MacBook Pro")

# Create thread
thread = await client.create_thread("My Conversation")

# Send encrypted message
message = await client.send_message(
    thread_id=thread.id,
    content="Hello World",  # Encrypted automatically
    role="user"
)

# List messages
messages = await client.get_messages(thread.id)
for msg in messages:
    print(msg.content)  # Decrypted automatically

# Upload encrypted file
file_id = await client.upload_file(
    message_id=message.id,
    file_path="document.pdf"
)

# Real-time sync
def on_sync_event(event):
    print(f"New {event.event_type}: {event.entity_id}")

await client.connect_sync(on_sync_event)

# Keep connection alive
await client.run_forever()
```

### Key Classes to Implement

#### 1. client.py - Main Client
```python
class LLMSyncClient:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.token: Optional[str] = None
        self.master_key: Optional[bytes] = None
        self.http = httpx.AsyncClient()
        self.ws: Optional[WebSocketClient] = None
    
    async def request_magic_link(self, email: str):
        """Request magic link to email."""
        pass
    
    async def verify_magic_link(self, token: str):
        """Verify magic link and get access token."""
        pass
    
    async def generate_recovery_phrase(self) -> str:
        """Generate 12-word BIP39 recovery phrase."""
        pass
    
    async def setup_encryption(self, recovery_phrase: str):
        """Setup encryption with recovery phrase."""
        # 1. Generate master key
        # 2. Derive backup key from phrase
        # 3. Encrypt master key
        # 4. Send to server
        pass
    
    async def send_message(self, thread_id: str, content: str, role: str):
        """Send encrypted message."""
        # 1. Generate message UUID
        # 2. Encrypt content with master key
        # 3. Send to server
        pass
```

#### 2. crypto.py - E2EE Helpers
```python
from nacl.secret import SecretBox
from nacl.encoding import Base64Encoder
import base64

def generate_master_key() -> bytes:
    """Generate 32-byte master key."""
    return SecretBox.generate_key()

def generate_recovery_phrase() -> str:
    """Generate BIP39 12-word phrase."""
    # Use same algorithm as backend
    pass

def derive_key_from_phrase(phrase: str) -> bytes:
    """Derive key from recovery phrase using Argon2id."""
    from nacl.pwhash import argon2id
    pass

def encrypt_message(plaintext: str, master_key: bytes) -> dict:
    """Encrypt message with master key."""
    # Returns: encrypted_content, encrypted_key, nonce
    pass

def decrypt_message(encrypted: dict, master_key: bytes) -> str:
    """Decrypt message."""
    pass
```

#### 3. websocket.py - Real-Time Sync
```python
import websockets
import asyncio
import json

class WebSocketClient:
    def __init__(self, ws_url: str, token: str):
        self.ws_url = ws_url
        self.token = token
        self.ws = None
        self.callbacks = []
    
    async def connect(self):
        """Connect to WebSocket."""
        url = f"{self.ws_url}/api/sync/ws?token={self.token}"
        self.ws = await websockets.connect(url)
    
    async def listen(self):
        """Listen for events."""
        async for message in self.ws:
            data = json.loads(message)
            if data["type"] == "sync_event":
                for callback in self.callbacks:
                    callback(data["event"])
    
    def on_event(self, callback):
        """Register event callback."""
        self.callbacks.append(callback)
```

#### 4. models.py - Data Models
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Thread(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

class Message(BaseModel):
    id: str
    thread_id: str
    content: str  # Decrypted
    role: str
    timestamp: datetime

class Device(BaseModel):
    id: str
    device_name: Optional[str]
    device_fingerprint: str
    added_at: datetime
```

### Publishing to PyPI
```bash
# Build
cd sdk/python
python -m build

# Upload
python -m twine upload dist/*

# Install
pip install llmsync-sdk
```

---

## 📦 TypeScript SDK (@llmsync/sdk)

### Structure
```
sdk/typescript/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts
│   ├── client.ts
│   ├── crypto.ts
│   ├── websocket.ts
│   ├── models.ts
│   └── types.ts
└── tests/
    └── client.test.ts
```

### package.json
```json
{
  "name": "@llmsync/sdk",
  "version": "0.1.0",
  "description": "TypeScript SDK for LLMSync",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "prepublishOnly": "npm run build"
  },
  "dependencies": {
    "libsodium-wrappers": "^0.7.11",
    "ws": "^8.16.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/ws": "^8.5.0",
    "typescript": "^5.3.0",
    "jest": "^29.7.0"
  }
}
```

### Usage Example
```typescript
import { LLMSyncClient } from '@llmsync/sdk';

// Initialize
const client = new LLMSyncClient('https://api.llmsync.io');

// Login
await client.requestMagicLink('user@example.com');
await client.verifyMagicLink(token);

// Setup encryption
const recoveryPhrase = await client.generateRecoveryPhrase();
await client.setupEncryption(recoveryPhrase);

// Send message
const message = await client.sendMessage(
  threadId,
  'Hello World',
  'user'
);

// Real-time sync
client.onSyncEvent((event) => {
  console.log('Sync event:', event);
});

await client.connectSync();
```

### Key Files to Implement

#### src/client.ts
```typescript
export class LLMSyncClient {
  private apiUrl: string;
  private token?: string;
  private masterKey?: Uint8Array;
  private ws?: WebSocket;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }

  async requestMagicLink(email: string): Promise<void> {
    const response = await fetch(`${this.apiUrl}/api/auth/login/magic-link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    // Handle response
  }

  async sendMessage(
    threadId: string,
    content: string,
    role: 'user' | 'assistant'
  ): Promise<Message> {
    // 1. Encrypt content
    const encrypted = await this.encryptMessage(content);
    
    // 2. Send to API
    const response = await fetch(
      `${this.apiUrl}/api/threads/${threadId}/messages`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: crypto.randomUUID(),
          thread_seq: 1, // Track locally
          encrypted_content: encrypted.content,
          encrypted_key: encrypted.key,
          nonce: encrypted.nonce,
          role,
          timestamp: new Date().toISOString()
        })
      }
    );
    
    return await response.json();
  }

  async connectSync(): Promise<void> {
    this.ws = new WebSocket(
      `${this.apiUrl.replace('http', 'ws')}/api/sync/ws?token=${this.token}`
    );
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'sync_event') {
        this.emit('sync_event', data.event);
      }
    };
  }
}
```

#### src/crypto.ts
```typescript
import sodium from 'libsodium-wrappers';

export async function generateMasterKey(): Promise<Uint8Array> {
  await sodium.ready;
  return sodium.crypto_secretbox_keygen();
}

export async function encryptMessage(
  plaintext: string,
  masterKey: Uint8Array
): Promise<{ content: string; key: string; nonce: string }> {
  await sodium.ready;
  
  // Generate ephemeral message key
  const messageKey = sodium.crypto_secretbox_keygen();
  const nonce = sodium.randombytes_buf(sodium.crypto_secretbox_NONCEBYTES);
  
  // Encrypt content
  const ciphertext = sodium.crypto_secretbox_easy(
    plaintext,
    nonce,
    messageKey
  );
  
  // Wrap message key with master key
  const wrappedKey = sodium.crypto_secretbox_easy(
    messageKey,
    nonce,
    masterKey
  );
  
  return {
    content: sodium.to_base64(ciphertext),
    key: sodium.to_base64(wrappedKey),
    nonce: sodium.to_base64(nonce)
  };
}
```

### Publishing to NPM
```bash
# Build
cd sdk/typescript
npm run build

# Publish
npm publish --access public

# Install
npm install @llmsync/sdk
```

---

## 🔌 MCP Server (llmsync-mcp)

### What is MCP?

MCP (Model Context Protocol) allows Claude Code to access external tools. An LLMSync MCP server exposes conversation sync functionality directly in Claude Code.

### Structure
```
mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts          (MCP server)
│   ├── client.ts         (LLMSync API client)
│   ├── tools.ts          (MCP tool definitions)
│   └── types.ts
└── README.md
```

### package.json
```json
{
  "name": "llmsync-mcp",
  "version": "0.1.0",
  "description": "MCP server for LLMSync integration with Claude Code",
  "bin": {
    "llmsync-mcp": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "@llmsync/sdk": "^0.1.0"
  }
}
```

### MCP Tools Exposed

#### 1. llmsync_save_conversation
```typescript
{
  name: "llmsync_save_conversation",
  description: "Save the current conversation to LLMSync",
  inputSchema: {
    type: "object",
    properties: {
      title: { type: "string", description: "Conversation title" },
      messages: {
        type: "array",
        items: {
          type: "object",
          properties: {
            role: { type: "string", enum: ["user", "assistant"] },
            content: { type: "string" }
          }
        }
      }
    },
    required: ["messages"]
  }
}
```

#### 2. llmsync_list_threads
```typescript
{
  name: "llmsync_list_threads",
  description: "List all synced conversation threads",
  inputSchema: {
    type: "object",
    properties: {
      limit: { type: "number", default: 20 }
    }
  }
}
```

#### 3. llmsync_get_thread
```typescript
{
  name: "llmsync_get_thread",
  description: "Get a specific conversation thread with all messages",
  inputSchema: {
    type: "object",
    properties: {
      thread_id: { type: "string", description: "Thread UUID" }
    },
    required: ["thread_id"]
  }
}
```

#### 4. llmsync_search
```typescript
{
  name: "llmsync_search",
  description: "Search across all synced conversations",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
      limit: { type: "number", default: 10 }
    },
    required: ["query"]
  }
}
```

### Implementation

#### src/index.ts - MCP Server
```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { LLMSyncClient } from '@llmsync/sdk';
import { tools } from './tools.js';

const API_URL = process.env.LLMSYNC_API_URL || 'http://localhost:8000';
const TOKEN = process.env.LLMSYNC_TOKEN;

const client = new LLMSyncClient(API_URL);
client.setToken(TOKEN);

const server = new Server(
  {
    name: 'llmsync-mcp',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register tools
server.setRequestHandler('tools/list', async () => ({
  tools: tools
}));

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case 'llmsync_save_conversation':
      return await saveConversation(args, client);
    
    case 'llmsync_list_threads':
      return await listThreads(args, client);
    
    case 'llmsync_get_thread':
      return await getThread(args, client);
    
    case 'llmsync_search':
      return await searchConversations(args, client);
    
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('LLMSync MCP server running');
```

### Usage in Claude Code

Add to Claude Code config (`~/.config/claude-code/mcp-servers.json`):

```json
{
  "mcpServers": {
    "llmsync": {
      "command": "npx",
      "args": ["llmsync-mcp"],
      "env": {
        "LLMSYNC_API_URL": "https://api.llmsync.io",
        "LLMSYNC_TOKEN": "your-access-token"
      }
    }
  }
}
```

Then in Claude Code:
```
User: "Save this conversation to LLMSync"

Claude: [Uses llmsync_save_conversation tool]
✓ Conversation saved to LLMSync (Thread ID: abc-123)

User: "Show me my previous conversations about Python"

Claude: [Uses llmsync_search tool with query="Python"]
Found 3 conversations:
1. Python async patterns (2 days ago)
2. Python packaging guide (1 week ago)
3. Python testing best practices (2 weeks ago)
```

---

## 🚀 Implementation Priority

### Week 1 (Must Have)
1. **Python SDK basics** (8 hours)
   - client.py with HTTP methods
   - crypto.py with E2EE
   - Basic models

2. **MCP Server** (8 hours)
   - Core 4 tools
   - LLMSync API client
   - Claude Code integration

### Week 2 (Should Have)
3. **TypeScript SDK** (12 hours)
   - Same features as Python SDK
   - Browser + Node.js support

4. **WebSocket Support** (4 hours)
   - Add to both SDKs
   - Real-time sync

### Week 3 (Nice to Have)
5. **Tests** (8 hours)
   - Unit tests for both SDKs
   - Integration tests

6. **Documentation** (4 hours)
   - API docs
   - Examples
   - Tutorials

---

## 📦 Publishing Checklist

### Python SDK to PyPI
- [ ] Complete implementation
- [ ] Write tests (pytest)
- [ ] Add README with examples
- [ ] Build: `python -m build`
- [ ] Test install: `pip install dist/*.whl`
- [ ] Upload: `twine upload dist/*`

### TypeScript SDK to NPM
- [ ] Complete implementation
- [ ] Write tests (Jest)
- [ ] Add README with examples
- [ ] Build: `npm run build`
- [ ] Test install: `npm pack && npm install *.tgz`
- [ ] Publish: `npm publish --access public`

### MCP Server
- [ ] Complete implementation
- [ ] Test with Claude Code
- [ ] Add README with setup guide
- [ ] Publish to NPM
- [ ] Add to MCP server registry

---

## 💡 Tips

### For Python SDK
- Use `httpx` for async HTTP
- Use `PyNaCl` for encryption (same as backend)
- Use `websockets` for WebSocket
- Follow backend crypto exactly

### For TypeScript SDK
- Use `libsodium-wrappers` for encryption
- Support both browser and Node.js
- Include TypeScript types
- Bundle with rollup/esbuild

### For MCP Server
- Keep tools simple and focused
- Handle errors gracefully
- Log to stderr (not stdout - MCP uses stdout for protocol)
- Test with real Claude Code before publishing

---

## 🎯 Success Criteria

SDKs are complete when:
- ✅ Can authenticate with magic link
- ✅ Can setup encryption
- ✅ Can send/receive encrypted messages
- ✅ Can upload/download encrypted files
- ✅ Can sync via WebSocket
- ✅ Has tests with >80% coverage
- ✅ Has clear documentation
- ✅ Published to package registry

MCP Server is complete when:
- ✅ All 4 tools work in Claude Code
- ✅ Can save current conversation
- ✅ Can retrieve past conversations
- ✅ Can search conversations
- ✅ Published to NPM
- ✅ Setup guide exists

---

**Estimated Total Time: 44 hours**
- Python SDK: 12 hours
- TypeScript SDK: 16 hours
- MCP Server: 12 hours
- Documentation: 4 hours

**Result: Complete developer experience + Claude Code integration** 🎉
