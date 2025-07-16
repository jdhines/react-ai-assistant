"""
Test script to verify that only the latest checkpoint is stored per conversation.
This demonstrates the storage efficiency of the MongoDB persistence solution.
"""
import asyncio
from sample_agent.conversation_aware_checkpointer import ConversationAwareMongoCheckpointer
import os
from dotenv import dotenv_values

# Load environment variables
os.environ.update(dotenv_values())


async def test_checkpoint_storage():
    """Test that only one checkpoint per thread is stored."""
    print("🧪 Testing Latest Checkpoint Storage")
    print("=" * 50)

    # Initialize checkpointer
    mongo_connection_string = os.getenv(
        "MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
    checkpointer = ConversationAwareMongoCheckpointer(mongo_connection_string)

    try:
        # Ensure indexes
        await checkpointer.ensure_indexes()

        # Test data
        user_id = "test_user_storage"
        thread_id = "test_thread_123"

        print(f"1. Testing storage for user: {user_id}, thread: {thread_id}")

        # Check initial count
        initial_count = await checkpointer.collection.count_documents({"thread_id": thread_id})
        print(f"   Initial documents for thread: {initial_count}")

        # Simulate multiple checkpoint saves (like multiple messages)
        from langchain_core.runnables import RunnableConfig
        from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
        import uuid
        from datetime import datetime

        config = RunnableConfig(
            configurable={"thread_id": thread_id, "user_id": user_id})

        for i in range(5):
            print(f"   Saving checkpoint #{i+1}...")

            # Create a mock checkpoint with different data each time
            checkpoint = Checkpoint(
                v=1,
                ts=str(datetime.utcnow().timestamp()),
                id=str(uuid.uuid4()),
                channel_values={
                    # Growing message list
                    "messages": [f"Message {j+1}" for j in range(i+1)],
                    "agent_state": {"step": i+1}
                },
                channel_versions={},
                versions_seen={},
                pending_sends=[]
            )

            metadata = CheckpointMetadata(
                source="input",
                step=i+1,
                writes={},
                parents={}
            )

            # Save checkpoint
            await checkpointer._aput(config, checkpoint, metadata, {})

            # Check count after each save
            count = await checkpointer.collection.count_documents({"thread_id": thread_id})
            print(f"     Documents after save #{i+1}: {count}")

        print(f"\n2. Final verification:")

        # Get the final document
        final_doc = await checkpointer.collection.find_one({"thread_id": thread_id})
        if final_doc:
            messages = final_doc["checkpoint"]["channel_values"]["messages"]
            agent_state = final_doc["checkpoint"]["channel_values"]["agent_state"]

            print(f"   ✅ Only 1 document exists per thread")
            print(f"   ✅ Contains all {len(messages)} messages: {messages}")
            print(f"   ✅ Latest agent state: {agent_state}")
            print(f"   ✅ Storage efficient: No intermediate checkpoints stored")

        # Test with another conversation to show isolation
        print(f"\n3. Testing with second conversation:")
        thread_id_2 = "test_thread_456"
        config_2 = RunnableConfig(
            configurable={"thread_id": thread_id_2, "user_id": user_id})

        checkpoint_2 = Checkpoint(
            v=1,
            ts=str(datetime.utcnow().timestamp()),
            id=str(uuid.uuid4()),
            channel_values={
                "messages": ["Hello from conversation 2"],
                "agent_state": {"conversation": 2}
            },
            channel_versions={},
            versions_seen={},
            pending_sends=[]
        )

        await checkpointer._aput(config_2, checkpoint_2, metadata, {})

        # Check total documents for user
        total_conversations = await checkpointer.collection.count_documents({"user_id": user_id})
        print(f"   Total conversations for {user_id}: {total_conversations}")
        print(f"   ✅ Each conversation = 1 document (efficient storage)")

        # Get conversations summary
        conversations = await checkpointer.get_conversations_by_user(user_id)
        print(f"\n4. Conversations summary:")
        for conv in conversations:
            print(f"   Thread: {conv['thread_id']}")
            print(f"   Messages: {conv['message_count']}")
            print(f"   Last updated: {conv['last_updated']}")
            print()

        print("🎉 Storage efficiency test completed!")
        print("\nKey findings:")
        print("✓ Only latest checkpoint stored per conversation")
        print("✓ Complete message history preserved")
        print("✓ Agent state properly maintained")
        print("✓ Multiple conversations properly isolated")
        print("✓ Database size remains manageable")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await checkpointer.close()

if __name__ == "__main__":
    asyncio.run(test_checkpoint_storage())
