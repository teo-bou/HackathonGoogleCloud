# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /agents

# Copy requirements (if any)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
# The API key is expected to be passed at runtime, e.g., from a .env file
ARG GOOGLE_API_KEY
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}


# Expose port (change if your API server uses a different port)
EXPOSE 8000

# Make start script executable
RUN chmod +x ./start.sh

# Start the agent in api_server mode
CMD ["/bin/sh", "./start.sh"]