"""
Example script demonstrating MongoDB persistence with CopilotKit + LangGraph.
This shows how to create conversations, send messages, and retrieve chat history.
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


async def example_conversation_flow():
    """Example flow showing conversation management and chat persistence."""

    async with aiohttp.ClientSession() as session:
        user_id = "user123"

        print("🚀 Starting MongoDB Persistence Demo")
        print("=" * 50)

        # 1. Create a new conversation
        print("\n1. Creating a new conversation...")
        async with session.post(f"{BASE_URL}/conversations",
                                json={"user_id": user_id}) as response:
            new_conv = await response.json()
            thread_id = new_conv["thread_id"]
            print(f"✅ Created conversation: {thread_id}")

        # 2. Send some messages to build conversation history
        print("\n2. Sending messages to build conversation history...")
        messages = [
            "Hello! I'm testing the MongoDB persistence feature.",
            "Can you tell me about the weather in New York?",
            "That's great! How about Paris?"
        ]

        for i, message in enumerate(messages, 1):
            print(f"   Sending message {i}: {message[:50]}...")

            # Simulate sending message via CopilotKit
            chat_data = {
                "message": message,
                "config": {
                    "configurable": {
                        "user_id": user_id,
                        "thread_id": thread_id
                    }
                }
            }

            # Note: In real usage, this would go through CopilotKit's endpoint
            # For demo purposes, we'll just show the structure
            print(
                f"   📨 Would send to /copilotkit: {json.dumps(chat_data, indent=2)}")

            # Simulate some delay
            await asyncio.sleep(0.5)

        # 3. Retrieve conversation history
        print(f"\n3. Retrieving conversations for user {user_id}...")
        async with session.get(f"{BASE_URL}/conversations/{user_id}") as response:
            conversations = await response.json()

            print(f"✅ Found {len(conversations)} conversations:")
            for conv in conversations:
                print(f"   - Thread: {conv['thread_id'][:8]}...")
                print(f"     Messages: {conv['message_count']}")
                print(f"     Last updated: {conv['last_updated']}")
                if conv.get('first_message_preview'):
                    preview = conv['first_message_preview']
                    print(f"     Preview: {str(preview)[:100]}...")
                print()

        # 4. Create another conversation to show multiple conversations
        print("\n4. Creating a second conversation...")
        async with session.post(f"{BASE_URL}/conversations",
                                json={"user_id": user_id}) as response:
            new_conv2 = await response.json()
            thread_id2 = new_conv2["thread_id"]
            print(f"✅ Created second conversation: {thread_id2}")

        # 5. Show updated conversation list
        print(f"\n5. Updated conversation list for user {user_id}...")
        async with session.get(f"{BASE_URL}/conversations/{user_id}") as response:
            conversations = await response.json()
            print(f"✅ Now showing {len(conversations)} conversations")

        # 6. Delete the first conversation
        print(f"\n6. Deleting first conversation {thread_id[:8]}...")
        async with session.delete(f"{BASE_URL}/conversations/{thread_id}?user_id={user_id}") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ {result['message']}")
            else:
                print(f"❌ Failed to delete: {response.status}")

        # 7. Final conversation list
        print(f"\n7. Final conversation list for user {user_id}...")
        async with session.get(f"{BASE_URL}/conversations/{user_id}") as response:
            conversations = await response.json()
            print(f"✅ Final count: {len(conversations)} conversations")

        print("\n" + "=" * 50)
        print("🎉 MongoDB Persistence Demo Complete!")
        print("\nKey Features Demonstrated:")
        print("✓ Conversation creation and management")
        print("✓ User-based conversation organization")
        print("✓ Thread-based message persistence")
        print("✓ Conversation deletion")
        print("✓ RESTful API for conversation management")


async def check_server_health():
    """Check if the server is running."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Server is healthy: {health}")
                    return True
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        print(f"   Make sure the server is running on {BASE_URL}")
        return False


if __name__ == "__main__":
    print("MongoDB Persistence Demo for CopilotKit + LangGraph")
    print("Make sure your server is running with: python server.py")
    print()

    async def main():
        # Check server health first
        if await check_server_health():
            await example_conversation_flow()
        else:
            print("\n🛑 Demo cancelled - server not available")
            print("Start the server with: python server.py")

    asyncio.run(main())
