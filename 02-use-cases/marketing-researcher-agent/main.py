"""
Marketing Researcher Agent

A multi-agent system for automated marketing research, data analysis, and report generation.
Built with Amazon Bedrock AgentCore and Strands Agents SDK with AgentCore Memory integration.
"""

import os
import json
import logging
from uuid import uuid4
from datetime import datetime
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType
from strands import Agent
from strands.hooks import (
    AgentInitializedEvent,
    HookProvider,
    HookRegistry,
    MessageAddedEvent,
)
from strands_tools import python_repl, file_write, editor
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider

# Import custom tools
from tools.tavily_tool import web_search, web_extract, web_crawl
from tools.knowledge_base_tool import get_schema
from tools.sqllite_tool import run_sqlite_query
from constants import BEDROCK_MODEL

# Set environment for tools
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("marketing-researcher-agent")

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Initialize memory client (stateless - created per request)
REGION = os.getenv("AWS_REGION", "us-west-2")


class MarketingMemoryHookProvider(HookProvider):
    """Memory hook provider for short-term memory (conversation history)"""

    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_client = memory_client
        self.memory_id = memory_id

    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts"""
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")

            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return

            # Load the last 10 conversation turns from memory
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id, actor_id=actor_id, session_id=session_id, k=10
            )

            if recent_turns:
                # Format conversation history for context
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        role = message["role"]
                        content = message["content"]["text"]
                        context_messages.append(f"{role}: {content}")

                context = "\n".join(context_messages)
                # Add context to agent's system prompt
                event.agent.system_prompt += (
                    f"\n\nRecent conversation history:\n{context}"
                )
                logger.info(f"✅ Loaded {len(recent_turns)} conversation turns")

        except Exception as e:
            logger.error(f"Memory load error: {e}")

    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in memory"""
        messages = event.agent.messages
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")

            if messages and len(messages) > 0:
                last_message = messages[-1]
                if last_message.get("content") and len(last_message["content"]) > 0:
                    content_item = last_message["content"][0]
                    if content_item.get("text"):
                        self.memory_client.create_event(
                            memory_id=self.memory_id,
                            actor_id=actor_id,
                            session_id=session_id,
                            messages=[(content_item["text"], last_message["role"])],
                        )
        except Exception as e:
            logger.error(f"Memory save error: {e}")

    def register_hooks(self, registry: HookRegistry):
        # Register memory hooks
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)


# Global memory cache to avoid repeated creation
_memory_cache = {"client": None, "memory_id": None}


def get_or_create_memory():
    """Get or create AgentCore Memory resource with caching"""
    try:
        # Return cached memory if available
        if _memory_cache["client"] and _memory_cache["memory_id"]:
            logger.info(f"Using cached memory: {_memory_cache['memory_id']}")
            return _memory_cache["client"], _memory_cache["memory_id"]

        client = MemoryClient(region_name=REGION)
        memory_name = "MarketingResearcherAgent"

        # Try to find existing memory first
        memories = client.list_memories()
        existing_memory = next((m for m in memories if memory_name in m["id"]), None)

        if existing_memory:
            logger.info(f"Found existing memory: {existing_memory['id']}")
            # Cache the memory
            _memory_cache["client"] = client
            _memory_cache["memory_id"] = existing_memory["id"]
            return client, existing_memory["id"]

        # Only create new memory if none exists
        logger.info("Creating new memory (this may take a moment)...")
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="Marketing Researcher Agent with memory capabilities",
            strategies=[
                {
                    StrategyType.USER_PREFERENCE.value: {
                        "name": "UserPreferences",
                        "description": "Captures user preferences for marketing research",
                        "namespaces": ["user/{actorId}/preferences"],
                    }
                }
            ],
            event_expiry_days=30,
            max_wait=30,  # Reduced wait time further
            poll_interval=3,
        )

        memory_id = memory["id"]
        logger.info(f"Created new memory: {memory_id}")

        # Cache the memory
        _memory_cache["client"] = client
        _memory_cache["memory_id"] = memory_id
        return client, memory_id

    except Exception as e:
        logger.error(f"Memory initialization error: {e}")
        # Continue without memory if it fails
        logger.info("Continuing without memory capabilities")
        return None, None


