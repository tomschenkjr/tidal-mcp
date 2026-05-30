#!/usr/bin/env python
"""
HTTP server wrapper for TIDAL MCP.
Exposes the MCP server over HTTP with FastAPI + SSE transport.
Requires API key authentication for security.
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import StreamingResponse

# Import the MCP server
from src.tidal_mcp.server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    yield


app = FastAPI(title="TIDAL MCP", lifespan=lifespan)

# API key from environment (set in Lambda or ECS task definition)
API_KEY = os.getenv("TIDAL_MCP_API_KEY", "")


def verify_api_key(x_api_key: str = Header(None)) -> None:
    """Verify API key on protected endpoints."""
    if not API_KEY:
        # If no API key is set, allow all requests (local development)
        return

    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )


@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "tidal-mcp"}


@app.get("/sse")
async def sse(_: None = Header(None, alias="x-api-key")):
    """SSE transport for MCP protocol (requires API key)."""
    verify_api_key(_)

    async def generate():
        async with mcp.server_session() as session:
            async for message in session:
                yield f"data: {message}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")


def run():
    """Run the HTTP server."""
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    run()
