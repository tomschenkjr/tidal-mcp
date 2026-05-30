#!/usr/bin/env python
"""
HTTP server wrapper for TIDAL MCP.
Exposes the MCP server over HTTP with FastAPI + SSE transport.
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

# Import the MCP server
from src.tidal_mcp.server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    yield


app = FastAPI(title="TIDAL MCP", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tidal-mcp"}


@app.get("/sse")
async def sse():
    """SSE transport for MCP protocol."""
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
