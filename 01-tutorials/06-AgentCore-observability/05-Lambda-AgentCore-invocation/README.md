# Lambda AgentCore Invocation with CloudWatch Observability

This tutorial demonstrates how to invoke Strands agents hosted on Amazon Bedrock AgentCore Runtime from AWS Lambda functions, with full CloudWatch observability enabled through X-Ray tracing and GenAI Observability.

## Overview

Learn how to build a serverless architecture where Lambda functions invoke MCP-enabled agents running on AgentCore Runtime, with complete visibility into both Lambda execution and agent behavior through CloudWatch.

## Project Structure

```
05-Lambda-AgentCore-invocation/
├── agentcore_observability_lambda.ipynb  # Main tutorial notebook
├── lambda_agentcore_invoker.py           # Lambda function code
├── mcp_agent_multi_server.py             # Agent with multiple MCP servers
├── Dockerfile                            # Container image for Lambda
├── requirements.txt                      # Python dependencies
├── .dockerignore                         # Docker ignore patterns
└── .gitignore                            # Git ignore patterns
```

## Tutorial Details

| Information         | Details                                                                          |
|:-------------------|:----------------------------------------------------------------------------------|
| Tutorial type      | Conversational                                                                   |
| Agent type         | Single                                                                           |
| Agentic Framework  | Strands Agents                                                                   |
| LLM model          | Anthropic Claude Sonnet 3.7                                                      |
| Tutorial components| Lambda invocation, AgentCore Runtime, MCP servers, CloudWatch Observability     |
| Example complexity | Advanced                                                                         |
| SDK used           | Amazon BedrockAgentCore Python SDK, boto3, AWS Lambda                           |

## Architecture

```
API/User → AWS Lambda → AgentCore Runtime → Strands Agent → MCP Servers (AWS Docs + CDK)
                ↓                                    ↓
          CloudWatch                          CloudWatch
          (X-Ray Traces)                      (Gen AI Observability)
```

## Key Features

* Integrating multiple MCP servers (AWS Documentation + AWS CDK) with Strands Agents
* Hosting agents on Amazon Bedrock AgentCore Runtime
* Invoking hosted agents from AWS Lambda functions
* Configuring CloudWatch Gen AI Observability for agent monitoring
* Enabling AWS X-Ray tracing for Lambda functions
* Viewing traces, spans, and metrics in CloudWatch console

## What You'll Learn

1. How to deploy an MCP-enabled agent to AgentCore Runtime
2. How to create a Lambda function that invokes the runtime agent
3. How to configure X-Ray sampling for Lambda observability
4. How to enable CloudWatch Gen AI Observability for your agents
5. How to view and analyze traces showing agent execution flow

## Prerequisites

* Python 3.10+
* AWS credentials configured with appropriate permissions
* Amazon Bedrock AgentCore SDK
* Strands Agents with OTEL support
* MCP libraries
* Permissions to create Lambda functions and IAM roles
* CloudWatch Transaction Search enabled

## Getting Started

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Enable CloudWatch Transaction Search (one-time setup per AWS account)

3. Open and run the Jupyter notebook:
   ```bash
   jupyter notebook agentcore_observability_lambda.ipynb
   ```

4. Follow the step-by-step instructions in the notebook to:
   - Configure CloudWatch Transaction Search
   - Create and deploy the MCP agent
   - Build and deploy the Lambda function
   - Test the integration
   - View traces in CloudWatch

## Components

### Lambda Function (`lambda_agentcore_invoker.py`)
Serverless function that receives user prompts and invokes the AgentCore Runtime agent. Includes error handling, logging, and X-Ray tracing integration.

### MCP Agent (`mcp_agent_multi_server.py`)
Strands agent configured with multiple MCP servers (AWS Documentation and AWS CDK) and OpenTelemetry instrumentation for observability.

### Dockerfile
Container image definition for deploying the Lambda function with all required dependencies.

## Usage

The Lambda function expects the following event format:

```json
{
  "prompt": "Your question here",
  "sessionId": "optional-session-id"
}
```

Response format:

```json
{
  "statusCode": 200,
  "body": {
    "response": "Agent's response",
    "sessionId": "session-id",
    "agentArn": "agent-arn"
  }
}
```

## Observability Features

* **X-Ray Tracing**: Track Lambda execution and downstream service calls
* **CloudWatch Logs**: Detailed logging of Lambda function execution
* **GenAI Observability**: Visualize agent workflow, tool calls, and LLM interactions
* **Transaction Search**: Query and analyze traces across your entire application

## Clean Up

After completing the tutorial, delete the following resources to avoid unnecessary charges:

1. Lambda function and associated IAM roles
2. AgentCore Runtime agent and endpoint
3. CloudWatch Log groups
4. Container images in ECR (if applicable)

## License

This project is licensed under the terms specified in the repository.
