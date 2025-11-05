# Twilio Call Agent with MCP Architecture

An AI-powered voice agent that receives phone calls through Twilio, uses **MCP (Model Context Protocol)** for tool orchestration, Ultravox for real-time voice interaction, and ChatOpenAI (GPT-4o) for intelligent responses.

## Features

- **MCP Server-Client Architecture**: Modular tool-based architecture using FastMCP
- **Twilio Integration**: Receives and handles incoming phone calls
- **Ultravox Real-time Voice**: Provides natural, real-time voice interactions
- **ChatOpenAI (GPT-4o)**: Powers intelligent conversational responses
- **Call Session Management**: Tracks active calls and conversation history
- **SSE Transport**: Server-Sent Events for MCP communication
- **Python-based**: Fully Python implementation with FastAPI and LangChain

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Incoming Call (Twilio)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (app.py)                        │
│              - Twilio Webhooks                              │
│              - Call Routing                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          MCP Client (SSE Connection)                        │
│          - Tool Invocation                                  │
│          - ChatOpenAI Integration                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          MCP Server (mcp_server.py)                         │
│          - Call Session Management                          │
│          - Conversation History                             │
│          - Ultravox Integration                             │
│          - Analytics & Tools                                │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   [OpenAI]        [Ultravox]        [Twilio]
```

## MCP Tools Available

The MCP server provides the following tools:

1. **initialize_call_session** - Initialize a new call session
2. **add_message_to_conversation** - Add message to conversation history
3. **get_conversation_history** - Get full conversation history
4. **create_ultravox_session** - Create Ultravox real-time voice session
5. **get_call_session** - Get complete call session information
6. **end_call_session** - End call and cleanup resources
7. **list_active_calls** - List all active call sessions
8. **get_system_prompt** - Get default AI agent system prompt
9. **send_twilio_sms** - Send SMS via Twilio
10. **get_call_analytics** - Get call analytics and metrics

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.10+**
2. **Twilio Account** with:
   - Account SID
   - Auth Token
   - A phone number
3. **OpenAI API Key** (for GPT-4o)
4. **Ultravox API Key**
5. **Public URL** (for webhooks):
   - Use [ngrok](https://ngrok.com/) for local development
   - Or deploy to a cloud platform

## Installation

### 1. Clone the repository:
```bash
git clone <repository-url>
cd call_agent_poc
```

### 2. Create Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Create environment file:
```bash
cp .env.example .env
```

### 5. Edit `.env` and fill in your credentials:
```env
# Server Configuration
PORT=3000
HOST=0.0.0.0

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000/sse

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Ultravox Configuration
ULTRAVOX_API_KEY=your_ultravox_api_key
ULTRAVOX_BASE_URL=https://api.ultravox.ai

# Application Configuration
PUBLIC_URL=https://your-public-url.com
```

## Running the Application

### Quick Start (Recommended)

Use the startup script to run both servers:

```bash
chmod +x start.sh
./start.sh
```

This will:
1. Start the MCP server on port 8000
2. Start the FastAPI application on port 3000
3. Display all necessary information

### Manual Start

**Terminal 1 - Start MCP Server:**
```bash
python mcp_server.py
```

**Terminal 2 - Start FastAPI Application:**
```bash
uvicorn app:app --host 0.0.0.0 --port 3000 --reload
```

### Testing the MCP Connection

Test the MCP server and client:

```bash
python test_mcp.py
```

This will:
- Connect to the MCP server
- Test all available tools
- Verify OpenAI integration
- Display results

## Setting Up Ngrok (Local Development)

### 1. Install ngrok:
```bash
# Using npm
npm install -g ngrok

