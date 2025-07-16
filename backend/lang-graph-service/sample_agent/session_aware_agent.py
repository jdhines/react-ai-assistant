"""
Custom LangGraph agent wrapper that handles automatic session restoration
based on recent conversation activity for CopilotKit integration.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig
from copilotkit import LangGraphAgent
from .conversation_aware_checkpointer import ConversationAwareMongoCheckpointer


class SessionAwareLangGraphAgent(LangGraphAgent):
    """
    LangGraph agent that automatically handles session restoration based on recent activity.

    If a user has a conversation within the last 3 hours, it restores that session.
    Otherwise, it creates a new conversation thread.
    """

    def __init__(self, checkpointer: ConversationAwareMongoCheckpointer, hours_threshold: int = 3, **kwargs):
        """
        Initialize the session-aware agent.

        Args:
            checkpointer: MongoDB checkpointer instance
            hours_threshold: Hours to look back for recent conversations (default: 3)
            **kwargs: Other arguments passed to LangGraphAgent
        """
        print(f"🔧 Initializing SessionAwareLangGraphAgent")
        super().__init__(**kwargs)
        self.checkpointer = checkpointer
        self.hours_threshold = hours_threshold

    async def _ensure_thread_id(self, config: RunnableConfig) -> RunnableConfig:
        """
        Ensure a thread_id exists in config, either by restoring a recent session
        or creating a new one.
        """
        # Debug: Print the entire config to understand the structure
        print(f"🔍 DEBUG: Full config structure: {config}")

        configurable = config.get("configurable", {})
        print(f"🔍 DEBUG: configurable section: {configurable}")

        # Try to get user_id from different possible locations
        user_id = configurable.get("user_id")
        if not user_id:
            # Check if CopilotKit puts properties elsewhere
            user_id = config.get("user_id")
        if not user_id:
            # Check for other common property names
            user_id = configurable.get("userId")
        if not user_id:
            user_id = config.get("userId")

        print(f"🔍 DEBUG: Extracted user_id: {user_id}")

        thread_id = configurable.get("thread_id")
        print(f"🔍 DEBUG: Extracted thread_id: {thread_id}")

        # If thread_id is already provided, use it as-is
        if thread_id:
            return config

        # If no user_id provided, create a new thread
        if not user_id:
            new_thread_id = str(uuid.uuid4())
            config["configurable"] = {
                **configurable, "thread_id": new_thread_id}
            print(
                f"⚠️  No user_id found, creating anonymous session {new_thread_id[:8]}...")
            return config

        # Look for recent active conversation for this user
        recent_thread_id = await self.checkpointer.get_recent_active_conversation(
            user_id, self.hours_threshold
        )

        if recent_thread_id:
            # Restore recent session
            config["configurable"] = {
                **configurable, "thread_id": recent_thread_id, "user_id": user_id}
            print(
                f"🔄 Restoring recent session {recent_thread_id[:8]}... for user {user_id}")
        else:
            # Create new session
            new_thread_id = str(uuid.uuid4())
            config["configurable"] = {
                **configurable, "thread_id": new_thread_id, "user_id": user_id}
            print(
                f"🆕 Creating new session {new_thread_id[:8]}... for user {user_id}")

        return config

    async def ainvoke(self, input_data: Dict[str, Any], config: Optional[RunnableConfig] = None, **kwargs) -> Any:
        """
        Async invoke with automatic session management.
        """
        print(
            f"🚀 SessionAwareLangGraphAgent.ainvoke called with input_data: {input_data}")
        print(f"🚀 SessionAwareLangGraphAgent.ainvoke config: {config}")

        if config is None:
            config = {}

        # Ensure thread_id exists (restore recent or create new)
        config = await self._ensure_thread_id(config)

        # Call the parent's ainvoke method
        return await super().ainvoke(input_data, config, **kwargs)

    def invoke(self, input_data: Dict[str, Any], config: Optional[RunnableConfig] = None, **kwargs) -> Any:
        """
        Sync invoke with automatic session management.
        """
        import asyncio

        if config is None:
            config = {}

        # Handle async session management in sync context
        try:
            loop = asyncio.get_event_loop()
            config = loop.run_until_complete(self._ensure_thread_id(config))
        except RuntimeError:
            # If no event loop is running, create a new one
            config = asyncio.run(self._ensure_thread_id(config))

        # Call the parent's invoke method
        return super().invoke(input_data, config, **kwargs)

    async def astream(self, input_data: Dict[str, Any], config: Optional[RunnableConfig] = None, **kwargs):
        """
        Async stream with automatic session management.
        """
        print(
            f"🌊 SessionAwareLangGraphAgent.astream called with input_data: {input_data}")
        print(f"🌊 SessionAwareLangGraphAgent.astream config: {config}")

        if config is None:
            config = {}

        # Ensure thread_id exists (restore recent or create new)
        config = await self._ensure_thread_id(config)

        # Call the parent's astream method
        async for chunk in super().astream(input_data, config, **kwargs):
            yield chunk

    def stream(self, input_data: Dict[str, Any], config: Optional[RunnableConfig] = None, **kwargs):
        """
        Sync stream with automatic session management.
        """
        import asyncio

        if config is None:
            config = {}

        # Handle async session management in sync context
        try:
            loop = asyncio.get_event_loop()
            config = loop.run_until_complete(self._ensure_thread_id(config))
        except RuntimeError:
            # If no event loop is running, create a new one
            config = asyncio.run(self._ensure_thread_id(config))

        # Call the parent's stream method
        for chunk in super().stream(input_data, config, **kwargs):
            yield chunk
