#!/usr/bin/env python3
"""
MCP Server for Twilio Call Agent
Provides tools for call handling, conversation management, and AI-powered responses.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from fastmcp import FastMCP
import httpx
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("twilio-call-agent", host="0.0.0.0", port=8000)

# Storage for active call sessions
active_calls: Dict[str, dict] = {}

# Initialize Twilio client
twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)


@mcp.tool()
def initialize_call_session(call_sid: str, caller_number: str, called_number: str) -> dict:
    """
    Initialize a new call session with tracking and conversation history.

    Args:
        call_sid: Twilio call SID identifier
        caller_number: Phone number of the caller
        called_number: Phone number that was called

    Returns:
        Dictionary with session information
    """
    session = {
        "call_sid": call_sid,
        "caller_number": caller_number,
        "called_number": called_number,
        "start_time": datetime.now().isoformat(),
        "conversation_history": [],
        "status": "active",
        "ultravox_call_id": None,
    }

    active_calls[call_sid] = session

    return {
        "success": True,
        "message": f"Call session initialized for {call_sid}",
        "session": session,
    }


@mcp.tool()
def add_message_to_conversation(call_sid: str, role: str, content: str) -> dict:
    """
    Add a message to the call conversation history.

    Args:
        call_sid: Twilio call SID identifier
        role: Role of the speaker (user, assistant, or system)
        content: Message content

    Returns:
        Dictionary with success status and updated history
    """
    if call_sid not in active_calls:
        return {
            "success": False,
            "error": f"Call session {call_sid} not found",
        }

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }

    active_calls[call_sid]["conversation_history"].append(message)

    return {
        "success": True,
        "message": "Message added to conversation",
        "conversation_length": len(active_calls[call_sid]["conversation_history"]),
    }


@mcp.tool()
def get_conversation_history(call_sid: str) -> dict:
    """
    Get the full conversation history for a call.

    Args:
        call_sid: Twilio call SID identifier

    Returns:
        Dictionary with conversation history
    """
    if call_sid not in active_calls:
        return {
            "success": False,
            "error": f"Call session {call_sid} not found",
            "history": [],
        }

    return {
        "success": True,
        "call_sid": call_sid,
        "history": active_calls[call_sid]["conversation_history"],
    }


@mcp.tool()
async def create_ultravox_session(call_sid: str, system_prompt: str) -> dict:
    """
    Create an Ultravox real-time voice session for the call.

    Args:
        call_sid: Twilio call SID identifier
        system_prompt: System prompt for the AI agent

    Returns:
        Dictionary with Ultravox session information
    """
    if call_sid not in active_calls:
        return {
            "success": False,
            "error": f"Call session {call_sid} not found",
        }

    ultravox_api_key = os.getenv("ULTRAVOX_API_KEY")
    ultravox_base_url = os.getenv("ULTRAVOX_BASE_URL", "https://api.ultravox.ai")

    if not ultravox_api_key:
        return {
            "success": False,
            "error": "ULTRAVOX_API_KEY not configured",
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ultravox_base_url}/calls",
                headers={
                    "Authorization": f"Bearer {ultravox_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "systemPrompt": system_prompt,
                    "model": "fixie-ai/ultravox",
                    "voice": "terrence",
                    "temperature": 0.7,
                    "firstSpeaker": "agent",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                active_calls[call_sid]["ultravox_call_id"] = data.get("callId")
                active_calls[call_sid]["ultravox_join_url"] = data.get("joinUrl")

                return {
                    "success": True,
                    "call_id": data.get("callId"),
                    "join_url": data.get("joinUrl"),
                    "status": data.get("status"),
                }
            else:
                return {
                    "success": False,
                    "error": f"Ultravox API error: {response.status_code}",
                    "details": response.text,
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create Ultravox session: {str(e)}",
        }


@mcp.tool()
def get_call_session(call_sid: str) -> dict:
    """
    Get complete information about a call session.

    Args:
        call_sid: Twilio call SID identifier

    Returns:
        Dictionary with complete session information
    """
    if call_sid not in active_calls:
        return {
            "success": False,
            "error": f"Call session {call_sid} not found",
        }

    return {
        "success": True,
        "session": active_calls[call_sid],
    }


@mcp.tool()
def end_call_session(call_sid: str) -> dict:
    """
    End a call session and cleanup resources.

    Args:
        call_sid: Twilio call SID identifier

    Returns:
        Dictionary with cleanup status
    """
    if call_sid not in active_calls:
        return {
            "success": False,
            "error": f"Call session {call_sid} not found",
        }

    session = active_calls[call_sid]
    session["status"] = "completed"
    session["end_time"] = datetime.now().isoformat()

    # Archive session (in production, save to database)
    completed_session = active_calls.pop(call_sid)

    return {
        "success": True,
        "message": f"Call session {call_sid} ended",
        "duration": completed_session.get("end_time"),
        "message_count": len(completed_session["conversation_history"]),
    }


@mcp.tool()
def list_active_calls() -> dict:
    """
    List all currently active call sessions.

    Returns:
        Dictionary with list of active calls
    """
    return {
        "success": True,
        "active_calls": list(active_calls.keys()),
        "count": len(active_calls),
        "sessions": [
            {
                "call_sid": sid,
                "caller": session["caller_number"],
                "start_time": session["start_time"],
                "status": session["status"],
            }
            for sid, session in active_calls.items()
        ],
    }


@mcp.tool()
def get_system_prompt() -> str:
    """
    Get the default system prompt for the AI voice agent.

    Returns:
        System prompt string
    """
    return """You are a helpful voice assistant handling phone calls. You should:
- Respond naturally and conversationally
- Keep responses concise (2-3 sentences) for voice interaction
- Be friendly and professional
- Ask clarifying questions when needed
- Provide helpful information

When a call starts, greet the caller warmly and ask how you can help them today."""


@mcp.tool()
async def send_twilio_sms(to_number: str, from_number: str, message: str) -> dict:
    """
    Send an SMS message via Twilio.

    Args:
        to_number: Recipient phone number
        from_number: Twilio phone number to send from
        message: SMS message content

    Returns:
        Dictionary with SMS send status
    """
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send SMS: {str(e)}",
        }


@mcp.tool()
def get_call_analytics(call_sid: str) -> dict:
    """
    Get analytics and metrics for a call session.

    Args:
        call_sid: Twilio call SID identifier

    Returns:
        Dictionary with call analytics
    """
    if call_sid not in active_calls:
        return {
            "success": False,
            "error": f"Call session {call_sid} not found",
        }

    session = active_calls[call_sid]
    history = session["conversation_history"]

    user_messages = [msg for msg in history if msg["role"] == "user"]
    assistant_messages = [msg for msg in history if msg["role"] == "assistant"]

    return {
        "success": True,
        "analytics": {
            "call_sid": call_sid,
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "start_time": session["start_time"],
            "has_ultravox": session["ultravox_call_id"] is not None,
        },
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MCP Server: Twilio Call Agent")
    print("=" * 60)
    print(f"Starting MCP server on port 8000 with SSE transport...")
    print(f"Available tools: {len(mcp.list_tools())}")
    print("=" * 60)
    mcp.run(transport="sse")