# Or download from https://ngrok.com/download
```

### 2. Start your servers:
```bash
./start.sh
```

### 3. In a new terminal, start ngrok:
```bash
ngrok http 3000
```

### 4. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

### 5. Update your `.env` file:
```env
PUBLIC_URL=https://abc123.ngrok.io
```

### 6. Restart your servers

## Configuring Twilio

1. Log in to your [Twilio Console](https://console.twilio.com/)

2. Go to **Phone Numbers** → **Manage** → **Active numbers**

3. Click on your phone number

4. Scroll to **Voice Configuration**:
   - **A CALL COMES IN**: Webhook
   - URL: `https://your-public-url.com/twilio/incoming-call`
   - HTTP Method: `POST`

5. Under **Call Status Changes**:
   - URL: `https://your-public-url.com/twilio/call-status`
   - HTTP Method: `POST`

6. Click **Save**

## Testing the Agent

1. Ensure both servers are running:
```bash
./start.sh
```

2. Check the health endpoints:
```bash
# FastAPI server
curl http://localhost:3000/health

# Active calls
curl http://localhost:3000/twilio/active-calls
```

3. Call your Twilio phone number from any phone

4. The agent should:
   - Answer the call
   - Initialize MCP session
   - Greet you via Ultravox
   - Listen to your speech
   - Respond intelligently using GPT-4o
   - Track conversation history
   - Continue the conversation

## API Endpoints

### Root
- `GET /` - API information and available endpoints
- `GET /health` - Server health status

### Twilio Webhooks
- `POST /twilio/incoming-call` - Handles incoming calls
- `POST /twilio/handle-speech` - Processes speech input
- `POST /twilio/call-status` - Receives call status updates
- `GET /twilio/active-calls` - Lists all active calls

## Project Structure

```
call_agent_poc/
├── app.py                      # FastAPI server for Twilio webhooks
├── mcp_server.py              # MCP server with tools
├── mcp_client.py              # MCP client with ChatOpenAI
├── test_mcp.py                # MCP testing script
├── start.sh                   # Startup script for all servers
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── src/                      # TypeScript files (legacy, optional)
│   ├── config.ts
│   ├── server.ts
│   ├── routes/
│   └── services/
├── package.json              # Node.js dependencies (legacy, optional)
└── tsconfig.json             # TypeScript config (legacy, optional)
```

## How It Works

### Call Flow

1. **Incoming Call**:
   - Twilio receives call → sends webhook to `/twilio/incoming-call`

2. **MCP Session Initialization**:
   - FastAPI server calls MCP tool: `initialize_call_session`
   - Creates session with caller info and conversation tracking

3. **System Prompt Setup**:
   - Calls MCP tool: `get_system_prompt`
   - Adds system message to conversation history

4. **Ultravox Connection**:
   - Calls MCP tool: `create_ultravox_session`
   - Gets WebSocket URL for real-time voice
   - Connects Twilio call to Ultravox stream

5. **Speech Processing Loop**:
   - User speaks → Twilio converts to text
   - Text sent to `/twilio/handle-speech`
   - MCP tool: `add_message_to_conversation` (user message)
   - MCP tool: `get_conversation_history`
   - ChatOpenAI generates response
   - MCP tool: `add_message_to_conversation` (assistant message)
   - Response converted to speech and played

6. **Call End**:
   - Call status update received
   - MCP tool: `get_call_analytics`
   - MCP tool: `end_call_session`
   - Resources cleaned up

### MCP Architecture Benefits

- **Modularity**: Tools are independent and reusable
- **Scalability**: MCP server can be scaled separately
- **Testability**: Each tool can be tested independently
- **Flexibility**: Easy to add new tools without changing client
- **Observability**: Clear separation of concerns

## Customization

### Modify the AI Assistant Personality

Edit `mcp_server.py`, function `get_system_prompt()`:

```python
@mcp.tool()
def get_system_prompt() -> str:
    return """You are a customer service agent for ACME Corporation.
Your role is to assist customers with their orders and questions.
Be professional, friendly, and concise in your responses (2-3 sentences)."""
```

### Change Voice Settings

Edit `mcp_server.py`, in `create_ultravox_session`:

