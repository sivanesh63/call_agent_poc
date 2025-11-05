"""
Twilio MCP Server - AI Voice Agent with FastMCP

This MCP server provides Twilio call handling capabilities with OpenAI integration.
It exposes tools for managing phone calls and conversation logging via MCP protocol.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging
from dotenv import load_dotenv

from fastmcp import FastMCP
from fastapi import Request, Response
from openai import AsyncOpenAI

# ----------------------------------------------------------------------
# Load Environment Variables
# ----------------------------------------------------------------------
load_dotenv()

# ----------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("TwilioMCPServer")

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
RESPONSES_FILE = Path("conversation_logs.jsonl")

# ----------------------------------------------------------------------
# OpenAI Client Setup
# ----------------------------------------------------------------------
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ----------------------------------------------------------------------
# Conversation History (In-Memory)
# ----------------------------------------------------------------------
conversation_history: Dict[str, list] = {}

# ----------------------------------------------------------------------
# FastMCP Server Initialization
# ----------------------------------------------------------------------
mcp = FastMCP(
    name="twilio-calling-agent",
    host=HOST,
    port=PORT,
    log_level="INFO",
    stateless_http=True,
    json_response=True
)

# ----------------------------------------------------------------------
# System Prompt for AI Agent
# ----------------------------------------------------------------------
SYSTEM_PROMPT = """
You are a professional AI voice agent assisting callers.
Respond politely and concisely.
Keep replies conversational and short for voice playback (2-3 sentences max).
Maintain context across exchanges.
Be helpful, friendly, and natural in your responses.
"""

# ----------------------------------------------------------------------
# MCP Tools
# ----------------------------------------------------------------------

@mcp.tool()
async def get_conversation_history(call_sid: str) -> Dict[str, Any]:
    """
    Retrieve the conversation history for a specific call.

    Args:
        call_sid: The Twilio Call SID identifier

    Returns:
        Dictionary containing the conversation history
    """
    history = conversation_history.get(call_sid, [])
    return {
        "call_sid": call_sid,
        "messages": history,
        "message_count": len(history)
    }


@mcp.tool()
async def clear_conversation_history(call_sid: str) -> Dict[str, str]:
    """
    Clear the conversation history for a specific call.

    Args:
        call_sid: The Twilio Call SID identifier

    Returns:
        Confirmation message
    """
    if call_sid in conversation_history:
        del conversation_history[call_sid]
        logger.info(f"Cleared history for call {call_sid}")
        return {"status": "success", "message": f"History cleared for call {call_sid}"}
    return {"status": "not_found", "message": f"No history found for call {call_sid}"}


@mcp.tool()
async def get_all_active_calls() -> Dict[str, Any]:
    """
    Get a list of all active call sessions with conversation history.

    Returns:
        Dictionary with all active call SIDs and their message counts
    """
    active_calls = {
        call_sid: {
            "message_count": len(messages),
            "last_message": messages[-1] if messages else None
        }
        for call_sid, messages in conversation_history.items()
    }
    return {
        "active_call_count": len(active_calls),
        "calls": active_calls
    }


@mcp.tool()
async def get_conversation_logs(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve recent conversation logs from the log file.

    Args:
        limit: Maximum number of log entries to retrieve (default: 10)

    Returns:
        Dictionary containing recent conversation logs
    """
    if not RESPONSES_FILE.exists():
        return {"logs": [], "count": 0}

    logs = []
    with RESPONSES_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Return most recent logs
    recent_logs = logs[-limit:] if len(logs) > limit else logs
    return {
        "logs": recent_logs,
        "count": len(recent_logs),
        "total_logs": len(logs)
    }


# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------

