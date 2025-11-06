FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -e .

# Exposes the FastAPI port
EXPOSE 8001

# run the commands to start both services
CMD ["bash", "-c", "python prod_assistant/mcp_servers/product_search_server.py & python prod_assistant/router/main.py"]