#!/usr/bin/env python3
"""
MCP Client for Twilio Call Agent
Connects to MCP server and provides AI-powered call handling using ChatOpenAI.
"""

import os
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool

# Load environment variables
load_dotenv()


class MCPCallAgentClient:
    """MCP Client for handling Twilio calls with AI agent."""

    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        """
        Initialize MCP client.

        Args:
            mcp_server_url: URL of the MCP server SSE endpoint
        """
        self.mcp_server_url = mcp_server_url
        self.session: ClientSession | None = None
        self.tools: List[Tool] = []
        self.model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.agent: AgentExecutor | None = None

    async def connect(self):
        """Connect to MCP server and initialize session."""
        print(f"🔌 Connecting to MCP server at {self.mcp_server_url}...")

        async with sse_client(self.mcp_server_url) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                print("✓ MCP session initialized")

                # Load tools from MCP server
                await self.load_tools()

                # Create agent
                self.create_agent()

                print(f"✓ Agent created with {len(self.tools)} tools")
                print("✓ MCP Client ready")

                # Keep session alive
                while True:
                    await asyncio.sleep(1)

    async def load_tools(self):
        """Load tools from MCP server and convert to LangChain tools."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        # List available tools
        tools_response = await self.session.list_tools()

        print(f"📋 Loading {len(tools_response.tools)} tools from MCP server...")

        # Convert MCP tools to LangChain tools
        self.tools = []
        for mcp_tool in tools_response.tools:
            tool_name = mcp_tool.name
            tool_description = mcp_tool.description or "No description"

            # Create a closure to capture the tool name
            def make_tool_func(name: str):
                async def tool_func(**kwargs) -> str:
                    """Execute MCP tool."""
                    result = await self.session.call_tool(name, arguments=kwargs)
                    return str(result.content[0].text) if result.content else ""

                return tool_func

            langchain_tool = Tool(
                name=tool_name,
                description=tool_description,
                func=lambda **kwargs: asyncio.create_task(make_tool_func(tool_name)(**kwargs)),
                coroutine=make_tool_func(tool_name),
            )

            self.tools.append(langchain_tool)
            print(f"  ✓ Loaded tool: {tool_name}")

    def create_agent(self):
        """Create ReAct agent with loaded tools."""
        # Create agent prompt
        template = """You are an AI assistant helping handle phone calls through Twilio.
You have access to tools for managing call sessions, conversation history, and creating voice responses.

Available tools:
{tools}

Use the following format:

Question: the input question or task
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        # Create agent
        agent = create_react_agent(self.model, self.tools, prompt)
        self.agent = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

    async def handle_incoming_call(self, call_sid: str, caller: str, called: str) -> Dict[str, Any]:
        """
        Handle an incoming call by initializing session and creating Ultravox session.

        Args:
            call_sid: Twilio call SID
            caller: Caller phone number
            called: Called phone number

        Returns:
            Dictionary with call handling information
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        message = f"""Handle incoming call with the following details:
- Call SID: {call_sid}
- From: {caller}
- To: {called}

Please:
1. Initialize the call session
2. Get the system prompt
3. Create an Ultravox session
4. Return the Ultravox join URL"""

        result = await self.agent.ainvoke({"input": message})
        return result

    async def process_user_speech(self, call_sid: str, user_message: str) -> str:
        """
        Process user speech and generate AI response.

        Args:
            call_sid: Twilio call SID
            user_message: User's speech converted to text

        Returns:
            AI-generated response
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        message = f"""Process speech for call {call_sid}:
User said: "{user_message}"

Please:
1. Add the user message to conversation history
2. Get the conversation history
3. Generate an appropriate response (keep it concise for voice, 2-3 sentences)
4. Add your response to the conversation history
5. Return only the response text to say to the user"""

        result = await self.agent.ainvoke({"input": message})
        return result.get("output", "")

    async def end_call(self, call_sid: str) -> Dict[str, Any]:
        """
        End a call session.

        Args:
            call_sid: Twilio call SID

        Returns:
            Dictionary with call end information
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        message = f"""End call session {call_sid}:
1. Get call analytics
2. End the session
3. Return a summary"""

        result = await self.agent.ainvoke({"input": message})
        return result


class MCPClientAPI:
    """
    Simplified API wrapper for MCP client to use from Express server.
    Uses direct tool calls instead of agent for better performance.
    """

    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        self.mcp_server_url = mcp_server_url
        self.session: ClientSession | None = None
        self.model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    async def initialize(self):
        """Initialize connection to MCP server."""
        print(f"🔌 Connecting to MCP server at {self.mcp_server_url}...")
        # This will be called from Express/Node.js side
        # For now, return success
        return {"success": True}

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        result = await self.session.call_tool(tool_name, arguments=kwargs)
        return result.content[0].text if result.content else ""

    async def initialize_call(self, call_sid: str, caller: str, called: str) -> Dict[str, Any]:
        """Initialize call session."""
        # This would normally call the MCP tool, but for the API we'll create a simpler version
        return {
            "success": True,
            "call_sid": call_sid,
            "message": "Call initialized",
        }

    async def generate_response(self, call_sid: str, conversation_history: List[Dict]) -> str:
        """Generate AI response using OpenAI."""
        # Convert conversation history to OpenAI format
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]

        # Generate response
        response = await self.model.ainvoke(messages)
        return response.content


# Example usage
async def example_usage():
    """Example of using the MCP client."""
    client = MCPCallAgentClient()

    # This would normally connect to the server
    # await client.connect()

    # Example: Handle incoming call
    # result = await client.handle_incoming_call(
    #     "CA1234567890abcdef",
    #     "+1234567890",
    #     "+0987654321"
    # )
    # print(result)


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 MCP Client: Twilio Call Agent")
    print("=" * 60)
    print("This client connects to the MCP server and provides AI-powered call handling.")
    print("=" * 60)

    # Run example
    # asyncio.run(example_usage())

    # For production, this would be imported and used by the Express server
    print("\nTo use: Import MCPClientAPI in your application")
