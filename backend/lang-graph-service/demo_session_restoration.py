"""
Demo script for testing MongoDB persistence with automatic session restoration.
This demonstrates the 3-hour session restoration logic.
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


async def demo_session_restoration():
    """Demonstrate session restoration functionality."""
    print("🔄 Session Restoration Demo")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        user_id = "demo_user_123"

        # 1. Check initial session status
        print(f"\n1. Checking initial session status for user {user_id}...")
        async with session.get(f"{BASE_URL}/session/{user_id}") as response:
            if response.status == 200:
                session_info = await response.json()
                print(f"✅ Initial session status:")
                print(
                    f"   Has recent session: {session_info['has_recent_session']}")
                print(f"   Thread ID: {session_info.get('thread_id', 'None')}")
                print(f"   Message: {session_info['message']}")
            else:
                print(f"❌ Session check failed: {response.status}")
                return

        # 2. Simulate a chat interaction (this would normally go through CopilotKit)
        print(f"\n2. Simulating chat interaction...")
        print("   In real usage, CopilotKit runtime would:")
        print("   - Send user message to /copilotkit endpoint")
        print("   - Include user_id in config (no thread_id initially)")
        print("   - Our SessionAwareLangGraphAgent would automatically:")

        if session_info['has_recent_session']:
            print(
                f"     • Restore existing session: {session_info['thread_id']}")
        else:
            print("     • Create new session with UUID")

        chat_example = {
            "message": "Hello! Can you help me with something?",
            "config": {
                "configurable": {
                    "user_id": user_id
                    # Note: No thread_id provided - will be auto-managed
                }
            }
        }
        print(f"   Example payload: {json.dumps(chat_example, indent=4)}")

        # 3. Create a conversation to test restoration later
        print(f"\n3. Creating a conversation for testing...")
        async with session.post(f"{BASE_URL}/conversations",
                                json={"user_id": user_id}) as response:
            if response.status == 200:
                conv = await response.json()
                thread_id = conv["thread_id"]
                print(f"✅ Created conversation: {thread_id}")

                # Simulate adding some activity to this conversation
                # (In real usage, this would happen through CopilotKit interactions)
                print("   📝 Simulating conversation activity...")
                print(
                    "   (In production, messages would be automatically saved via MongoDB checkpointer)")

        # 4. Check session status again (should now show the new conversation)
        print(f"\n4. Checking session status after creating conversation...")
        async with session.get(f"{BASE_URL}/session/{user_id}") as response:
            if response.status == 200:
                session_info = await response.json()
                print(f"✅ Updated session status:")
                print(
                    f"   Has recent session: {session_info['has_recent_session']}")
                print(f"   Thread ID: {session_info.get('thread_id', 'None')}")
                print(f"   Message: {session_info['message']}")

        # 5. Show conversation list
        print(f"\n5. Current conversations for user {user_id}...")
        async with session.get(f"{BASE_URL}/conversations/{user_id}") as response:
            if response.status == 200:
                conversations = await response.json()
                print(f"✅ Found {len(conversations)} conversations:")
                for conv in conversations:
                    last_updated = datetime.fromisoformat(
                        conv['last_updated'].replace('Z', '+00:00'))
                    hours_ago = (datetime.now(last_updated.tzinfo) -
                                 last_updated).total_seconds() / 3600

                    print(f"   - Thread: {conv['thread_id'][:8]}...")
                    print(
                        f"     Last updated: {conv['last_updated']} ({hours_ago:.1f} hours ago)")
                    print(f"     Messages: {conv['message_count']}")

                    if hours_ago <= 3:
                        print(
                            f"     🔄 This session WILL be restored (within 3 hours)")
                    else:
                        print(
                            f"     ⏰ This session will NOT be restored (older than 3 hours)")
                    print()

        print("\n" + "=" * 50)
        print("🎉 Session Restoration Demo Complete!")
        print("\n📋 How it works:")
        print("1. When CopilotKit runtime sends a message without thread_id:")
        print("2. SessionAwareLangGraphAgent checks for recent activity (3 hours)")
        print("3. If found: Restores the existing conversation")
        print("4. If not found: Creates a new conversation thread")
        print("5. All subsequent messages in that session use the same thread_id")
        print("\n🔑 Key Benefits:")
        print("• Seamless conversation continuation")
        print("• No need for frontend to manage thread_ids")
        print("• Automatic cleanup of old sessions")
        print("• Context preservation across browser sessions")


async def demo_multiple_users():
    """Demo showing how multiple users have isolated sessions."""
    print("\n\n👥 Multiple Users Demo")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        users = ["alice_123", "bob_456", "charlie_789"]

        for user_id in users:
            print(f"\n🔍 Checking session for {user_id}...")
            async with session.get(f"{BASE_URL}/session/{user_id}") as response:
                if response.status == 200:
                    session_info = await response.json()
                    print(
                        f"   Has recent session: {session_info['has_recent_session']}")
                    if session_info['has_recent_session']:
                        print(
                            f"   Thread ID: {session_info['thread_id'][:8]}...")
                    else:
                        print("   Would create new session")

        print(f"\n✅ Each user has isolated conversation history")
        print(f"✅ Session restoration works independently per user")

if __name__ == "__main__":
    async def main():
        try:
            # Check server health first
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/health") as response:
                    if response.status != 200:
                        print("❌ Server not available. Start with: python server.py")
                        return

            await demo_session_restoration()
            await demo_multiple_users()

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            print("Make sure the server is running with: python server.py")

    asyncio.run(main())
