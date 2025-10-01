# Marketing Researcher Agent

## Overview

A multi-agent system for automated marketing research, data analysis, and report generation. Built with Amazon Bedrock AgentCore and Strands Agents SDK.

| Information   | Details                                  |
| ------------- | ---------------------------------------- |
| Use case type | Conversational                           |
| Agent type    | Multi-agent                              |
| Components    | Tools, Memory, AgentCore Runtime         |
| Vertical      | Marketing/Business Intelligence          |
| Complexity    | Advanced                                 |
| SDK           | Amazon Bedrock AgentCore, Strands Agents |

## Solution Architecture

The Marketing Researcher Agent system consists of several specialized agents working together:

![Marketing Researcher Agent Architecture](./architecture.png)

### Agent Roles

1. **Planner Agent**: Orchestrates workflow and breaks user requests into actionable tasks
2. **Researcher Agent**: Conducts web research and gathers market intelligence using Tavily API
3. **Text2SQL Agent**: Analyzes customer databases by converting natural language to SQL queries
4. **Python Agent**: Performs data analysis and creates visualizations using Python
5. **Report Agent**: Generates professional marketing reports and executive summaries
6. **Memory Agent**: Manages user preferences and maintains conversation history across sessions
7. **Reflection Agent**: Reviews outputs for quality and triggers improvements when needed

### Key Features

- **Multi-Agent Orchestration**: Specialized agents collaborate intelligently
- **AgentCore Memory**: 
  - **Short-term Memory**: Conversation history and context across turns
  - **Long-term Memory**: User preferences and marketing insights across sessions
