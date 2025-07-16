"""
Custom MongoDB checkpointer for LangGraph that saves conversation state as documents.
This allows for easy querying and retrieval of chat conversations by user_id.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class MongoCheckpointSaver(BaseCheckpointSaver):
    """MongoDB-based checkpoint saver for LangGraph conversations."""

    def __init__(self, connection_string: str, database_name: str = "chatdb", collection_name: str = "conversations"):
        """
        Initialize MongoDB checkpointer.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection to store checkpoints
        """
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[database_name]
        self.collection: AsyncIOMotorCollection = self.db[collection_name]

    async def ensure_indexes(self):
        """Create indexes for efficient querying."""
        # One document per thread_id (unique)
        await self.collection.create_index([("thread_id", 1)], unique=True)
        # Index for user-based queries
        await self.collection.create_index([("user_id", 1)])
        # Index for time-based queries (session restoration)
        await self.collection.create_index([("updated_at", -1)])
        # Compound index for user + time queries
        await self.collection.create_index([("user_id", 1), ("updated_at", -1)])

    def get(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get the latest checkpoint for a thread (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._aget(config))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self._aget(config))

    def aget(self, config: RunnableConfig):
        """Get the latest checkpoint for a thread (async)."""
        return self._aget(config)

    async def _aget(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async implementation of get."""
        thread_id = config["configurable"]["thread_id"]

        # Find the latest checkpoint for this thread
        doc = await self.collection.find_one(
            {"thread_id": thread_id},
            sort=[("checkpoint_ns", -1)]
        )

        if not doc:
            return None

        checkpoint = Checkpoint(
            v=doc["checkpoint"]["v"],
            ts=doc["checkpoint"]["ts"],
            id=doc["checkpoint"]["id"],
            channel_values=doc["checkpoint"]["channel_values"],
            channel_versions=doc["checkpoint"]["channel_versions"],
            versions_seen=doc["checkpoint"]["versions_seen"],
            pending_sends=doc["checkpoint"]["pending_sends"]
        )

        metadata = CheckpointMetadata(
            source=doc["metadata"].get("source", "input"),
            step=doc["metadata"].get("step", -1),
            writes=doc["metadata"].get("writes", {}),
            parents=doc["metadata"].get("parents", {})
        )

        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=doc.get("parent_config")
        )

    def list(self, config: RunnableConfig, *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> List[CheckpointTuple]:
        """List checkpoints for a thread (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._alist(config, filter=filter, before=before, limit=limit))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self._alist(config, filter=filter, before=before, limit=limit))

    def alist(self, config: RunnableConfig, *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None):
        """List checkpoints for a thread (async)."""
        return self._alist(config, filter=filter, before=before, limit=limit)

    async def _alist(self, config: RunnableConfig, *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> List[CheckpointTuple]:
        """Async implementation of list."""
        thread_id = config["configurable"]["thread_id"]

        query = {"thread_id": thread_id}
        if filter:
            query.update(filter)

        sort_order = [("checkpoint_ns", -1)]

        cursor = self.collection.find(query).sort(sort_order)
        if limit:
            cursor = cursor.limit(limit)

        checkpoints = []
        async for doc in cursor:
            checkpoint = Checkpoint(
                v=doc["checkpoint"]["v"],
                ts=doc["checkpoint"]["ts"],
                id=doc["checkpoint"]["id"],
                channel_values=doc["checkpoint"]["channel_values"],
                channel_versions=doc["checkpoint"]["channel_versions"],
                versions_seen=doc["checkpoint"]["versions_seen"],
                pending_sends=doc["checkpoint"]["pending_sends"]
            )

            metadata = CheckpointMetadata(
                source=doc["metadata"].get("source", "input"),
                step=doc["metadata"].get("step", -1),
                writes=doc["metadata"].get("writes", {}),
                parents=doc["metadata"].get("parents", {})
            )

            checkpoints.append(CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=doc.get("parent_config")
            ))

        return checkpoints

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Dict[str, Any]) -> RunnableConfig:
        """Save a checkpoint (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._aput(config, checkpoint, metadata, new_versions))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self._aput(config, checkpoint, metadata, new_versions))

    def aput(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Dict[str, Any]):
        """Save a checkpoint (async)."""
        return self._aput(config, checkpoint, metadata, new_versions)

    async def _aput(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Dict[str, Any]) -> RunnableConfig:
        """Async implementation of put - saves only the latest checkpoint per thread."""
        thread_id = config["configurable"]["thread_id"]
        user_id = config["configurable"].get("user_id")

        # Create document to store - this will replace the entire conversation state
        doc = {
            "thread_id": thread_id,
            "user_id": user_id,
            "checkpoint_id": checkpoint.id,
            "checkpoint_ns": checkpoint.ts,
            "checkpoint": {
                "v": checkpoint.v,
                "ts": checkpoint.ts,
                "id": checkpoint.id,
                "channel_values": checkpoint.channel_values,
                "channel_versions": checkpoint.channel_versions,
                "versions_seen": checkpoint.versions_seen,
                "pending_sends": checkpoint.pending_sends
            },
            "metadata": {
                "source": metadata.source,
                "step": metadata.step,
                "writes": metadata.writes,
                "parents": metadata.parents
            },
            "new_versions": new_versions,
            "updated_at": datetime.utcnow()
        }

        # Set created_at only for new documents
        existing_doc = await self.collection.find_one({"thread_id": thread_id})
        if not existing_doc:
            doc["created_at"] = datetime.utcnow()

        # Replace the entire conversation document (only one per thread_id)
        await self.collection.replace_one(
            {"thread_id": thread_id},
            doc,
            upsert=True
        )

        return config

    async def get_conversations_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all conversations for a specific user."""
        # Simple query since we only have one document per conversation
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).limit(limit)

        conversations = []
        async for doc in cursor:
            # Get message count from the checkpoint data
            messages = doc.get("checkpoint", {}).get(
                "channel_values", {}).get("messages", [])
            first_message = messages[0] if messages else None

            conversations.append({
                "thread_id": doc["thread_id"],
                "user_id": doc["user_id"],
                "last_updated": doc["updated_at"],
                "message_count": len(messages),
                "messages": messages,
                "first_message_preview": first_message
            })

        return conversations

    async def delete_conversation(self, thread_id: str, user_id: str) -> bool:
        """Delete all checkpoints for a conversation."""
        result = await self.collection.delete_many({
            "thread_id": thread_id,
            "user_id": user_id
        })
        return result.deleted_count > 0

    async def close(self):
        """Close the MongoDB connection."""
        self.client.close()

    async def get_recent_active_conversation(self, user_id: str, hours_threshold: int = 3) -> Optional[str]:
        """
        Get the most recent active conversation for a user within the specified hours threshold.

        Args:
            user_id: The user ID to search for
            hours_threshold: Number of hours to look back for recent activity (default: 3)

        Returns:
            thread_id of the most recent active conversation, or None if no recent conversation found
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        # Find the most recent conversation that has activity within the threshold
        doc = await self.collection.find_one(
            {
                "user_id": user_id,
                "updated_at": {"$gte": cutoff_time}
            },
            sort=[("updated_at", -1)]
        )

        return doc["thread_id"] if doc else None
