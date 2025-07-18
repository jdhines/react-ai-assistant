"""
CosmosDB checkpointer that follows our conversation-centric model while using CosmosDB.
This combines your colleague's CosmosDB implementation with our conversation management features.
"""
import json
import logging
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator, Sequence
from azure.cosmos.aio import CosmosClient, DatabaseProxy
from azure.identity import DefaultAzureCredential
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    get_checkpoint_id
)
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CheckpointerConfig(BaseModel):
    """Configuration for the CosmosDB checkpointer."""
    DATABASE: str = "chat_assistant"
    ENDPOINT: str
    CONVERSATIONS_CONTAINER: str = "conversations"
    CHECKPOINTS_CONTAINER: str = "checkpoints"
    CHECKPOINT_WRITES_CONTAINER: str = "checkpoint_writes"


def serialize_for_cosmosdb(obj: Any) -> Any:
    """
    Recursively serialize objects for CosmosDB storage.
    Handles LangChain messages and other complex objects that can't be directly stored in CosmosDB.
    """
    if hasattr(obj, '__dict__'):
        # If it's a complex object (like LangChain messages), convert to dict
        if hasattr(obj, 'content') and hasattr(obj, 'type'):
            # LangChain message object
            return {
                "_type": obj.__class__.__name__,
                "content": obj.content,
                "type": obj.type,
                "additional_kwargs": getattr(obj, 'additional_kwargs', {}),
                "response_metadata": getattr(obj, 'response_metadata', {}),
                "id": getattr(obj, 'id', None)
            }
        else:
            # General object serialization
            result = {"_type": obj.__class__.__name__}
            result.update({k: serialize_for_cosmosdb(v)
                          for k, v in obj.__dict__.items()})
            return result
    elif isinstance(obj, dict):
        return {k: serialize_for_cosmosdb(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_cosmosdb(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        # For any other type, try to convert to string as a fallback
        try:
            return str(obj)
        except Exception:
            return f"<unserializable: {type(obj).__name__}>"


def deserialize_from_cosmosdb(obj: Any) -> Any:
    """
    Recursively deserialize objects from CosmosDB storage.
    Reconstructs LangChain messages and other complex objects from serialized format.
    """
    if isinstance(obj, dict) and "_type" in obj:
        obj_type = obj["_type"]
        if obj_type in ["HumanMessage", "AIMessage", "SystemMessage"]:
            # Reconstruct LangChain message
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
            message_classes = {
                "HumanMessage": HumanMessage,
                "AIMessage": AIMessage,
                "SystemMessage": SystemMessage
            }
            message_class = message_classes.get(obj_type, HumanMessage)
            return message_class(
                content=obj.get("content", ""),
                additional_kwargs=obj.get("additional_kwargs", {}),
                response_metadata=obj.get("response_metadata", {}),
                id=obj.get("id")
            )
        else:
            # General object reconstruction (return as dict for now)
            result = {k: deserialize_from_cosmosdb(
                v) for k, v in obj.items() if k != "_type"}
            return result
    elif isinstance(obj, dict):
        return {k: deserialize_from_cosmosdb(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deserialize_from_cosmosdb(item) for item in obj]
    elif isinstance(obj, str):
        # Try to parse ISO datetime strings
        if len(obj) > 10 and 'T' in obj and obj.endswith('Z') or '+' in obj[-6:]:
            try:
                return datetime.fromisoformat(obj.replace('Z', '+00:00'))
            except ValueError:
                pass
        return obj
    else:
        return obj


class Checkpointer(BaseCheckpointSaver):
    """
    CosmosDB checkpointer optimized for chat applications with conversation management.

    Key Features:
    - One conversation per user (single conversation model)
    - Session restoration capabilities
    - Efficient querying for conversation management
    - Compatible with LangGraph checkpointing
    """

    def __init__(self, endpoint: str, credential=None, config: CheckpointerConfig = None):
        super().__init__()

        if config is None:
            config = CheckpointerConfig(ENDPOINT=endpoint)

        self.config = config

        # Initialize CosmosDB client
        if credential is None:
            credential = DefaultAzureCredential()

        # Check if credential is a connection string
        if isinstance(credential, str) and credential.startswith("AccountEndpoint="):
            # Parse connection string for CosmosDB emulator
            parts = {}
            for part in credential.split(';'):
                if '=' in part:
                    key, value = part.split('=', 1)
                    parts[key] = value

            # Extract endpoint and key from connection string
            endpoint_url = parts.get('AccountEndpoint', config.ENDPOINT)
            account_key = parts.get('AccountKey')

            if account_key:
                # Use the account key from connection string
                self.client = CosmosClient(
                    url=endpoint_url, credential=account_key)
            else:
                raise ValueError(
                    "Connection string must contain AccountKey for authentication")
        else:
            # It's a credential object or regular endpoint/key
            self.client = CosmosClient(
                url=config.ENDPOINT, credential=credential)

        self.db = self.client.get_database_client(config.DATABASE)

        # Get containers
        self.conversations_container = self.db.get_container_client(
            config.CONVERSATIONS_CONTAINER)
        self.checkpoints_container = self.db.get_container_client(
            config.CHECKPOINTS_CONTAINER)
        self.writes_container = self.db.get_container_client(
            config.CHECKPOINT_WRITES_CONTAINER)

    async def ensure_indexes(self):
        """Ensure database and containers exist in CosmosDB."""
        try:
            # Create database if it doesn't exist
            await self.client.create_database_if_not_exists(
                id=self.config.DATABASE
            )

            # For CosmosDB emulator, we need to use proper partition key specification
            from azure.cosmos import PartitionKey

            # Create containers if they don't exist
            await self.db.create_container_if_not_exists(
                id=self.config.CONVERSATIONS_CONTAINER,
                partition_key=PartitionKey(path="/userId")
            )

            await self.db.create_container_if_not_exists(
                id=self.config.CHECKPOINTS_CONTAINER,
                partition_key=PartitionKey(path="/thread_id")
            )

            await self.db.create_container_if_not_exists(
                id=self.config.CHECKPOINT_WRITES_CONTAINER,
                partition_key=PartitionKey(path="/thread_id")
            )

            logger.info(
                f"Database '{self.config.DATABASE}' and containers created/verified successfully")

        except Exception as e:
            logger.error(f"Error creating database/containers: {e}")
            raise

    async def close(self):
        """Close the CosmosDB client."""
        await self.client.close()

    # LangGraph checkpoint methods (adapted from your colleague's implementation)
    def dumps_typed(self, obj: Any) -> Tuple[str, str]:
        """Serializes an object and encodes the serialized data in base64 format."""
        type_, serialized_ = self.serde.dumps_typed(obj)
        return type_, base64.b64encode(serialized_).decode("utf-8")

    def loads_typed(self, data: Tuple[str, str]) -> Any:
        """Deserialize a tuple containing a string and a base64 encoded string."""
        return self.serde.loads_typed((data[0], base64.b64decode(data[1].encode("utf-8"))))

    def dumps(self, obj: Any) -> str:
        """Serializes an object to a base64-encoded string."""
        return base64.b64encode(self.serde.dumps(obj)).decode("utf-8")

    def loads(self, data: str) -> Any:
        """Deserialize a base64 encoded string into a Python object."""
        return self.serde.loads(base64.b64decode(data.encode("utf-8")))

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple from the database."""
        assert "configurable" in config
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        if checkpoint_id := get_checkpoint_id(config):
            query = f"SELECT * FROM c WHERE c.thread_id = '{thread_id}' AND c.checkpoint_ns = '{checkpoint_ns}' AND c.checkpoint_id = '{checkpoint_id}'"
        else:
            query = f"SELECT * FROM c WHERE c.thread_id = '{thread_id}' AND c.checkpoint_ns = '{checkpoint_ns}' ORDER BY c.checkpoint_id DESC"

        result = [item async for item in self.checkpoints_container.query_items(query)]
        if result:
            doc = result[0]
            config_values = {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": doc["checkpoint_id"],
            }
            checkpoint = self.loads_typed((doc["type"], doc["checkpoint"]))

            _serialized_writes = self.writes_container.query_items(
                f"SELECT * FROM c WHERE c.thread_id = '{thread_id}' AND c.checkpoint_ns = '{checkpoint_ns}' AND c.checkpoint_id = '{doc['checkpoint_id']}'"
            )
            serialized_writes = [writes async for writes in _serialized_writes]

            pending_writes = [
                (
                    write_doc["task_id"],
                    write_doc["channel"],
                    self.loads_typed((write_doc["type"], write_doc["value"])),
                )
                for write_doc in serialized_writes
            ]
            return CheckpointTuple(
                {"configurable": config_values},
                checkpoint,
                self.loads(doc["metadata"]),
                (
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": doc["parent_checkpoint_id"],
                        }
                    }
                    if doc.get("parent_checkpoint_id")
                    else None
                ),
                pending_writes,
            )

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints from the database."""
        query = "SELECT * FROM c"
        if config is not None:
            assert "configurable" in config
            query += f" WHERE c.thread_id = '{config['configurable']['thread_id']}' AND c.checkpoint_ns = '{config['configurable'].get('checkpoint_ns', '')}'"

        if filter:
            for key, value in filter.items():
                query += f" AND c.metadata.{key} = '{value}'"

        if before is not None:
            assert "configurable" in before
            query += f" AND c.checkpoint_id < '{before['configurable']['checkpoint_id']}'"

        query += " ORDER BY c.checkpoint_id DESC"

        if limit is not None:
            query += f" OFFSET 0 LIMIT {limit}"

        result = self.checkpoints_container.query_items(query)

        async for doc in result:
            checkpoint = self.loads_typed((doc["type"], doc["checkpoint"]))
            yield CheckpointTuple(
                {
                    "configurable": {
                        "thread_id": doc["thread_id"],
                        "checkpoint_ns": doc["checkpoint_ns"],
                        "checkpoint_id": doc["checkpoint_id"],
                    }
                },
                checkpoint,
                self.loads(doc["metadata"]),
                (
                    {
                        "configurable": {
                            "thread_id": doc["thread_id"],
                            "checkpoint_ns": doc["checkpoint_ns"],
                            "checkpoint_id": doc["parent_checkpoint_id"],
                        }
                    }
                    if doc.get("parent_checkpoint_id")
                    else None
                ),
            )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to the database."""
        assert "configurable" in config
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = checkpoint["id"]
        type_, serialized_checkpoint = self.dumps_typed(checkpoint)

        doc = {
            "id": f"{thread_id}_{checkpoint_ns}_{checkpoint_id}",
            "parent_checkpoint_id": config["configurable"].get("checkpoint_id"),
            "type": type_,
            "checkpoint": serialized_checkpoint,
            "metadata": self.dumps(metadata),
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
        }
        await self.checkpoints_container.upsert_item(body=doc)

        # Also update/create conversation document for our conversation management
        await self._update_conversation_document(config, checkpoint, metadata)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Store intermediate writes linked to a checkpoint."""
        assert "configurable" in config
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = config["configurable"]["checkpoint_id"]

        for idx, (channel, value) in enumerate(writes):
            type_, serialized_value = self.dumps_typed(value)
            doc = {
                "id": f"{thread_id}_{checkpoint_ns}_{checkpoint_id}_{task_id}_{idx}",
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "idx": idx,
                "channel": channel,
                "type": type_,
                "value": serialized_value,
            }
            await self.writes_container.upsert_item(body=doc)

    # Conversation management methods (preserved from our MongoDB implementation)
    async def _update_conversation_document(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata):
        """Update the conversation document for conversation management."""
        thread_id = config["configurable"]["thread_id"]

        # Extract user_id from the LangGraph config (passed when creating the conversation)
        user_id = config["configurable"].get("user_id")

        if not user_id:
            logger.warning(
                f"No user_id found in config for thread_id: {thread_id}")
            return  # Skip if we can't extract user_id

        logger.info(
            f"Updating conversation document for user_id: {user_id}, thread_id: {thread_id}")

        # Get messages from checkpoint
        messages = []
        if 'channel_values' in checkpoint and 'messages' in checkpoint['channel_values']:
            messages = checkpoint['channel_values']['messages']

        # Serialize messages for CosmosDB storage
        serialized_messages = serialize_for_cosmosdb(messages)

        now = datetime.utcnow()

        # Create or update conversation document
        conversation_doc = {
            "id": thread_id,
            "userId": user_id,
            "lastUpdated": now.isoformat(),
            "messages": serialized_messages,
            "checkpointId": checkpoint["id"],
            "metadata": serialize_for_cosmosdb(metadata)
        }

        try:
            # In CosmosDB, the partition key value is automatically extracted from the document
            await self.conversations_container.upsert_item(body=conversation_doc)
            logger.info(
                f"Successfully saved conversation document for user_id: {user_id}")
        except Exception as e:
            logger.error(f"Error saving conversation document: {e}")
            raise

    async def get_conversations_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversations for a specific user."""
        query = f"SELECT * FROM c WHERE c.userId = '{user_id}' ORDER BY c.lastUpdated DESC OFFSET 0 LIMIT {limit}"
        results = []

        async for doc in self.conversations_container.query_items(query):
            # Calculate message count
            messages = doc.get("messages", [])
            message_count = len(messages) if isinstance(messages, list) else 0

            # Get first message preview
            first_message_preview = None
            if messages and isinstance(messages, list) and len(messages) > 0:
                first_msg = messages[0]
                if isinstance(first_msg, dict):
                    content = first_msg.get("content", "")
                    first_message_preview = {
                        "role": first_msg.get("type", ""),
                        "content": content[:100] + "..." if len(content) > 100 else content,
                        "timestamp": doc.get("lastUpdated", "")
                    }

            results.append({
                "thread_id": doc["id"],
                "user_id": doc["userId"],
                "last_updated": datetime.fromisoformat(doc["lastUpdated"]) if isinstance(doc["lastUpdated"], str) else doc["lastUpdated"],
                "message_count": message_count,
                "first_message_preview": first_message_preview
            })

        return results

    async def get_or_create_user_conversation(self, user_id: str) -> str:
        """Get the user's single conversation thread_id, or create one if it doesn't exist."""
        # Check if user already has a conversation
        query = f"SELECT * FROM c WHERE c.userId = '{user_id}' ORDER BY c.lastUpdated DESC OFFSET 0 LIMIT 1"
        results = [doc async for doc in self.conversations_container.query_items(query)]

        if results:
            return results[0]["id"]

        # Create a new GUID-format thread_id for this user
        import uuid
        thread_id = str(uuid.uuid4())
        return thread_id

    async def cleanup_old_conversations(self, user_id: str):
        """Clean up any extra conversations for a user, keeping only the most recent one."""
        query = f"SELECT * FROM c WHERE c.userId = '{user_id}' ORDER BY c.lastUpdated DESC"
        conversations = [doc async for doc in self.conversations_container.query_items(query)]

        if len(conversations) <= 1:
            return  # Nothing to clean up

        # Keep the most recent conversation, delete the rest
        delete_conversations = conversations[1:]

        for conv in delete_conversations:
            await self.conversations_container.delete_item(item=conv["id"], partition_key=conv["userId"])

    async def delete_conversation(self, thread_id: str) -> bool:
        """Delete a conversation and all its associated checkpoints."""
        try:
            # First, get the conversation to find the userId (needed for partition key)
            query = f"SELECT * FROM c WHERE c.id = '{thread_id}'"
            conversations = [doc async for doc in self.conversations_container.query_items(query)]

            if conversations:
                conv = conversations[0]
                # Delete conversation document (partition key is userId)
                await self.conversations_container.delete_item(item=thread_id, partition_key=conv["userId"])

            # Delete associated checkpoints (partition key is thread_id)
            query = f"SELECT * FROM c WHERE c.thread_id = '{thread_id}'"
            checkpoints = [doc async for doc in self.checkpoints_container.query_items(query)]

            for checkpoint in checkpoints:
                await self.checkpoints_container.delete_item(item=checkpoint["id"], partition_key=checkpoint["thread_id"])

            # Delete associated checkpoint writes (partition key is thread_id)
            writes = [doc async for doc in self.writes_container.query_items(query)]
            for write in writes:
                await self.writes_container.delete_item(item=write["id"], partition_key=write["thread_id"])

            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {thread_id}: {e}")
            return False

    async def get_total_conversations(self) -> int:
        """Get the total number of conversations in the database."""
        try:
            query = "SELECT VALUE COUNT(1) FROM c"
            result = [item async for item in self.conversations_container.query_items(query)]
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting total conversations count: {e}")
            return 0

    async def get_all_unique_user_ids(self) -> List[str]:
        """Get all unique user IDs from the conversations."""
        try:
            query = "SELECT DISTINCT VALUE c.userId FROM c"
            user_ids = [item async for item in self.conversations_container.query_items(query)]
            return sorted(user_ids)
        except Exception as e:
            logger.error(f"Error getting unique user IDs: {e}")
            return []

    async def get_all_unique_thread_ids(self) -> List[str]:
        """Get all unique thread IDs from the conversations."""
        try:
            query = "SELECT DISTINCT VALUE c.id FROM c"
            thread_ids = [item async for item in self.conversations_container.query_items(query)]
            return sorted(thread_ids)
        except Exception as e:
            logger.error(f"Error getting unique thread IDs: {e}")
            return []