def create_marketing_orchestrator(
    user_id: str,
    session_id: str,
    memory_client: MemoryClient = None,
    memory_id: str = None,
):
    """Create marketing researcher orchestrator with multi-agent workflow capabilities"""

    from datetime import datetime
    from agents.planner_agent import planner_agent_tool
    from agents.researcher_agent import researcher_agent_tool
    from agents.python_agent import python_agent_tool
    from agents.text2sql_agent import text2sql_agent_tool
    from agents.report_agent import report_agent_tool
    from agents.reflection_agent import reflection_agent_tool

    now = datetime.now()
    current_quarter = (now.month - 1) // 3 + 1

    system_prompt = f"""You are a Marketing Research Orchestrator, managing a team of specialized AI agents to conduct comprehensive marketing research and analysis.

## Current Context
- **Current Date**: {now.strftime("%B %d, %Y")}
- **Current Year**: {now.year}
- **Current Quarter**: Q{current_quarter}
- **User ID**: {user_id}
- **Session ID**: {session_id}

## Your Specialized Agent Team
You have access to these specialist agents as tools:

1. **planner_agent_tool**: Creates detailed execution plans and breaks requests into tasks
2. **researcher_agent_tool**: Conducts web research using search, extract, and crawl tools
3. **text2sql_agent_tool**: Analyzes customer databases by generating SQL queries
4. **python_agent_tool**: Performs data analysis and creates visualizations using Python
5. **report_agent_tool**: Generates professional markdown reports and saves them to files
6. **reflection_agent_tool**: Reviews work quality and suggests improvements

## Multi-Agent Workflow Process
For complex requests, coordinate multiple agents in sequence:

### Example Workflow:
1. **Planning**: Use planner_agent_tool to break down complex requests
2. **Research**: Use researcher_agent_tool for market intelligence
3. **Analysis**: Use python_agent_tool for data analysis and visualizations
4. **Database**: Use text2sql_agent_tool for customer data queries
5. **Quality**: Use reflection_agent_tool to review work quality
6. **Report**: Use report_agent_tool to synthesize final reports

## Decision Framework
- **Simple requests**: Handle directly with your own tools or single agent
- **Complex requests**: Coordinate multiple specialist agents
- **Research-heavy**: Always include researcher_agent_tool
- **Data analysis**: Include python_agent_tool for calculations and visualizations  
- **Database queries**: Use text2sql_agent_tool for customer data analysis
- **Final output**: Always end with report_agent_tool for professional reports

## Task Management Example
For complex workflows, manage tasks like this:

```python
tasks = {{
    "market_research": {{
        "description": "Research current sustainable fashion market trends",
        "agent": researcher_agent_tool,
        "status": "pending",
        "dependencies": []
    }},
    "data_analysis": {{
        "description": "Analyze market data and create visualizations", 
        "agent": python_agent_tool,
        "status": "pending",
        "dependencies": ["market_research"]
    }},
    "final_report": {{
        "description": "Generate comprehensive marketing report",
        "agent": report_agent_tool,
        "status": "pending", 
        "dependencies": ["market_research", "data_analysis"]
    }}
}}
```

## Current Context for Analysis
- Focus on {now.year} data and trends
- Consider Q{current_quarter} context for quarterly analyses
- Include both current market state and future projections
- Integrate multiple data sources for comprehensive insights

Your role is to intelligently coordinate these specialist agents to deliver comprehensive, professional marketing research results. Use the agents as tools to break down complex requests into manageable tasks."""

    # Production-ready model configuration
    from strands.models.bedrock import BedrockModel

    agent_model = BedrockModel(
        model_id=BEDROCK_MODEL,
        temperature=0.3,
        max_tokens=4000,
        top_p=0.8,
    )

    # Core tools including specialist agents
    tools = [
        # Specialist agent tools
        planner_agent_tool,
        researcher_agent_tool,
        python_agent_tool,
        text2sql_agent_tool,
        report_agent_tool,
        reflection_agent_tool,
        # Direct tools for simple tasks
        web_search,
        web_extract,
        web_crawl,
        get_schema,
        run_sqlite_query,
        python_repl,
        file_write,
        editor,
    ]

    # Add memory tools if available
    hooks = []
    if memory_client and memory_id:
        try:
            # Add long-term memory tools
            memory_provider = AgentCoreMemoryToolProvider(
                memory_id=memory_id,
                actor_id=user_id,
                session_id=session_id,
                namespace=f"user/{user_id}/preferences",
            )
            tools.extend(memory_provider.tools)

            # Add short-term memory hooks for conversation history
            memory_hooks = MarketingMemoryHookProvider(memory_client, memory_id)
            hooks.append(memory_hooks)

            logger.info("✅ Memory integration enabled")
        except Exception as e:
            logger.error(f"Memory integration failed: {e}")

    # Production conversation management
    from strands.agent.conversation_manager import SlidingWindowConversationManager

    conversation_manager = SlidingWindowConversationManager(
        window_size=15,  # Increased for multi-agent context
    )

    # Create orchestrator agent
    agent = Agent(
        model=agent_model,
        system_prompt=system_prompt,
        tools=tools,
        hooks=hooks,
        conversation_manager=conversation_manager,
        state={"actor_id": user_id, "session_id": session_id},
    )

    return agent


