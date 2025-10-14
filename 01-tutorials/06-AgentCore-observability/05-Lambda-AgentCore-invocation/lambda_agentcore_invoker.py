import json
import boto3
import os
import traceback
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to invoke AgentCore Runtime agent.

    Expected event format:
    {
        "prompt": "Your question here",
        "sessionId": "optional-session-id"  # Optional
    }
    """

    # Initialize boto3 client inside handler for better Lambda performance
    bedrock_agentcore_client = boto3.client('bedrock-agentcore')

    try:
        # Get environment variables
        agent_arn = os.environ.get('AGENT_ARN')
        endpoint_arn = os.environ.get('ENDPOINT_ARN')

        print(f"Lambda function started")
        print(f"Agent ARN: {agent_arn}")
        print(f"Endpoint ARN: {endpoint_arn}")

        if not agent_arn or not endpoint_arn:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Configuration Error',
                    'message': 'Missing AGENT_ARN or ENDPOINT_ARN environment variables'
                })
            }

        # Parse input
        if isinstance(event, str):
            event = json.loads(event)

        prompt = event.get('prompt', '')
        session_id = event.get('sessionId', context.aws_request_id)

        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'Missing prompt in request'
                })
            }

        print(f"Processing prompt: {prompt}")
        print(f"Session ID: {session_id}")

        # Prepare payload for AgentCore
        payload = json.dumps({"prompt": prompt})

        # Invoke AgentCore Runtime
        print(f"Invoking AgentCore Runtime...")
        response = bedrock_agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=endpoint_arn,
            runtimeSessionId=session_id,
            payload=payload
        )

        print(f"Response received from AgentCore")
        print(f"Response keys: {list(response.keys())}")

        # Parse response - handle StreamingBody
        agent_response = None

        if 'response' in response:
            response_body = response['response']
            print(f"Response body type: {type(response_body).__name__}")

            # Check if it's a StreamingBody (has read method)
            if hasattr(response_body, 'read'):
                # It's a StreamingBody, read it
                raw_data = response_body.read()
                print(f"Raw data type after read: {type(raw_data).__name__}")

                if isinstance(raw_data, bytes):
                    agent_response = raw_data.decode('utf-8')
                else:
                    agent_response = str(raw_data)

            elif isinstance(response_body, list) and len(response_body) > 0:
                # It's a list
                if isinstance(response_body[0], bytes):
                    agent_response = response_body[0].decode('utf-8')
                else:
                    agent_response = str(response_body[0])

            elif isinstance(response_body, bytes):
                agent_response = response_body.decode('utf-8')

            elif isinstance(response_body, str):
                agent_response = response_body

            else:
                agent_response = str(response_body)

        if not agent_response:
            agent_response = "No response from agent"
            print("Warning: No response extracted from AgentCore")

        print(f"Agent response received (length: {len(agent_response)} chars)")
        print(f"Agent response preview: {agent_response[:100]}...")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': agent_response,
                'sessionId': session_id,
                'agentArn': agent_arn
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"AWS ClientError: {error_code}")
        print(f"Error message: {error_message}")
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_code,
                'message': error_message
            })
        }

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        traceback.print_exc()

        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid JSON',
                'message': str(e)
            })
        }

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'InternalError',
                'message': str(e),
                'type': type(e).__name__
            })
        }
