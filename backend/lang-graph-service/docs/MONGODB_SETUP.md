# MongoDB Persistence Setup for CopilotKit + LangGraph

This setup enables persistent chat conversations using MongoDB as the storage backend, optimized for CosmosDB deployment patterns and chat application best practices.

## Features

- **CosmosDB-Aligned Architecture**: Document structure and query patterns optimized for Azure CosmosDB
- **Persistent Chat History**: All chat messages and conversation state are saved to MongoDB
- **User-based Partitioning**: Each conversation is partitioned by `userId` for optimal scalability
- **Efficient Storage Model**: One document per conversation with embedded LangGraph state
- **Automatic Session Restoration**: Recent conversations (within 3 hours) are automatically restored
- **Point Read Operations**: Optimized queries for high performance and low cost
- **RESTful API**: Endpoints to manage conversations (list, create, delete)

## Prerequisites

1. **MongoDB**: You need a MongoDB instance running. Options:
   - Local MongoDB: `docker run -d -p 27017:27017 mongo:latest`
   - MongoDB Atlas (cloud): Create a free cluster at https://cloud.mongodb.com
   - Docker Compose (see example below)

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install
# or
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Update `.env` with your configurations:
```bash
# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb://localhost:27017

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### 3. Start MongoDB (if using Docker)

```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

Or use Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

### 4. Run the Server

```bash
python server.py
```

The server will start on `http://localhost:8000`.

## API Endpoints

### Chat with CopilotKit
- **POST** `/copilotkit` - Main CopilotKit endpoint for chat interactions

### Conversation Management
- **GET** `/conversations/{user_id}` - Get all conversations for a user
- **POST** `/conversations` - Create a new conversation
- **DELETE** `/conversations/{thread_id}?user_id={user_id}` - Delete a conversation

### Session Management
- **GET** `/session/{user_id}` - Check session status and recent activity

### Health Check
- **GET** `/health` - Server health status

## Usage Examples

### Frontend Integration

When making requests to CopilotKit, include the `user_id` and `thread_id` in the configuration:

```javascript
// Frontend example
const response = await fetch('/copilotkit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: "Hello!",
    config: {
      configurable: {
        user_id: "user123",
        thread_id: "conversation456"
      }
    }
  })
});
```

### Creating a New Conversation

```javascript
// Create a new conversation
const newConv = await fetch('/conversations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: "user123" })
});
const { thread_id } = await newConv.json();
```

### Retrieving User Conversations

```javascript
// Get all conversations for a user
const conversations = await fetch('/conversations/user123');
const convList = await conversations.json();
```

## Automatic Session Restoration

The system now automatically handles session restoration based on recent activity:

### How It Works
1. **New Chat**: When CopilotKit runtime starts a chat, only provide `user_id` (no `thread_id`)
2. **Session Check**: System checks for conversations within the last 3 hours
3. **Restore or Create**:
   - If recent conversation found → restores that session
   - If no recent activity → creates new conversation thread
4. **Seamless Experience**: User continues where they left off

### Configuration
- **Time Threshold**: 3 hours (configurable)
- **Per-User Isolation**: Each user's sessions are independent
- **Automatic Cleanup**: Old sessions naturally age out

### Example Behavior
```
User starts chat → System checks last activity
├── Last message < 3 hours ago → Restore session ABC123
└── Last message > 3 hours ago → Create new session XYZ789
```

## Database Schema

The MongoDB collection stores **one document per conversation thread** with this structure:

```json
{
  "_id": "ObjectId",
  "thread_id": "uuid4-string",
  "user_id": "user123",
  "checkpoint_id": "latest-checkpoint-uuid",
  "checkpoint_ns": "timestamp",
  "checkpoint": {
    "v": 1,
    "ts": "timestamp",
    "id": "checkpoint-id",
    "channel_values": {
      "messages": [...],  // All conversation messages
      "agent_state": {...}  // Current agent state
    },
    "channel_versions": {...},
    "versions_seen": {...},
    "pending_sends": []
  },
  "metadata": {
    "source": "input",
    "step": 1,
    "writes": {...},
    "parents": {...}
  },
  "created_at": "2025-07-15T10:30:00Z",  // When conversation started
  "updated_at": "2025-07-15T10:30:00Z"   // Last message timestamp
}
```

**Key Design Decision**: Only the **latest checkpoint** is stored per conversation. Each new message/interaction replaces the entire document, keeping the database size manageable while preserving the complete conversation state.

## Storage Efficiency

### Latest Checkpoint Only
This implementation saves **only the latest checkpoint** per conversation, not every intermediate state. This provides several benefits:

- **Database Size**: Prevents exponential growth from storing every checkpoint
- **Performance**: Faster queries with one document per conversation
- **Cost Effective**: Minimal storage requirements, perfect for production
- **Clean State**: Complete conversation state in a single document

### What Gets Saved
- ✅ **Complete conversation history** (all messages)
- ✅ **Current agent state** (context, variables, etc.)
- ✅ **Session metadata** (user_id, timestamps)
- ❌ **Intermediate checkpoints** (only latest state)

For most chat applications, you only need the current state to continue conversations, making this approach ideal.

## Migration to CosmosDB

When moving to production with CosmosDB:

1. **Connection String**: Update `MONGODB_CONNECTION_STRING` to CosmosDB connection string
2. **API Compatibility**: CosmosDB supports MongoDB API, so minimal code changes needed
3. **Indexing**: CosmosDB has different indexing - update the `ensure_indexes()` method
4. **Scaling**: Configure CosmosDB throughput and partitioning as needed

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure MongoDB is running and accessible
2. **Import Errors**: Run `poetry install` or `pip install -r requirements.txt`
3. **Permission Issues**: Check MongoDB user permissions if using authentication

### Logs

The server logs checkpoint operations. Check console output for debugging.

### Database Inspection

Use MongoDB Compass or CLI to inspect the stored conversations:

```bash
# Connect to MongoDB
mongosh

# List databases
show dbs

# Use the chat database
use chatdb

# List collections
show collections

# Query conversations
db.conversations.find().pretty()
```