@app.entrypoint
async def invoke(payload):
    """Process marketing research requests with production-ready error handling and streaming"""
    try:
        # Input validation
        if not isinstance(payload, dict):
            raise ValueError("Invalid payload format")

        # Extract and validate parameters
        user_message = payload.get(
            "prompt",
            "Hello! I'm your Marketing Researcher Agent. How can I help you today?",
        )
        user_id = payload.get("user_id", f"user_{uuid4().hex[:8]}")
        session_id = payload.get("session_id", f"session_{uuid4().hex[:8]}")

        # Validate inputs
        if not user_message or not isinstance(user_message, str):
            raise ValueError("Invalid or missing prompt")

        if len(user_message) > 10000:  # Reasonable limit
            raise ValueError("Prompt too long")

        logger.info(f"Processing request for user: {user_id}, session: {session_id}")

        # Initialize memory with error handling
        memory_client, memory_id = None, None
        try:
            memory_client, memory_id = get_or_create_memory()
        except Exception as memory_error:
            logger.warning(
                f"Memory initialization failed, continuing without memory: {memory_error}"
            )

        # Create multi-agent orchestrator
        orchestrator = create_marketing_orchestrator(
            user_id, session_id, memory_client, memory_id
        )

        # Process request with multi-agent workflow
        try:
            # Try async streaming first (if available)
            if hasattr(orchestrator, "stream_async"):
                logger.info("Using multi-agent async streaming")

                # Stream the response with workflow coordination
                stream = orchestrator.stream_async(user_message)
                full_response = ""
                tool_messages_sent = set()

                async for event in stream:
                    # Only handle content block deltas for streaming text
                    if isinstance(event, dict) and "event" in event:
                        event_data = event["event"]
                        if "contentBlockDelta" in event_data:
                            delta = event_data["contentBlockDelta"]
                            if "delta" in delta and "text" in delta["delta"]:
                                delta_text = delta["delta"]["text"]
                                if delta_text:
                                    full_response += delta_text
                                    yield delta_text

                    # Handle tool usage with structured tags
                    elif isinstance(event, dict) and "message" in event:
                        message = event["message"]
                        if (
                            "content" in message
                            and "role" in message
                            and message["role"] == "assistant"
                        ):
                            for content_item in message["content"]:
                                if "toolUse" in content_item:
                                    tool_use = content_item["toolUse"]
                                    tool_name = tool_use.get("name", "unknown")
                                    tool_input = tool_use.get("input", {})
                                    tool_id = tool_use.get(
                                        "toolUseId",
                                        f"{tool_name}_{len(tool_messages_sent)}",
                                    )

                                    if tool_id not in tool_messages_sent:
                                        tool_messages_sent.add(tool_id)

                                        # Create structured tool message with tags
                                        tool_data = {
                                            "name": tool_name,
                                            "id": tool_id,
                                            "input": tool_input,
                                            "status": "running",
                                        }

                                        tool_message = f"<TOOL_START>{json.dumps(tool_data)}</TOOL_START>"
                                        yield tool_message

                        # Skip tool results - don't show them to user
                        elif "content" in message and message.get("role") == "user":
                            for content_item in message["content"]:
                                if "toolResult" in content_item:
                                    # Just skip - don't send tool results to frontend
                                    pass

            else:
                # Fallback to synchronous processing
                logger.info("Using synchronous multi-agent processing")
                result = orchestrator(user_message)

                # Extract and yield the response
                if hasattr(result, "message") and result.message:
                    if isinstance(result.message, str):
                        yield result.message
                    elif (
                        isinstance(result.message, dict) and "content" in result.message
                    ):
                        content = result.message["content"]
                        if (
                            isinstance(content, list)
                            and len(content) > 0
                            and "text" in content[0]
                        ):
                            yield content[0]["text"]
                        else:
                            yield str(result.message)
                    else:
                        yield str(result.message)
                else:
                    yield "I apologize, but I couldn't generate a proper response. Please try again."

        except Exception as agent_error:
            logger.error(f"Agent execution error: {agent_error}")

            # Provide user-friendly error messages
            if "throttlingException" in str(agent_error) or "Too many requests" in str(
                agent_error
            ):
                yield "The service is currently busy. Please wait a moment and try again."
            elif "ValidationException" in str(agent_error):
                yield "There was an issue with your request. Please try rephrasing your question."
            elif "ServiceUnavailableException" in str(agent_error):
                yield "The service is temporarily unavailable. Please try again later."
            else:
                yield f"I encountered an error while processing your request. Please try again or contact support if the issue persists."

    except ValueError as validation_error:
        logger.error(f"Validation error: {validation_error}")
        yield f"Invalid request: {str(validation_error)}"

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        yield "An unexpected error occurred. Please try again later."


if __name__ == "__main__":
    logger.info("🚀 Starting Marketing Researcher Agent")
    logger.info("🤖 Powered by Amazon Bedrock AgentCore")
    logger.info("🧠 Memory-enabled conversation system")
    logger.info("🔧 Marketing research and analysis capabilities")
    logger.info("📡 Server starting on port 8080...")
    app.run()
