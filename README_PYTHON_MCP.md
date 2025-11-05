# Twilio MCP Server (Python)

A Python-based MCP (Model Context Protocol) server that provides Twilio calling agent capabilities with OpenAI integration. This implementation uses FastMCP to expose phone call handling as MCP tools and resources.

## Features

- **MCP Server**: Exposes Twilio calling capabilities via Model Context Protocol
- **FastMCP Framework**: Built on FastMCP for easy MCP server development
- **OpenAI Integration**: Uses OpenAI for intelligent conversational responses
- **Twilio Webhooks**: Handles incoming calls and speech processing
- **Conversation Management**: Tracks conversation history per call session
- **Persistent Logging**: Saves all conversations to JSONL file
- **MCP Tools**: Provides tools for conversation history management
- **MCP Resources**: Exposes conversation logs and active calls as resources

## Architecture

```
Twilio Call → Webhook (/voice)
    ↓
FastMCP Server
    ├── OpenAI Client (GPT-4)
    ├── Conversation History (In-Memory)
    └── Persistent Logs (JSONL)
    ↓
MCP Tools & Resources
```

## Prerequisites

1. **Python 3.9+**
2. **Twilio Account** with:
   - Account SID
   - Auth Token
   - A phone number
3. **OpenAI API Key**
4. **Public URL** for webhooks (use ngrok for local development)

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8080

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Twilio Configuration (for reference)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

## Running the Server

### Start the MCP Server

```bash
python twilio_webhook.py
```

The server will start on `http://0.0.0.0:8080` by default.

### Using with Ngrok (Local Development)

1. Start the server:
```bash
python twilio_webhook.py
```

2. In another terminal, start ngrok:
```bash
ngrok http 8080
```

3. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

4. Configure Twilio webhook (see below)

## Twilio Configuration

