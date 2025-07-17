"""
This serves the "sample_agent" agent. This is an example of self-hosting an agent
through our FastAPI integration. However, you can also host in LangGraph platform.
"""
import os
import uuid
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import dotenv_values
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent, CopilotKitState
# the coagents-starter path, replace this if its different
from sample_agent.agent import workflow, AgentState
from sample_agent.cosmosdb_checkpointer import Checkpointer, CheckpointerConfig
from sample_agent.session_aware_agent import SessionAwareLangGraphAgent


os.environ.update(dotenv_values())  # Load environment variables from .env file

# Global variable to store checkpointer for API endpoints
checkpointer = None


class ConversationResponse(BaseModel):
    thread_id: str
    user_id: str
    last_updated: str
    message_count: int
    first_message_preview: Optional[Dict[str, Any]] = None


class CreateConversationRequest(BaseModel):
    user_id: str
    title: Optional[str] = None


class DatabaseSummaryResponse(BaseModel):
    total_conversations: int
    unique_users: List[str]
    unique_thread_ids: List[str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler to set up CosmosDB persistence and CopilotKit integration."""
    global checkpointer

    # Initialize CosmosDB connection
    cosmosdb_endpoint = os.getenv("COSMOSDB_ENDPOINT")
    if not cosmosdb_endpoint:
        raise ValueError("COSMOSDB_ENDPOINT environment variable is required")

    # Optional: Use connection string instead of DefaultAzureCredential
    cosmosdb_connection_string = os.getenv("COSMOSDB_CONNECTION_STRING")

    config = CheckpointerConfig(
        DATABASE=os.getenv("COSMOSDB_DATABASE", "chat_assistant"),
        ENDPOINT=cosmosdb_endpoint,
        CONVERSATIONS_CONTAINER=os.getenv(
            "COSMOSDB_CONVERSATIONS_CONTAINER", "conversations"),
        CHECKPOINTS_CONTAINER=os.getenv(
            "COSMOSDB_CHECKPOINTS_CONTAINER", "checkpoints"),
        CHECKPOINT_WRITES_CONTAINER=os.getenv(
            "COSMOSDB_CHECKPOINT_WRITES_CONTAINER", "checkpoint_writes")
    )

    # Use connection string if provided, otherwise use DefaultAzureCredential
    if cosmosdb_connection_string:
        checkpointer = Checkpointer(
            endpoint=cosmosdb_endpoint,
            credential=cosmosdb_connection_string,
            config=config
        )
    else:
        from azure.identity import DefaultAzureCredential
        checkpointer = Checkpointer(
            endpoint=cosmosdb_endpoint,
            credential=DefaultAzureCredential(),
            config=config
        )

    # Set up indexes
    await checkpointer.ensure_indexes()

    # Create the graph with CosmosDB checkpointer
    graph = workflow.compile(checkpointer=checkpointer)

    # Use dynamic agents to access CopilotKit properties
    def create_agents(context):
        """
        Dynamic agent factory that has access to CopilotKit properties.
        This is called by CopilotKit for each request and receives context including properties.
        """

        # Extract user_id from CopilotKit properties
        user_id = None
        if 'properties' in context and context['properties']:
            user_id = context['properties'].get('user_id')

        # Create agent with user_id in config
        agent_config = {}
        if user_id:
            agent_config = {
                'configurable': {
                    'user_id': user_id
                }
            }

        return [
            SessionAwareLangGraphAgent(
                checkpointer=checkpointer,
                name="sample_agent",
                description="AI assistant with persistent conversation history using CosmosDB and automatic session restoration",
                graph=graph,
                langgraph_config=agent_config,
            )
        ]

    sdk = CopilotKitRemoteEndpoint(
        agents=create_agents
    )

    # Add the CopilotKit FastAPI endpoint
    add_fastapi_endpoint(app, sdk, "/copilotkit")

    yield

    # Cleanup on shutdown
    await checkpointer.close()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173",
                   "http://localhost:4173"],  # Common frontend dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


@app.get("/conversation-by-user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(user_id: str, limit: int = 50):
    """Get the single conversation for a specific user (new model: one conversation per user)."""
    global checkpointer
    try:
        conversations = await checkpointer.get_conversations_by_user(user_id, limit)

        # With the new model, there should be at most one conversation per user
        if len(conversations) > 1:
            # Clean up duplicates automatically
            await checkpointer.cleanup_old_conversations(user_id)
            # Fetch again after cleanup
            conversations = await checkpointer.get_conversations_by_user(user_id, limit)

        return [
            ConversationResponse(
                thread_id=conv["thread_id"],
                user_id=conv["user_id"],
                last_updated=conv["last_updated"].isoformat(),
                message_count=conv["message_count"],
                first_message_preview=conv.get("first_message_preview")
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving conversations: {str(e)}")


@app.post("/conversations", response_model=Dict[str, str])
async def create_conversation(request: CreateConversationRequest):
    """Get or create conversation for a user (new model: one conversation per user)."""
    global checkpointer
    try:
        # Get or create the user's single conversation
        thread_id = await checkpointer.get_or_create_user_conversation(request.user_id)
        return {
            "thread_id": thread_id,
            "user_id": request.user_id,
            "message": "Conversation ready"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating conversation: {str(e)}")


@app.delete("/conversations/{thread_id}")
async def delete_conversation_thread(thread_id: str):
    """Delete a conversation thread """
    global checkpointer
    try:
        # Find and delete the user's conversation (use "id" field, not "thread_id")
        # Note: In CosmosDB, we need to query the conversations container
        query = "SELECT * FROM c WHERE c.id = @thread_id"
        parameters = [{"name": "@thread_id", "value": thread_id}]
        items = [item async for item in checkpointer.conversations_container.query_items(
            query=query, parameters=parameters)]

        if not items:
            raise HTTPException(
                status_code=404, detail="Conversation not found")

        doc = items[0]
        deleted = await checkpointer.delete_conversation(doc["id"])
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting conversation: {str(e)}")


@app.get("/session/{user_id}")
async def get_session_info(user_id: str):
    """Get session information for a user (new model: always returns the user's single conversation)."""
    global checkpointer
    try:
        # Get the user's conversation (no time threshold needed)
        thread_id = await checkpointer.get_or_create_user_conversation(user_id)

        return {
            "user_id": user_id,
            "has_recent_session": True,  # Always true since we maintain one conversation per user
            "thread_id": thread_id,
            "message": "User conversation ready"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking session: {str(e)}")


@app.get("/conversation-by-id/{thread_id}", response_model=ConversationResponse)
async def get_conversation_by_thread(thread_id: str):
    """Get conversation details by thread ID."""
    global checkpointer
    try:
        # Find conversation by thread_id (which is stored as "id" in the document)
        query = "SELECT * FROM c WHERE c.id = @thread_id"
        parameters = [{"name": "@thread_id", "value": thread_id}]
        items = [item async for item in checkpointer.conversations_container.query_items(
            query=query, parameters=parameters)]

        if not items:
            raise HTTPException(
                status_code=404, detail="Conversation not found")

        doc = items[0]

        # Extract message count
        message_count = len(doc.get("messages", []))

        # Get first message preview
        first_message_preview = None
        messages = doc.get("messages", [])
        if messages:
            first_message_preview = {
                "role": messages[0].get("role", ""),
                "content": messages[0].get("content", "")[:100] + "..." if len(messages[0].get("content", "")) > 100 else messages[0].get("content", ""),
                "timestamp": messages[0].get("timestamp", "")
            }

        return ConversationResponse(
            thread_id=doc["id"],
            user_id=doc["userId"],
            last_updated=doc["lastUpdated"],  # It's already in ISO format
            message_count=message_count,
            first_message_preview=first_message_preview
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving conversation: {str(e)}")


@app.get("/database-summary", response_model=DatabaseSummaryResponse)
async def get_database_summary():
    """Get a summary of the database: total conversations, unique users, and unique thread IDs."""
    global checkpointer
    try:
        # Get the count of all conversations
        total_conversations = await checkpointer.get_total_conversations()

        # Get all unique user IDs and thread IDs
        unique_users = await checkpointer.get_all_unique_user_ids()
        unique_thread_ids = await checkpointer.get_all_unique_thread_ids()

        return DatabaseSummaryResponse(
            total_conversations=total_conversations,
            unique_users=unique_users,
            unique_thread_ids=unique_thread_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving database summary: {str(e)}")


def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "server:app",  # Updated to reference the app in this file
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