```python
json={
    "systemPrompt": system_prompt,
    "model": "fixie-ai/ultravox",
    "voice": "terrence",  # Change to different voice
    "temperature": 0.7,   # Adjust creativity (0.0-1.0)
    "firstSpeaker": "agent",
}
```

### Adjust OpenAI Model

Update `.env`:
```env
OPENAI_MODEL=gpt-4o  # or gpt-3.5-turbo for faster/cheaper
```

### Add New MCP Tools

Add new tools to `mcp_server.py`:

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int) -> dict:
    """
    Description of your tool.

    Args:
        param1: Description
        param2: Description

    Returns:
        Dictionary with results
    """
    # Your implementation
    return {"success": True, "data": "result"}
```

## Troubleshooting

### MCP Server Connection Issues
```bash
# Check if MCP server is running
curl http://localhost:8000/health

# Check MCP server logs
python mcp_server.py
```

### Call not connecting
- Verify `PUBLIC_URL` is accessible from internet
- Check Twilio webhook configuration
- Ensure ngrok is running (for local development)
- Check both servers are running

### No AI responses
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI API quota and billing
- Review server logs for errors

### Ultravox connection issues
- Verify `ULTRAVOX_API_KEY` is valid
- Check Ultravox service status
- Review network connectivity

### View logs
```bash
# Start with verbose logging
./start.sh

# Or check individual servers
python mcp_server.py
python -m uvicorn app:app --log-level debug
```

## Development

### Running Tests
```bash
# Test MCP server and tools
python test_mcp.py

# Test specific functionality
python -c "import asyncio; from test_mcp import test_mcp_connection; asyncio.run(test_mcp_connection())"
```

### Adding Dependencies
```bash
# Add to requirements.txt
echo "package-name==version" >> requirements.txt

# Install
pip install -r requirements.txt
```

## Security Considerations

- Never commit `.env` file to version control
- Use environment variables for all secrets
- Validate Twilio webhook signatures in production
- Implement rate limiting for production use
- Use HTTPS for all webhook endpoints
- Rotate API keys regularly
- Monitor MCP tool usage for abuse

## Cost Considerations

- **Twilio**: ~$0.013/minute for voice calls
- **OpenAI GPT-4o**: ~$0.005/1K input tokens, ~$0.015/1K output tokens
- **Ultravox**: Check Ultravox pricing
- Consider using GPT-3.5-turbo for development to reduce costs

## Deployment

### Deploy to Cloud Platform

#### Heroku
```bash
# Add Procfile
echo "web: ./start.sh" > Procfile

# Deploy
git push heroku main
```

#### Railway
1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically

#### Google Cloud Run
```bash
# Create Dockerfile
# Build and deploy container
gcloud run deploy --source .
```

#### AWS Elastic Beanstalk
```bash
# Create application
eb init
eb create
```

**Remember to set environment variables on your platform!**

## MCP Server API

The MCP server exposes the following endpoints:

- `GET /sse` - SSE endpoint for MCP client connections
- `GET /health` - Health check
- Tool calls via MCP protocol

## Example: Using MCP Client Programmatically

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async def use_mcp():
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call a tool
            result = await session.call_tool(
                "initialize_call_session",
                arguments={
                    "call_sid": "CA123",
                    "caller_number": "+1234567890",
                    "called_number": "+0987654321"
                }
            )

            print(result.content[0].text)
```

## License

MIT

## Support

For issues and questions:
- Check the [Twilio documentation](https://www.twilio.com/docs)
- Review [OpenAI API docs](https://platform.openai.com/docs)
- Consult [Ultravox documentation](https://ultravox.ai/docs)
- Read [MCP specification](https://modelcontextprotocol.io)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### v2.0.0 (Current)
- Migrated to MCP server-client architecture
- Added FastMCP for tool orchestration
- Integrated ChatOpenAI (GPT-4o) with LangChain
- Implemented SSE transport for MCP
- Added comprehensive testing suite
- Python-based implementation

### v1.0.0
- Initial TypeScript implementation
- Basic Twilio, Ultravox, OpenAI integration
