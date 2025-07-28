# CopilotKit + LangGraph with CosmosDB

Fullstack AI chat assistant with persistent conversations using CosmosDB, LangGraph, and CopilotKit.

## Table of Contents

- [CopilotKit + LangGraph with CosmosDB](#copilotkit--langgraph-with-cosmosdb)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [How It Works](#how-it-works)
    - [Configuration](#configuration)
    - [Example Behavior](#example-behavior)
  - [Fast API Endpoints](#fast-api-endpoints)
    - [Chat with CopilotKit](#chat-with-copilotkit)
    - [Conversation Management](#conversation-management)
    - [Session Management](#session-management)
    - [Health Check](#health-check)
  - [CosmosDB Design](#cosmosdb-design)
    - [Container Purposes](#container-purposes)
    - [Why We Need Both Systems](#why-we-need-both-systems)
    - [Could We Simplify This?](#could-we-simplify-this)
    - [Conversation Object Design](#conversation-object-design)
    - [Storage Efficiency - Latest Checkpoint Only](#storage-efficiency---latest-checkpoint-only)
      - [What Gets Saved](#what-gets-saved)
  - [Dev Setup](#dev-setup)
  - [License](#license)

## Project Structure

- `react-client`: The frontend React application
- `copilot-runtime-service`: The CopilotKit runtime service
- `lang-graph-service`: The LangGraph agent service

```sh
[react-client]
      |
[copilot-runtime-service]
      |
[lang-graph-service]
```

## How It Works
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

## Fast API Endpoints

Open the Swagger API page at http://localhost:8000/docs to play with the endpoints.

### Chat with CopilotKit

- **POST** `/copilotkit` - Main CopilotKit endpoint for chat interactions

### Conversation Management

- **GET** `/conversation-by-user/{user_id}` - Get conversations for a specific user
- **GET** `/conversation-by-id/{thread_id}` - Get conversation details by thread ID
- **POST** `/conversations` - Create a new conversation
- **DELETE** `/conversations/{thread_id}` - Delete a conversation
- **GET** `/database-summary` - Get summary of all conversations with unique user_ids and thread_ids

### Session Management

- **GET** `/session/{user_id}` - Check session status and recent activity

### Health Check

- **GET** `/health` - Server health status

---

## CosmosDB Design

**Database name**: `chat_assistant`
**Container names:**: `conversations`, `checkpoints`, `checkpoint_writes`

This structure is about the separation of concerns between LangGraph's internal checkpointing system and our conversation management features.

### Container Purposes

1. `conversations` Container

- Purpose: High-level conversation management for our application
- Contains: User-friendly conversation metadata, message summaries, last updated timestamps
- Partition Key: userId (optimized for user queries)
- Used for:
  - `/conversation-by-user/{user_id}` - listing user's conversations
  - `/conversation-by-id/{thread_id}` - getting conversation details
  - `/database-summary` - count of conversations, list of user IDs and thread IDs

1. `checkpoints` Container

- Purpose: LangGraph's internal state management system
- Contains: Complete agent state snapshots, execution checkpoints, internal LangGraph metadata
- Partition Key: thread_id (optimized for LangGraph operations)
- Used for:
  - Session restoration (when user returns to continue a conversation)
  - Agent state recovery between requests
  - LangGraph's internal workflow execution

1. `checkpoint_writes` Container

- Purpose: LangGraph's intermediate execution tracking
- Contains: Pending writes, partial state updates, task execution details
- Used for:
  - Handling multi-step agent operations
  - Ensuring consistency during complex workflows
  - Recovery from interrupted agent executions

### Why We Need Both Systems
The key insight is that LangGraph requires its own checkpointing system to function properly - this is built into the framework. We can't just store conversations and expect LangGraph to work without its checkpoints.

**Think of it like this:**

- conversations = user-facing features (like a file explorer showing documents)
- checkpoints + checkpoint_writes = system internals (like the filesystem's inodes and journal)

### Could We Simplify This?
We could potentially eliminate the separate conversations container and derive everything from the checkpoints, but that would:

1. Make queries slower - we'd have to parse complex LangGraph state for simple operations like "show user's conversations"
1. Couple our UI to LangGraph internals - if LangGraph changes its checkpoint format, our UI breaks
1. Make the code more complex - extracting user-friendly data from technical checkpoints is harder
1. Reduce performance - checkpoints are large and complex; conversations are lightweight summaries

The current design gives us clean separation: LangGraph handles agent execution, while our conversation layer handles user experience.

### Conversation Object Design

The `conversations` container stores **one document per conversation thread** with this structure:

```json
{
  "_id": "ObjectId",
  "thread_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  // Standard GUID format
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

**Key Design Decisions**:
- **GUID Format**: Thread IDs use standard GUID format (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) for compatibility with external systems
- **Latest Checkpoint Only**: Only the latest checkpoint is stored per conversation. Each new message/interaction replaces the entire document, keeping the database size manageable while preserving the complete conversation state
- **User ID Storage**: User IDs are stored separately in the conversation document, not embedded in the thread ID

### Storage Efficiency - Latest Checkpoint Only

This implementation saves **only the latest checkpoint** per conversation, not every intermediate state. This provides several benefits:

- **Database Size**: Prevents exponential growth from storing every checkpoint
- **Performance**: Faster queries with one document per conversation
- **Cost Effective**: Minimal storage requirements, perfect for production
- **Clean State**: Complete conversation state in a single document

#### What Gets Saved

- ✅ **Complete conversation history** (all messages)
- ✅ **Current agent state** (context, variables, etc.)
- ✅ **Session metadata** (user_id, timestamps)
- ❌ **Intermediate checkpoints** (only latest state)

For most chat applications, you only need the current state to continue conversations, making this approach ideal.

---

## Dev Setup

1. **Copy and update environment variables:**

   ```sh
   cp lang-graph-service/.env.example lang-graph-service/.env
   ```

   Edit lang-graph-service/.env and set your variables:

   ```env
   # CosmosDB Configuration (required)
   COSMOSDB_ENDPOINT=https://your-account.documents.azure.com:443/
   # Option 1: Use connection string (recommended for development)
   COSMOSDB_CONNECTION_STRING=AccountEndpoint=https://your-account.documents.azure.com:443/;AccountKey=your-key;
   # Option 2: Use DefaultAzureCredential (for production with managed identity)
   COSMOSDB_DATABASE=chat_assistant
   COSMOSDB_CONVERSATIONS_CONTAINER=conversations
   COSMOSDB_CHECKPOINTS_CONTAINER=checkpoints
   COSMOSDB_CHECKPOINT_WRITES_CONTAINER=checkpoint_writes

   # Server config
   PORT=8000
   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_MODEL=gpt-4o-mini
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   ```

2. **Create a Python virtual environment**

   ```sh
      python -m venv .venv
      . ./.venv/Scripts/activate
      # use command deactivate to get out of the venv when you want
   ```

3. **Install poetry**
   Install the poetry package manager for python. [See how](https://python-poetry.org/docs/#installing-with-the-official-installer).

  If that method doesn't work, do the following:

  ```sh
    #make sure the Python venv is running (you should see `(.venv)` in your terminal above or next to the command line)
    cd backend/lang-graph-service
    python -m pip install poetry
    python -m poetry install
  ```

1. **Install dependencies for runtime and backend**

   Open a new terminal tab (or shell) for each service.

   **CopilotKit Runtime:**

   ```sh
      cd ../copilot-runtime-service && npm install
      npm run dev
   ```

   **Backend (FastAPI with LangGraph and CopilotKit):**

   ```sh
      cd ../lang-graph-service && poetry install
      npm run dev
   ```

   **MongoDB (must have Docker desktop running):**

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

- Copilot runtime: http://localhost:4000/copilotkit
- LangGraph agent: http://localhost:8000/copilotkit

## License

MIT