1. Log in to [Twilio Console](https://console.twilio.com/)
2. Go to **Phone Numbers** → **Manage** → **Active numbers**
3. Click on your phone number
4. Configure **Voice & Fax**:
   - **A CALL COMES IN**: Webhook
   - URL: `https://your-ngrok-url.ngrok.io/voice`
   - HTTP Method: `POST`
5. Configure **Call Status Changes**:
   - URL: `https://your-ngrok-url.ngrok.io/call-status`
   - HTTP Method: `POST`
6. Click **Save**

## MCP Tools

The server exposes the following MCP tools:

### 1. `get_conversation_history`
Retrieve conversation history for a specific call.

**Parameters:**
- `call_sid` (string): The Twilio Call SID

**Returns:**
```json
{
  "call_sid": "CAxxxx",
  "messages": [...],
  "message_count": 5
}
```

### 2. `clear_conversation_history`
Clear conversation history for a specific call.

**Parameters:**
- `call_sid` (string): The Twilio Call SID

**Returns:**
```json
{
  "status": "success",
  "message": "History cleared for call CAxxxx"
}
```

### 3. `get_all_active_calls`
Get list of all active call sessions.

**Returns:**
```json
{
  "active_call_count": 2,
  "calls": {
    "CAxxxx": {
      "message_count": 5,
      "last_message": {...}
    }
  }
}
```

### 4. `get_conversation_logs`
Retrieve recent conversation logs from file.

**Parameters:**
- `limit` (integer): Max entries to retrieve (default: 10)

**Returns:**
```json
{
  "logs": [...],
  "count": 10,
  "total_logs": 150
}
```

## MCP Resources

### 1. `conversation://logs`
Access to persistent conversation logs (last 50 entries).

### 2. `conversation://active-calls`
Information about currently active calls.

## HTTP Endpoints

### Voice Webhook
- **POST** `/voice` - Handles incoming calls and speech input
- Returns TwiML response for Twilio

### Call Status
- **POST** `/call-status` - Receives call status updates
- Cleans up conversation history when calls end

### Health Check
- **GET** `/health` - Server health status
- Returns active call count and configuration status

## Usage Example

### Testing with MCP Client

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async def test_mcp_tools():
    async with sse_client("http://localhost:8080/mcp") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Get active calls
            result = await session.call_tool("get_all_active_calls", {})
            print(result)

            # Get conversation history
            result = await session.call_tool(
                "get_conversation_history",
                {"call_sid": "CAxxxx"}
            )
            print(result)
```

### Making a Test Call

1. Call your Twilio phone number
2. The AI will greet you: "Hello! I'm your AI assistant. How can I help you today?"
3. Speak your question or request
4. The AI will respond intelligently
5. Conversation continues until you hang up

## Conversation Flow

1. **Call Initiated**: User calls Twilio number
2. **Initial Greeting**: AI welcomes the caller
3. **Speech Input**: Twilio converts speech to text
4. **AI Processing**:
   - Retrieves conversation history
   - Sends to OpenAI with context
   - Gets intelligent response
5. **Response Delivery**: AI speaks response to caller
6. **Loop**: Steps 3-5 repeat for conversation
7. **Call End**: History is cleaned up

## Customization

### Modify AI Personality

Edit the `SYSTEM_PROMPT` in `twilio_webhook.py`:

```python
SYSTEM_PROMPT = """
You are a customer service agent for ACME Corp.
Be professional, friendly, and concise.
Focus on helping customers with orders and products.
"""
```

### Adjust OpenAI Model

Update `.env`:
```env
OPENAI_MODEL=gpt-4o          # High quality
# or
OPENAI_MODEL=gpt-3.5-turbo   # Faster, cheaper
```

### Change Response Length

In `get_ai_response()` function:
```python
response = await openai_client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=messages,
    temperature=0.7,
    max_tokens=150  # Adjust this value
)
```

## File Structure

```
call_agent_poc/
├── twilio_webhook.py          # Main MCP server implementation
├── requirements.txt           # Python dependencies
├── conversation_logs.jsonl    # Persistent conversation logs
├── .env                       # Environment variables (gitignored)
└── README_PYTHON_MCP.md      # This file
```

## Logging

The server logs to both:
1. **Console**: Real-time logs with timestamps
2. **File**: `conversation_logs.jsonl` - All conversations in JSONL format

### Log Format
```json
{
  "call_sid": "CAxxxx",
  "timestamp": "2025-11-05T10:30:45",
  "user_input": "What are your hours?",
  "ai_response": "We're open Monday through Friday, 9 AM to 5 PM."
}
```

## Troubleshooting

### Server Won't Start
- Check Python version: `python --version` (need 3.9+)
- Verify dependencies: `pip install -r requirements.txt`
- Check port availability: `lsof -i :8080`

### OpenAI API Errors
- Verify `OPENAI_API_KEY` in `.env`
- Check API quota and billing
- Review error logs in console

### Twilio Not Connecting
- Verify ngrok is running and URL is correct
- Check Twilio webhook configuration
- Ensure `/voice` endpoint is publicly accessible
- Review Twilio debugger in console

### Conversations Not Persisting
- Check write permissions on `conversation_logs.jsonl`
- Verify disk space
- Check logs for errors

## Security Considerations

- **Never commit `.env`** - Contains API keys
- **Validate Twilio requests** - Add signature validation in production
- **Rate limiting** - Implement for production use
- **HTTPS only** - Use HTTPS for all webhook endpoints
- **API key rotation** - Regularly rotate OpenAI and Twilio keys

## Performance Tips

1. **Use GPT-3.5-turbo** for development to reduce latency and cost
2. **Adjust max_tokens** to control response length
3. **Monitor conversation_logs.jsonl** size and rotate as needed
4. **Clean up old call histories** periodically

## Cost Considerations

- **Twilio**: ~$0.013/minute for voice calls
- **OpenAI**:
  - GPT-4: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
  - GPT-3.5-turbo: ~$0.0015 per 1K tokens (much cheaper)
- Estimate: ~$0.05-0.15 per minute of conversation (GPT-4)

## Integration with Other MCP Clients

This server can be used with any MCP client:

```python
# Example: Using with LangChain MCP Adapter
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.client.sse import sse_client
from mcp import ClientSession

async with sse_client("http://localhost:8080/mcp") as (read, write):
    async with ClientSession(read, write) as client:
        await client.initialize()
        tools = await load_mcp_tools(client)
        # Use tools with your agent
```

## Development

### Run in Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python twilio_webhook.py
```

### Test Without Twilio

You can test the MCP tools directly without making actual phone calls:

```bash
# Use MCP client to test tools
# See "Usage Example" section above
```

## License

MIT

## Support

For issues:
- Check server logs for errors
- Review [FastMCP documentation](https://github.com/jlowin/fastmcp)
- Consult [Twilio docs](https://www.twilio.com/docs)
- Review [OpenAI API docs](https://platform.openai.com/docs)

## Contributing

Contributions welcome! Please submit pull requests with:
- Clear description of changes
- Tests if applicable
- Updated documentation
