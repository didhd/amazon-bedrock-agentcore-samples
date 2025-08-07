from utils import create_agentcore_role
from boto3.session import Session
from bedrock_agentcore_starter_toolkit import Runtime

# Create IAM Role for AgentCore Runtime
agent_name="agentcore_strands"
agentcore_iam_role = create_agentcore_role(agent_name=agent_name)

# Configure Runtime deployment
boto_session = Session()
region = boto_session.region_name

agentcore_runtime = Runtime()

agentcore_runtime.configure(
    entrypoint="main.py",
    execution_role=agentcore_iam_role['Role']['Arn'],
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name
)

agentcore_runtime.launch()