- **Web Research**: Real-time market research using [Tavily](https://www.tavily.com/) search
- **Data Analysis**: SQL-based customer database analysis and Python analytics
- **Report Generation**: Automated professional marketing reports with visualizations
- **Streaming Responses**: Real-time response generation with progress indicators
- **Web Interface**: Interactive Streamlit interface for easy interaction

### Workflow Process

1. **User Request**: User submits a marketing research query
2. **Planning Phase**: Planner Agent analyzes the request and creates an execution plan
3. **Research Phase**: Researcher Agent gathers market intelligence and competitive data
4. **Data Analysis**: Text2SQL and Python Agents analyze customer data and create insights
5. **Quality Review**: Reflection Agent reviews outputs and suggests improvements
6. **Report Generation**: Report Agent compiles findings into professional reports
7. **Memory Storage**: Memory Agent stores insights and preferences for future use

## Prerequisites

- Python 3.10+
- AWS Account with Bedrock and AgentCore access
- [Tavily API Key](https://www.tavily.com/) for web search
- Docker (for deployment)

## Quick Start

### 1. Get Tavily API Key

Sign up at [tavily.com](https://www.tavily.com/) and get your API key.

### 2. Set Environment Variables

```bash
export AWS_REGION=us-west-2
export TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Deploy to AgentCore

```bash
./deploy.sh
```

That's it! The deployment script will:
- Check prerequisites
- Create IAM roles
- Deploy to AgentCore Runtime
- Provide testing instructions

### 4. Test Deployed Agent

```bash
# Test the deployed agent
agentcore invoke '{"prompt": "Hello world!"}'

# Monitor logs
agentcore logs --follow

# Get agent status
agentcore status
```

## Local Development

### Option 1: Streamlit Web Interface (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TAVILY_API_KEY=your_api_key_here

# Start the agent API
python main.py

# In another terminal, start the web interface
streamlit run app.py
```

Open http://localhost:8501 in your browser for an interactive web interface with:
- **Real-time streaming responses** with typing indicators
- **Memory integration** across sessions (remembers preferences and context)
- **Example queries** and templates for quick start
- **Professional report generation** with automatic saving
- **Tool usage indicators** showing research progress
- **Session management** with unique user and session IDs

### Option 2: AgentCore CLI

```bash
# Install AgentCore CLI
pip install bedrock-agentcore

# Set environment variables
export TAVILY_API_KEY=your_api_key_here

# Run locally with AgentCore
agentcore run

# Test with curl
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research the latest trends in sustainable fashion", "user_id": "test_user", "session_id": "test_session"}'
```

### Option 3: Direct API Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TAVILY_API_KEY=your_api_key_here

# Run directly
python main.py

# Test with streaming
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze our customer demographics", "stream": true, "user_id": "user123", "session_id": "session456"}'
```

## Usage Examples

### Market Research
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research the latest trends in sustainable fashion for this year"}'
```

### Customer Analysis
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze our customer demographics and purchasing patterns"}'
```

### Report Generation
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a comprehensive market analysis report for this quarter"}'
```

### Competitor Analysis
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze competitor pricing strategies in the SaaS market", "user_id": "analyst1", "session_id": "research_session"}'
```

### Memory-Enabled Conversation
```bash
# First interaction - agent learns preferences
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I prefer executive summary format reports for B2B SaaS markets", "user_id": "analyst1", "session_id": "session1"}'

# Later interaction - agent remembers preferences
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a market analysis report for cloud storage solutions", "user_id": "analyst1", "session_id": "session2"}'
```

## Agent Tools and Capabilities

### Researcher Agent Tools
- **web_search**: Performs comprehensive web searches for market intelligence
- **web_extract**: Extracts detailed content from specific web pages
- **web_crawl**: Crawls websites for comprehensive data collection

### Data Analysis Tools
- **get_schema**: Retrieves database schema and table information
- **run_sqlite_query**: Executes SQL queries against customer database
- **python_repl**: Runs Python code for data analysis and visualization

### Report Generation Tools
- **file_write**: Creates and saves marketing reports and documents
- **editor**: Edits and formats professional reports

### Memory and Context
- **Short-term Memory**: Maintains conversation history within sessions using AgentCore Memory hooks
- **Long-term Memory**: Stores user preferences and marketing insights using AgentCore Memory tools
- **Automatic Extraction**: Intelligently extracts and consolidates important information
- **Cross-session Continuity**: Remembers user preferences and insights across different sessions

## Use Case Scenarios

### Scenario 1: Market Research Report
**Request**: "Research the sustainable fashion market and create a comprehensive report"

**Agent Workflow**:
1. **Planner Agent** creates execution plan: research → data analysis → report generation
2. **Researcher Agent** searches for sustainable fashion trends, market size, key players
3. **Python Agent** analyzes collected data and creates visualizations
4. **Report Agent** compiles findings into professional market research report
5. **Memory Agent** stores insights about sustainable fashion market for future reference

### Scenario 2: Customer Segmentation Analysis
**Request**: "Analyze our customer base and identify key segments for targeted marketing"

**Agent Workflow**:
1. **Planner Agent** determines need for database analysis and segmentation
2. **Text2SQL Agent** queries customer database for demographics and purchase patterns
3. **Python Agent** performs clustering analysis and creates customer segments
4. **Report Agent** generates segmentation report with recommendations
5. **Reflection Agent** reviews analysis quality and suggests additional insights

### Scenario 3: Competitive Intelligence
**Request**: "Analyze our top 3 competitors' pricing strategies and market positioning"

**Agent Workflow**:
1. **Planner Agent** plans competitive research across multiple sources
2. **Researcher Agent** gathers competitor information from web sources
3. **Python Agent** analyzes pricing data and creates comparison charts
4. **Report Agent** creates competitive analysis report with strategic recommendations
5. **Memory Agent** stores competitor insights for ongoing monitoring

## Production Best Practices

### Configuration

The Marketing Researcher Agent follows production best practices:

#### Model Configuration
- **Explicit Model Settings**: Temperature (0.3), max tokens (4000), and top_p (0.8) optimized for consistent results
- **Retry Logic**: Adaptive retry mode with exponential backoff for resilience
- **Connection Pooling**: Optimized boto3 configuration for better performance

#### Tool Management
- **Explicit Tool Specification**: All tools are explicitly listed (no auto-loading)
- **Tool Permissions**: Each tool operates with minimal required permissions
- **Tool Timeout**: Individual tool execution timeout of 60 seconds

#### Memory Management
- **Sliding Window**: Conversation history limited to 10 turns to prevent context overflow
- **Memory Caching**: Efficient memory reuse with 1-hour TTL
- **Graceful Degradation**: Continues operation even if memory initialization fails

#### Error Handling
- **Input Validation**: Validates prompt length and format
- **Retry Logic**: Automatic retry with exponential backoff for rate limiting
- **User-Friendly Messages**: Converts technical errors to user-friendly messages
- **Output Sanitization**: Basic sanitization to prevent sensitive data exposure

#### Performance Optimization
- **Streaming Support**: Uses async streaming when available for better responsiveness
- **Connection Management**: Optimized connection pooling and timeouts
- **Resource Limits**: Configurable limits for concurrent requests and execution time

### Environment Variables

Configure these environment variables for production:

```bash
# Model and AWS Configuration
export BEDROCK_MODEL_ID="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
export AWS_DEFAULT_REGION="us-west-2"
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"

# Performance Settings
export MAX_CONCURRENT_REQUESTS="10"
export REQUEST_TIMEOUT="300"
export TOOL_EXECUTION_TIMEOUT="60"

# Memory Settings
export MEMORY_CACHE_TTL="3600"
export CONVERSATION_WINDOW_SIZE="10"

# API Keys
export TAVILY_API_KEY="your_tavily_api_key_here"
```

### Monitoring

The agent includes built-in metrics for production monitoring:

- **Response Times**: Track end-to-end response latency
- **Tool Usage**: Monitor which tools are being used and their execution time
- **Error Rates**: Track different types of errors and retry attempts
- **Memory Operations**: Monitor memory creation and retrieval performance

### Security Considerations

- **Input Validation**: All user inputs are validated before processing
- **Output Sanitization**: Basic patterns are removed from responses
- **Tool Permissions**: Each tool operates with minimal required AWS permissions
- **Session Management**: Unique session IDs for request tracing and isolation

## Clean Up

```bash
# Delete deployed agent
agentcore delete

# Remove IAM role
aws iam delete-role --role-name MarketingResearcherAgentRole
```

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.