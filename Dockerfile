# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /pdf-ai-chatbot

# Copy requirements.txt
COPY requirements.txt .

# Make sure backend is a Python package
RUN mkdir -p backend && touch backend/__init__.py
RUN mkdir -p backend/src/common/ && touch backend/src/common/__init__.py

# Copy the files in the backend directory to /pdf-ai-chatbot/backend in the container
COPY backend/src/common/logger.py ./backend/src/common/logger.py
COPY backend/src/common/posm_service_azure.py ./backend/src/common/posm_service_azure.py
COPY backend/app.py ./backend/app.py

# Set the Python module search path
ENV PYTHONPATH=/pdf-ai-chatbot/backend

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Set up health checks
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${WEBSITES_PORT:-8000}/health || exit 1

# Expose ports
EXPOSE 8000

# Startup command (uvicorn using FastAPI)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
