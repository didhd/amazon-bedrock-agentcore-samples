#!/bin/bash

# Marketing Researcher Agent Deployment Script
# Simplified deployment to Amazon Bedrock AgentCore Runtime

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_NAME="marketing-researcher-agent"
ROLE_NAME="MarketingResearcherAgentRole"
REGION="${AWS_REGION:-us-west-2}"
ENTRYPOINT="main.py"

echo -e "${BLUE}🚀 Marketing Researcher Agent Deployment${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Agent Name: ${GREEN}${AGENT_NAME}${NC}"
echo -e "Region: ${GREEN}${REGION}${NC}"
echo -e "Entrypoint: ${GREEN}${ENTRYPOINT}${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found${NC}"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Please configure AWS credentials using 'aws configure' or environment variables"
    exit 1
fi

# Check if TAVILY_API_KEY is set
if [ -z "$TAVILY_API_KEY" ]; then
    echo -e "${RED}❌ TAVILY_API_KEY environment variable not set${NC}"
    echo "Please set TAVILY_API_KEY environment variable"
    echo "Get your API key from: https://www.tavily.com/"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Please install Docker to continue"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# Install dependencies if needed
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -q bedrock-agentcore bedrock-agentcore-starter-toolkit boto3

# Create IAM role
echo -e "${YELLOW}🔐 Creating IAM role...${NC}"
python3 -c "
import boto3
import json
import time

iam = boto3.client('iam', region_name='${REGION}')
account_id = boto3.client('sts').get_caller_identity()['Account']

trust_policy = {
    'Version': '2012-10-17',
    'Statement': [{
        'Effect': 'Allow',
        'Principal': {'Service': 'bedrock-agentcore.amazonaws.com'},
        'Action': 'sts:AssumeRole',
        'Condition': {
            'StringEquals': {'aws:SourceAccount': account_id},
            'ArnLike': {'aws:SourceArn': f'arn:aws:bedrock-agentcore:${REGION}:{account_id}:*'}
        }
    }]
}

execution_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
            'Resource': '*'
        },
        {
            'Effect': 'Allow',
            'Action': ['bedrock-agentcore:*'],
            'Resource': '*'
        },
        {
            'Effect': 'Allow',
            'Action': ['ecr:GetAuthorizationToken', 'ecr:BatchCheckLayerAvailability', 'ecr:GetDownloadUrlForLayer', 'ecr:BatchGetImage'],
            'Resource': '*'
        },
        {
            'Effect': 'Allow',
            'Action': ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
            'Resource': f'arn:aws:logs:${REGION}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*'
        },
        {
            'Effect': 'Allow',
            'Action': ['xray:PutTraceSegments', 'xray:PutTelemetryRecords'],
            'Resource': '*'
        }
    ]
}

try:
    role = iam.create_role(
        RoleName='${ROLE_NAME}',
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    print('✅ Created IAM role')
except iam.exceptions.EntityAlreadyExistsException:
    print('✅ IAM role already exists')
    role = iam.get_role(RoleName='${ROLE_NAME}')

iam.put_role_policy(
    RoleName='${ROLE_NAME}',
    PolicyName='MarketingResearcherAgentPolicy',
    PolicyDocument=json.dumps(execution_policy)
)

print(f'Role ARN: {role[\"Role\"][\"Arn\"]}')
time.sleep(5)  # Wait for role propagation
"

# Deploy to AgentCore Runtime
echo -e "${YELLOW}🚀 Deploying to AgentCore Runtime...${NC}"

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --query 'Role.Arn' --output text)

# Configure AgentCore
echo -e "${YELLOW}⚙️ Configuring AgentCore...${NC}"
agentcore configure \
  --entrypoint ${ENTRYPOINT} \
  --name ${AGENT_NAME} \
  --execution-role ${ROLE_ARN} \
  --region ${REGION}

# Launch the agent
echo -e "${YELLOW}🚀 Launching agent (this may take several minutes)...${NC}"
agentcore launch

# Get the agent ARN
AGENT_ARN=$(agentcore status --format json | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'agent_arn' in data:
        print(data['agent_arn'])
    elif 'config' in data and 'agent_arn' in data['config']:
        print(data['config']['agent_arn'])
    else:
        print('Unknown')
except:
    print('Unknown')
")

# Save ARN
echo "${AGENT_ARN}" > .agent_arn

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "Agent ARN: ${GREEN}${AGENT_ARN}${NC}"
echo -e "Region: ${GREEN}${REGION}${NC}"

echo ""
echo -e "${GREEN}🎉 Marketing Researcher Agent deployed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "1. Test your agent: ${YELLOW}agentcore invoke '{\"prompt\": \"Hello world!\"}'${NC}"
echo -e "2. Monitor logs: ${YELLOW}agentcore logs --follow${NC}"
echo -e "3. Use web interface: ${YELLOW}streamlit run app.py${NC}"
echo -e "4. Use the Agent ARN for integrations"
echo ""

if [ -f ".agent_arn" ]; then
    AGENT_ARN=$(cat .agent_arn)
    echo -e "${BLUE}🏷️ Agent ARN:${NC} ${GREEN}${AGENT_ARN}${NC}"
    
    # Extract agent ID for logs
    AGENT_ID=$(echo $AGENT_ARN | cut -d'/' -f2)
    LOG_GROUP="/aws/bedrock-agentcore/runtimes/${AGENT_ID}-DEFAULT"
    echo -e "${BLUE}📊 CloudWatch Logs:${NC} ${YELLOW}${LOG_GROUP}${NC}"
    echo -e "${BLUE}📊 Tail logs:${NC} ${YELLOW}aws logs tail ${LOG_GROUP} --follow${NC}"
fi

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"