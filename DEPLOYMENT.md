# Deployment Guide

This document describes how to deploy the SHL Assessment Recommendation Agent to production.

## Local Deployment (Without Docker)

1. **Install Requirements**: Ensure Python 3.11+ is installed.
2. **Environment Variables**: Copy `.env.example` to `.env` and fill in the values, particularly `OPENROUTER_API_KEY` or `GROQ_API_KEY`.
3. **Install Dependencies**:
   ```bash
   pip install -e .
   ```
4. **Run Server**:
   ```bash
   python scripts/run_server.py
   ```
   Or via `make run`.

## Docker Deployment

The application provides a multi-stage `Dockerfile` optimized for production, using a non-root user for security.

### Build the Image
```bash
make docker-build
# or
docker build -t shl-agent:latest .
```

### Run the Container
```bash
docker run -d -p 8000:8000 --env-file .env --name shl_agent shl-agent:latest
# or
make docker-run
```

## Docker Compose

For standard production or staging environments, `docker-compose` simplifies the deployment.

1. Ensure `.env` is properly configured.
2. Start the service:
   ```bash
   make docker-compose-up
   # or
   docker-compose up -d
   ```
3. Stop the service:
   ```bash
   make docker-compose-down
   # or
   docker-compose down
   ```

## Production Checklist

- **Environment Variables**: Ensure `LOG_LEVEL` is set to `info` or `warning`, and all API keys are secured. Never commit `.env`.
- **Health Verification**: Check the `/health` endpoint to ensure the catalog, embedding index, and BM25 index are successfully loaded.
- **Restart Policy**: The Docker Compose file configures `restart: unless-stopped`.
- **Port Mapping**: Ensure port 8000 (or the port defined in `.env`) is exposed correctly to your reverse proxy (e.g., Nginx, Traefik).

## Troubleshooting

- **Index Not Loaded**: If `/health` reports that indexes are not loaded, verify that the `catalog/catalog.json` exists and the container has sufficient memory to instantiate sentence-transformers.
- **LLM Provider Unavailable**: If `POST /chat` returns `503`, check your network connection or the status of the selected LLM provider (OpenRouter or Groq), and verify your API keys.
