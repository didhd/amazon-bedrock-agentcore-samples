import uuid
import os
from botocore.config import Config as BotocoreConfig

# A unique session ID for this run, used for observability and tracing.
SESSION_ID = str(uuid.uuid4())

# Production-ready boto client configuration
BOTO_CONFIG = BotocoreConfig(
    retries={
        "max_attempts": 5,  # Increased for production resilience
        "mode": "adaptive",  # Adaptive retry mode for better handling
    },
    connect_timeout=15,  # Slightly increased for stability
    read_timeout=300,  # 5 minutes for long-running tasks
    max_pool_connections=50,  # Increased connection pool for better performance
)

# Production model configuration - using model ID string for explicit configuration
BEDROCK_MODEL = os.getenv(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
)

# AWS Region configuration
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")

# Production environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rate limiting and performance settings
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "300"))

# Memory settings
MEMORY_CACHE_TTL = int(os.getenv("MEMORY_CACHE_TTL", "3600"))  # 1 hour
CONVERSATION_WINDOW_SIZE = int(os.getenv("CONVERSATION_WINDOW_SIZE", "10"))

# Tool execution settings
TOOL_EXECUTION_TIMEOUT = int(
    os.getenv("TOOL_EXECUTION_TIMEOUT", "60")
)  # 1 minute per tool
