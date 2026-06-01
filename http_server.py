#!/usr/bin/env python
"""
HTTP server wrapper for TIDAL MCP.
Exposes the MCP server over HTTP with FastAPI + SSE transport.
Uses AWS Cognito M2M (client_credentials) for authentication when
COGNITO_JWKS_URI is set; runs unauthenticated for local development.
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.http import create_sse_app

# Import the MCP server
from src.tidal_mcp.server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    yield


app = FastAPI(title="TIDAL MCP", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "tidal-mcp"}


jwks_uri = os.getenv("COGNITO_JWKS_URI")
auth = (
    JWTVerifier(
        jwks_uri=jwks_uri,
        issuer=os.environ["COGNITO_ISSUER"],
        audience=os.environ["COGNITO_AUDIENCE"],
        required_scopes=["tidal-mcp/access"],
    )
    if jwks_uri
    else None
)

sse_app = create_sse_app(
    server=mcp,
    message_path="/messages/",
    sse_path="/sse",
    auth=auth,
)
app.mount("/", sse_app)


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

        # Serialize Pydantic models to dicts (mode='json' for recursive serialization)
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump(mode='json')
        elif hasattr(result, 'dict'):
            result_dict = result.dict()
        else:
            result_dict = result

        return {"result": result_dict}
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
