#!/usr/bin/env python
"""
HTTP server wrapper for TIDAL MCP.
Exposes the MCP server over HTTP with FastAPI + SSE transport.
Requires API key authentication for security.
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, status
from mcp.server.sse import SseServerTransport

# Import the MCP server
from src.tidal_mcp.server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    yield


app = FastAPI(title="TIDAL MCP", lifespan=lifespan)

# API key from environment (set in Lambda or ECS task definition)
API_KEY = os.getenv("TIDAL_MCP_API_KEY", "")

sse_transport = SseServerTransport("/messages/")


def verify_api_key(x_api_key: str = Header(None), authorization: str = Header(None)) -> None:
    """Verify API key from x-api-key header or Authorization: Bearer <token>."""
    if not API_KEY:
        return

    bearer_token = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization[7:]

    if bearer_token == API_KEY or x_api_key == API_KEY:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key"
    )


@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "tidal-mcp"}


@app.get("/sse")
async def handle_sse(request: Request, x_api_key: str = Header(None), authorization: str = Header(None)):
    """SSE transport for MCP protocol — server-to-client stream (requires API key)."""
    verify_api_key(x_api_key, authorization)
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp._mcp_server.run(
            streams[0], streams[1],
            mcp._mcp_server.create_initialization_options()
        )


@app.post("/messages/")
async def handle_messages(request: Request, x_api_key: str = Header(None), authorization: str = Header(None)):
    """SSE transport for MCP protocol — client-to-server messages (requires API key)."""
    verify_api_key(x_api_key, authorization)
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )


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
