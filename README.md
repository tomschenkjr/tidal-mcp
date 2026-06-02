# TIDAL MCP Server

An MCP (Model Context Protocol) server for TIDAL music streaming. Exposes 27 TIDAL tools to Claude and other MCP clients. Runs locally over stdio or remotely over HTTP with Google OAuth.

## Connect to the hosted server

The server runs at `https://tidal-mcp.tomschenkjr.net/sse`. Add it to Claude Desktop:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tidal": {
      "type": "sse",
      "url": "https://tidal-mcp.tomschenkjr.net/sse"
    }
  }
}
```

On first connection, Claude opens a browser to complete Google OAuth. The session persists — re-authentication is required only if the server's OAuth state is reset or you revoke access.

**Claude web**: Settings → Integrations → Add MCP Server → paste the URL above.

## Tools

27 tools across 7 categories:

| Category          | Tool                          | Description                          |
|-------------------|-------------------------------|--------------------------------------|
| **Auth**          | `login`                       | OAuth browser authentication         |
| **Search**        | `search_tracks`               | Find tracks by name or artist        |
|                   | `search_albums`               | Find albums                          |
|                   | `search_artists`              | Find artists                         |
|                   | `search_playlists`            | Find public playlists                |
| **Favorites**     | `get_favorite_tracks`         | Get liked tracks                     |
|                   | `get_favorite_albums`         | Get saved albums                     |
|                   | `get_favorite_artists`        | Get followed artists                 |
|                   | `add_track_to_favorites`      | Like a track                         |
|                   | `remove_track_from_favorites` | Unlike a track                       |
|                   | `remove_album_from_favorites` | Remove a saved album                 |
| **Playlists**     | `get_user_playlists`          | List your playlists                  |
|                   | `get_playlist_tracks`         | Get tracks from a playlist           |
|                   | `create_playlist`             | Create a new playlist                |
|                   | `add_tracks_to_playlist`      | Add tracks to a playlist             |
|                   | `remove_tracks_from_playlist` | Remove tracks from a playlist        |
|                   | `update_playlist`             | Update playlist name or description  |
|                   | `delete_playlist`             | Delete a playlist                    |
| **Albums**        | `get_album_tracks`            | Get all tracks from an album         |
|                   | `get_album`                   | Get album details                    |
|                   | `get_similar_albums`          | Find similar albums                  |
| **Artists**       | `get_artist`                  | Get artist details and biography     |
|                   | `get_artist_albums`           | Get artist discography               |
|                   | `get_artist_top_tracks`       | Get an artist's popular tracks       |
|                   | `get_similar_artists`         | Find similar artists                 |
| **Recommendations** | `get_track_radio`           | Tracks similar to a seed track       |
|                   | `get_artist_radio`            | Tracks based on an artist's style    |

## Run locally

### Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
git clone https://github.com/tomschenkjr/tidal-mcp
cd tidal-mcp
uv sync
```

### Connect Claude Desktop to the local server

```json
{
  "mcpServers": {
    "tidal": {
      "command": "/path/to/uv",
      "args": ["--directory", "/path/to/tidal-mcp", "run", "tidal-mcp"]
    }
  }
}
```

Find the full path to `uv` with `which uv`.

### Authenticate with TIDAL

On first run, authenticate your TIDAL account:

```bash
uv run python authenticate.py
```

This opens a browser for TIDAL's OAuth flow and saves the session to `.tidal-sessions/`.

## Run the HTTP server locally

```bash
PORT=3000 uv run python http_server.py
```

Without `OIDC_CLIENT_ID` set, the server runs without authentication. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full environment variable reference and production deployment instructions.

## Example workflows

### Create a playlist from search results

1. `search_tracks("Radiohead Creep")` — find tracks
2. `create_playlist("My Playlist", "")` — create a playlist
3. `add_tracks_to_playlist(playlist_id, [track_ids])` — add tracks

### Add an album to a playlist

1. `search_albums("OK Computer")` — find the album
2. `get_album_tracks(album_id)` — get all tracks
3. `add_tracks_to_playlist(playlist_id, [track_ids])` — add to playlist

### Explore an artist

1. `get_artist(artist_id)` — biography and details
2. `get_artist_top_tracks(artist_id)` — popular tracks
3. `get_similar_artists(artist_id)` — discover related artists
4. `get_artist_radio(artist_id)` — tracks in a similar style

## Project structure

```
tidal-mcp/
├── pyproject.toml        # Project configuration and dependencies
├── README.md             # This file
├── http_server.py        # HTTP server with Google OAuth (ECS deployment)
├── authenticate.py       # Local TIDAL OAuth helper
├── docs/
│   └── DEPLOYMENT.md     # AWS ECS deployment guide
└── src/
    └── tidal_mcp/
        ├── __init__.py   # Package init
        ├── models.py     # Pydantic response models
        └── server.py     # MCP server with 27 tools
```

## Dependencies

| Package            | Purpose                              |
|--------------------|--------------------------------------|
| `fastmcp>=2.12.0`  | MCP protocol framework               |
| `tidalapi>=0.8.6`  | TIDAL API client                     |
| `anyio>=4.0.0`     | Async utilities                      |
| `fastapi>=0.104.0` | HTTP server framework                |
| `uvicorn>=0.24.0`  | ASGI server                          |
| `boto3>=1.26.0`    | AWS SDK (Secrets Manager, ECS)       |

## Troubleshooting

**Authentication fails locally** — Ensure tidalapi >= 0.8.6. Delete `.tidal-sessions/` and re-run `authenticate.py`.

**OAuth loop in Claude Desktop** — Clear the cached MCP connection in Claude settings and reconnect. Claude will re-register and complete a fresh OAuth flow.

**Search returns no results** — Use a simpler query (single artist name or song title).

## License

MIT

## Credits

Built with [FastMCP](https://github.com/jlowin/fastmcp) and [tidalapi](https://github.com/tamland/python-tidal).