async def get_ai_response(call_sid: str, user_input: str) -> str:
    """
    Get AI response from OpenAI based on user input and conversation history.

    Args:
        call_sid: The Twilio Call SID
        user_input: The user's speech input

    Returns:
        AI-generated response text
    """
    # Initialize conversation history for new calls
    if call_sid not in conversation_history:
        conversation_history[call_sid] = []

    # Add user message to history
    conversation_history[call_sid].append({
        "role": "user",
        "content": user_input
    })

    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation_history[call_sid]
    ]

    try:
        # Get response from OpenAI
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )

        ai_response = response.choices[0].message.content

        # Add assistant response to history
        conversation_history[call_sid].append({
            "role": "assistant",
            "content": ai_response
        })

        return ai_response

    except Exception as e:
        logger.error(f"OpenAI API error for call {call_sid}: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again."


def log_conversation(call_sid: str, user_input: str, ai_response: str) -> None:
    """
    Log conversation to file for persistence.

    Args:
        call_sid: The Twilio Call SID
        user_input: The user's input
        ai_response: The AI's response
    """
    log_entry = {
        "call_sid": call_sid,
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "ai_response": ai_response
    }

    with RESPONSES_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# Twilio Webhook Endpoints
# ----------------------------------------------------------------------

@mcp.custom_route("/voice", ["POST"])
async def voice_webhook(request: Request) -> Response:
    """
    Main Twilio webhook endpoint for handling incoming calls and speech.
    This endpoint receives Twilio's voice webhook requests and responds with TwiML.
    """
    try:
        form = await request.form()
        user_input = form.get("SpeechResult") or form.get("Digits") or ""
        call_sid = form.get("CallSid", "unknown")

        logger.info(f"[CALL {call_sid}] User said: {user_input}")

        # Get AI response
        if user_input:
            ai_response = await get_ai_response(call_sid, user_input)
        else:
            # Initial greeting
            ai_response = "Hello! I'm your AI assistant. How can I help you today?"
            if call_sid not in conversation_history:
                conversation_history[call_sid] = []

        logger.info(f"[CALL {call_sid}] AI responded: {ai_response}")

        # Log conversation
        if user_input:
            log_conversation(call_sid, user_input, ai_response)

        # Generate TwiML response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{ai_response}</Say>
    <Pause length="1"/>
    <Gather input="speech" action="/voice" method="POST" timeout="5" speechTimeout="auto">
        <Say voice="alice">I'm listening...</Say>
    </Gather>
    <Say voice="alice">I didn't catch that. Please call back if you need assistance.</Say>
</Response>"""

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing voice webhook: {e}")

        # Error TwiML
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I'm sorry, something went wrong. Please try calling again.</Say>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")


@mcp.custom_route("/call-status", ["POST"])
async def call_status_webhook(request: Request) -> Response:
    """
    Twilio webhook endpoint for call status updates.
    Handles call lifecycle events (completed, busy, failed, etc.)
    """
    try:
        form = await request.form()
        call_sid = form.get("CallSid", "unknown")
        call_status = form.get("CallStatus", "unknown")

        logger.info(f"[CALL {call_sid}] Status update: {call_status}")

        # Clean up conversation history when call ends
        if call_status in ["completed", "failed", "busy", "no-answer"]:
            if call_sid in conversation_history:
                logger.info(f"[CALL {call_sid}] Call ended. Cleaning up history.")
                del conversation_history[call_sid]

        return Response(content="OK", media_type="text/plain")

    except Exception as e:
        logger.error(f"Error processing call status webhook: {e}")
        return Response(content="ERROR", media_type="text/plain")


@mcp.custom_route("/health", ["GET"])
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint to verify server status.
    """
    return {
        "status": "healthy",
        "service": "twilio-calling-agent",
        "timestamp": datetime.now().isoformat(),
        "active_calls": len(conversation_history),
        "openai_configured": bool(OPENAI_API_KEY)
    }


# ----------------------------------------------------------------------
# MCP Resources
# ----------------------------------------------------------------------

@mcp.resource("conversation://logs")
def get_logs_resource() -> str:
    """
    MCP Resource providing access to conversation logs.
    """
    if not RESPONSES_FILE.exists():
        return "No conversation logs available yet."

    with RESPONSES_FILE.open("r", encoding="utf-8") as f:
        logs = f.readlines()

    return "\n".join(logs[-50:])  # Last 50 entries


@mcp.resource("conversation://active-calls")
def get_active_calls_resource() -> str:
    """
    MCP Resource providing information about active calls.
    """
    if not conversation_history:
        return "No active calls."

    result = []
    for call_sid, messages in conversation_history.items():
        result.append(f"Call SID: {call_sid}")
        result.append(f"Messages: {len(messages)}")
        result.append("---")

    return "\n".join(result)


# ----------------------------------------------------------------------
# Main Entry Point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Twilio MCP Server")
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"OpenAI Model: {OPENAI_MODEL}")
    logger.info("=" * 60)

    # Ensure log file exists
    RESPONSES_FILE.touch(exist_ok=True)

    # Start the FastMCP server
    mcp.run()
