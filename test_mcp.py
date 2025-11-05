#!/usr/bin/env python3
"""
Test script for MCP Server and Client
Demonstrates how to use the MCP architecture for call handling.
"""

import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_openai import ChatOpenAI

load_dotenv()


async def test_mcp_connection():
    """Test connection to MCP server and call tools."""
    print("=" * 60)
    print("🧪 Testing MCP Server Connection")
    print("=" * 60)

    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
    print(f"\n📡 Connecting to: {mcp_server_url}")

    try:
        async with sse_client(mcp_server_url) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                print("✓ Session initialized")

                # List available tools
                tools = await session.list_tools()
                print(f"\n📋 Available Tools ({len(tools.tools)}):")
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description}")

                # Test: Initialize a call session
                print("\n🧪 Test 1: Initialize Call Session")
                result = await session.call_tool(
                    "initialize_call_session",
                    arguments={
                        "call_sid": "TEST_CALL_12345",
                        "caller_number": "+1234567890",
                        "called_number": "+0987654321",
                    }
                )
                print(f"✓ Result: {result.content[0].text if result.content else 'No content'}")

                # Test: Get system prompt
                print("\n🧪 Test 2: Get System Prompt")
                result = await session.call_tool("get_system_prompt", arguments={})
                prompt = result.content[0].text if result.content else ""
                print(f"✓ System Prompt: {prompt[:100]}...")

                # Test: Add message to conversation
                print("\n🧪 Test 3: Add Message to Conversation")
                result = await session.call_tool(
                    "add_message_to_conversation",
                    arguments={
                        "call_sid": "TEST_CALL_12345",
                        "role": "user",
                        "content": "Hello, I need help with my account.",
                    }
                )
                print(f"✓ Result: {result.content[0].text if result.content else 'No content'}")

                # Test: Get conversation history
                print("\n🧪 Test 4: Get Conversation History")
                result = await session.call_tool(
                    "get_conversation_history",
                    arguments={"call_sid": "TEST_CALL_12345"}
                )
                print(f"✓ Result: {result.content[0].text if result.content else 'No content'}")

                # Test: List active calls
                print("\n🧪 Test 5: List Active Calls")
                result = await session.call_tool("list_active_calls", arguments={})
                print(f"✓ Result: {result.content[0].text if result.content else 'No content'}")

                # Test: Get call analytics
                print("\n🧪 Test 6: Get Call Analytics")
                result = await session.call_tool(
                    "get_call_analytics",
                    arguments={"call_sid": "TEST_CALL_12345"}
                )
                print(f"✓ Result: {result.content[0].text if result.content else 'No content'}")

                # Test: End call session
                print("\n🧪 Test 7: End Call Session")
                result = await session.call_tool(
                    "end_call_session",
                    arguments={"call_sid": "TEST_CALL_12345"}
                )
                print(f"✓ Result: {result.content[0].text if result.content else 'No content'}")

                print("\n" + "=" * 60)
                print("✅ All tests passed!")
                print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the MCP server is running:")
        print("  python mcp_server.py")


async def test_openai_integration():
    """Test OpenAI integration with conversation."""
    print("\n" + "=" * 60)
    print("🧪 Testing OpenAI Integration")
    print("=" * 60)

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test conversation
    messages = [
        {
            "role": "system",
            "content": "You are a helpful voice assistant. Keep responses concise (2-3 sentences)."
        },
        {
            "role": "user",
            "content": "Hello, I need help with my account."
        }
    ]

    print("\n💬 Conversation:")
    print(f"  User: {messages[1]['content']}")

    response = await model.ainvoke(messages)
    print(f"  Assistant: {response.content}")

    print("\n✅ OpenAI integration working!")


if __name__ == "__main__":
    print("\n🎯 Starting MCP Tests\n")

    # Run tests
    asyncio.run(test_mcp_connection())
    asyncio.run(test_openai_integration())

    print("\n✅ All tests completed!")
