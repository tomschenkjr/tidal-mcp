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


@app.post("/api/call")
async def call_tool(request: Request, x_api_key: str = Header(None), authorization: str = Header(None)):
    """Simple HTTP API for invoking tools directly (requires API key)."""
    verify_api_key(x_api_key, authorization)
    body = await request.json()
    tool_name = body.get("tool", "")
    arguments = body.get("arguments", {})

    try:
        from src.tidal_mcp.server import (
            get_user_playlists,
            get_playlist_tracks,
            create_playlist,
            add_tracks_to_playlist,
            search_tracks,
            search_playlists,
            search_artists,
            search_albums,
            get_favorite_tracks,
            add_track_to_favorites,
            remove_track_from_favorites,
            get_favorite_albums,
            remove_album_from_favorites,
            get_favorite_artists,
            get_album_tracks,
            get_track_radio,
            get_artist_radio,
            get_artist,
            get_artist_albums,
            get_artist_top_tracks,
            get_similar_artists,
            get_album,
            get_similar_albums,
            update_playlist,
            remove_tracks_from_playlist,
            delete_playlist,
        )

        tools_map = {
            "get_user_playlists": get_user_playlists,
            "get_playlist_tracks": get_playlist_tracks,
            "create_playlist": create_playlist,
            "add_tracks_to_playlist": add_tracks_to_playlist,
            "search_tracks": search_tracks,
            "search_playlists": search_playlists,
            "search_artists": search_artists,
            "search_albums": search_albums,
            "get_favorite_tracks": get_favorite_tracks,
            "add_track_to_favorites": add_track_to_favorites,
            "remove_track_from_favorites": remove_track_from_favorites,
            "get_favorite_albums": get_favorite_albums,
            "remove_album_from_favorites": remove_album_from_favorites,
            "get_favorite_artists": get_favorite_artists,
            "get_album_tracks": get_album_tracks,
            "get_track_radio": get_track_radio,
            "get_artist_radio": get_artist_radio,
            "get_artist": get_artist,
            "get_artist_albums": get_artist_albums,
            "get_artist_top_tracks": get_artist_top_tracks,
            "get_similar_artists": get_similar_artists,
            "get_album": get_album,
            "get_similar_albums": get_similar_albums,
            "update_playlist": update_playlist,
            "remove_tracks_from_playlist": remove_tracks_from_playlist,
            "delete_playlist": delete_playlist,
        }

        if tool_name not in tools_map:
            return {"error": f"Unknown tool: {tool_name}"}, 404

        tool_func = tools_map[tool_name]
        result = await tool_func(**arguments)
        return {"result": result}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}, 500


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
