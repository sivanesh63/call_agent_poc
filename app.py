#!/usr/bin/env python3
"""
FastAPI Server for Twilio Call Agent with MCP Architecture
Handles Twilio webhooks and uses MCP client for AI-powered call processing.
"""

import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Twilio Call Agent with MCP",
    description="AI-powered call agent using MCP architecture",
    version="1.0.0",
)

# Initialize OpenAI client
openai_client = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# MCP Server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

# Global MCP session (in production, use connection pool)
mcp_session: ClientSession | None = None


async def get_mcp_session() -> ClientSession:
    """Get or create MCP session."""
    global mcp_session
    if mcp_session is None:
        # In production, implement proper connection management
        raise RuntimeError("MCP session not initialized. Start the application properly.")
    return mcp_session


async def call_mcp_tool(tool_name: str, **kwargs) -> Any:
    """
    Call an MCP tool.

    Args:
        tool_name: Name of the tool to call
        **kwargs: Tool arguments

    Returns:
        Tool result as dictionary
    """
    session = await get_mcp_session()
    result = await session.call_tool(tool_name, arguments=kwargs)

    # Parse result
    if result.content:
        import json
        try:
            return json.loads(result.content[0].text)
        except:
            return {"result": result.content[0].text}
    return {}


async def generate_ai_response(conversation_history: list) -> str:
    """
    Generate AI response using OpenAI.

    Args:
        conversation_history: List of conversation messages

    Returns:
        AI-generated response
    """
    # Add system prompt if not present
    if not conversation_history or conversation_history[0].get("role") != "system":
        system_message = {
            "role": "system",
            "content": """You are a helpful voice assistant handling phone calls.
Keep responses concise (2-3 sentences) and conversational.
Be friendly, professional, and helpful."""
        }
        conversation_history.insert(0, system_message)

    # Generate response
    response = await openai_client.ainvoke(conversation_history)
    return response.content


@app.on_event("startup")
async def startup_event():
    """Initialize MCP connection on startup."""
    global mcp_session
    print("=" * 60)
    print("🚀 Starting Twilio Call Agent with MCP Architecture")
    print("=" * 60)
    print(f"MCP Server URL: {MCP_SERVER_URL}")
    print(f"OpenAI Model: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")
    print("=" * 60)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Twilio Call Agent with MCP",
        "version": "1.0.0",
        "architecture": "MCP Server-Client",
        "endpoints": {
            "health": "/health",
            "incoming_call": "/twilio/incoming-call",
            "handle_speech": "/twilio/handle-speech",
            "call_status": "/twilio/call-status",
            "active_calls": "/twilio/active-calls",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mcp_server": MCP_SERVER_URL,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/twilio/incoming-call", response_class=PlainTextResponse)
async def incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
):
    """
    Handle incoming Twilio call.

    Args:
        CallSid: Twilio call identifier
        From: Caller phone number
        To: Called phone number

    Returns:
        TwiML response
    """
    print(f"📞 Incoming call - SID: {CallSid}, From: {From}, To: {To}")

    try:
        # Initialize call session via MCP
        result = await call_mcp_tool(
            "initialize_call_session",
            call_sid=CallSid,
            caller_number=From,
            called_number=To,
        )

        if not result.get("success"):
            print(f"❌ Error initializing call: {result.get('error')}")
            response = VoiceResponse()
            response.say("Sorry, we encountered an error. Please try again later.")
            return str(response)

        # Get system prompt
        system_prompt_result = await call_mcp_tool("get_system_prompt")
        system_prompt = system_prompt_result if isinstance(system_prompt_result, str) else str(system_prompt_result)

        # Add system message to conversation
        await call_mcp_tool(
            "add_message_to_conversation",
            call_sid=CallSid,
            role="system",
            content=system_prompt,
        )

        # Create Ultravox session
        ultravox_result = await call_mcp_tool(
            "create_ultravox_session",
            call_sid=CallSid,
            system_prompt=system_prompt,
        )

        # Create TwiML response
        response = VoiceResponse()

        if ultravox_result.get("success") and ultravox_result.get("join_url"):
            # Connect to Ultravox via Stream
            response.say("Hello! Connecting you to our AI assistant.")
            connect = response.connect()
            connect.stream(url=ultravox_result["join_url"].replace("https://", "wss://"))
        else:
            # Fallback to speech gathering
            response.say("Hello! Welcome to our AI voice assistant. How can I help you today?")
            gather = Gather(
                input="speech",
                action="/twilio/handle-speech",
                method="POST",
                speech_timeout="auto",
            )
            response.append(gather)

        print(f"✓ Call initialized: {CallSid}")
        return str(response)

    except Exception as e:
        print(f"❌ Error handling incoming call: {e}")
        response = VoiceResponse()
        response.say("Sorry, we encountered an error. Please try again later.")
        return str(response)


