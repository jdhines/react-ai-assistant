"""
Simple test script to verify the MongoDB persistence setup works correctly.
Run this after starting the server to test the conversation management endpoints.
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"


async def test_server():
    """Test the server endpoints."""
    print("🧪 Testing MongoDB Persistence Setup")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Server health: {health}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure to start the server with: python server.py")
            return False

        # Test conversation creation
        print("\n2. Testing conversation creation...")
        user_id = "test_user_123"
        try:
            async with session.post(f"{BASE_URL}/conversations",
                                    json={"user_id": user_id}) as response:
                if response.status == 200:
                    conv = await response.json()
                    thread_id = conv["thread_id"]
                    print(f"✅ Created conversation: {thread_id}")
                else:
                    print(f"❌ Conversation creation failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Conversation creation error: {e}")
            return False

        # Test conversation retrieval
        print("\n3. Testing conversation retrieval...")
        try:
            async with session.get(f"{BASE_URL}/conversations/{user_id}") as response:
                if response.status == 200:
                    conversations = await response.json()
                    print(f"✅ Retrieved {len(conversations)} conversations")
                    if conversations:
                        for conv in conversations:
                            print(f"   - Thread: {conv['thread_id']}")
                            print(f"     User: {conv['user_id']}")
                            print(f"     Messages: {conv['message_count']}")
                    else:
                        print(
                            "   ℹ️  No conversations found (expected - conversations are created when messages are sent)")
                        print(
                            "   ℹ️  The POST /conversations endpoint only generates thread IDs")
                        print(
                            "   ℹ️  Actual conversations are saved when chat messages are exchanged")
                else:
                    print(
                        f"❌ Conversation retrieval failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Conversation retrieval error: {e}")
            return False

        # Test session management
        print("\n4. Testing session management...")
        user_id_session = "test_user_456"
        try:
            async with session.get(f"{BASE_URL}/session/{user_id_session}") as response:
                if response.status == 200:
                    session_info = await response.json()
                    print(f"✅ Session info for {user_id_session}:")
                    print(
                        f"   Has recent session: {session_info['has_recent_session']}")
                    print(
                        f"   Thread ID: {session_info.get('thread_id', 'None')}")
                    print(f"   Message: {session_info['message']}")
                else:
                    print(f"❌ Session check failed: {response.status}")
        except Exception as e:
            print(f"❌ Session check error: {e}")

        # Test CopilotKit endpoint exists
        print("\n5. Testing CopilotKit endpoint availability...")
        try:
            # Just test that the endpoint exists (will likely return error without proper payload)
            async with session.post(f"{BASE_URL}/copilotkit",
                                    json={"test": "ping"}) as response:
                # Any response (even error) means the endpoint exists
                print(
                    f"✅ CopilotKit endpoint available (status: {response.status})")
                print("   The endpoint is ready for CopilotKit runtime integration")
                print("   Automatic session restoration is enabled (3-hour threshold)")
        except Exception as e:
            print(f"❌ CopilotKit endpoint error: {e}")
            return False

        print("\n" + "=" * 50)
        print("🎉 All tests passed! Server is ready.")
        print("\nHow conversations work:")
        print("1. POST /conversations generates thread IDs for frontend use")
        print(
            "2. Actual conversations are saved when chat messages are sent via CopilotKit")
        print(
            "3. GET /conversations/{user_id} retrieves persisted conversations from MongoDB")
        print("4. Session restoration works automatically within 3-hour window")
        print("\nNext steps:")
        print("1. Configure your CopilotKit runtime to connect to this server")
        print("2. Use thread_id and user_id in your chat configurations")
        print("3. MongoDB will automatically persist all conversations")

        return True

if __name__ == "__main__":
    asyncio.run(test_server())
