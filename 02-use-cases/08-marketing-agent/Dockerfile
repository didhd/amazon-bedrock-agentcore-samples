FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app



COPY requirements.txt requirements.txt
# Install from requirements file
RUN pip install -r requirements.txt




RUN pip install aws-opentelemetry-distro>=0.10.0


# Set AWS region environment variable

ENV AWS_REGION=us-west-2
ENV AWS_DEFAULT_REGION=us-west-2


# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

ENV TAVILY_API_KEY="YOUR TAVILY KEY"

ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
ENV OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"

ENV OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=aws-lambda,boto3sqs,botocore

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080
EXPOSE 8000

# Copy entire project (respecting .dockerignore)
COPY . .

# Use the full module path

CMD ["opentelemetry-instrument", "python", "-m", "main"]