@app.post("/twilio/handle-speech", response_class=PlainTextResponse)
async def handle_speech(
    CallSid: str = Form(...),
    SpeechResult: str = Form(None),
):
    """
    Handle speech input from caller.

    Args:
        CallSid: Twilio call identifier
        SpeechResult: Speech-to-text result

    Returns:
        TwiML response with AI-generated speech
    """
    print(f"🗣️  Speech received - SID: {CallSid}, Speech: {SpeechResult}")

    response = VoiceResponse()

    try:
        if not SpeechResult:
            response.say("I didn't catch that. Could you please repeat?")
            gather = Gather(
                input="speech",
                action="/twilio/handle-speech",
                method="POST",
                speech_timeout="auto",
            )
            response.append(gather)
            return str(response)

        # Add user message to conversation
        await call_mcp_tool(
            "add_message_to_conversation",
            call_sid=CallSid,
            role="user",
            content=SpeechResult,
        )

        # Get conversation history
        history_result = await call_mcp_tool(
            "get_conversation_history",
            call_sid=CallSid,
        )

        conversation_history = history_result.get("history", [])

        # Generate AI response
        ai_response = await generate_ai_response(conversation_history)

        # Add assistant response to conversation
        await call_mcp_tool(
            "add_message_to_conversation",
            call_sid=CallSid,
            role="assistant",
            content=ai_response,
        )

        # Create TwiML response
        response.say(ai_response)
        gather = Gather(
            input="speech",
            action="/twilio/handle-speech",
            method="POST",
            speech_timeout="auto",
        )
        response.append(gather)

        print(f"✓ Generated response for call: {CallSid}")
        return str(response)

    except Exception as e:
        print(f"❌ Error handling speech: {e}")
        response.say("Sorry, I encountered an error processing your request.")
        response.hangup()
        return str(response)


@app.post("/twilio/call-status")
async def call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
):
    """
    Handle call status updates.

    Args:
        CallSid: Twilio call identifier
        CallStatus: Call status (ringing, in-progress, completed, etc.)

    Returns:
        Success response
    """
    print(f"📊 Call status - SID: {CallSid}, Status: {CallStatus}")

    try:
        if CallStatus in ["completed", "failed", "no-answer", "busy", "canceled"]:
            # Get analytics before ending
            analytics = await call_mcp_tool("get_call_analytics", call_sid=CallSid)
            print(f"📈 Call analytics: {analytics}")

            # End call session
            result = await call_mcp_tool("end_call_session", call_sid=CallSid)
            print(f"✓ Call ended: {result}")

        return {"status": "ok"}

    except Exception as e:
        print(f"❌ Error handling call status: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/twilio/active-calls")
async def active_calls():
    """Get list of active calls."""
    try:
        result = await call_mcp_tool("list_active_calls")
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# Run with: uvicorn app:app --host 0.0.0.0 --port 3000 --reload
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🎙️  Twilio Call Agent with MCP Architecture")
    print("=" * 60)
    print("Starting FastAPI server...")
    print("=" * 60)

    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 3000)),
        reload=True,
    )
