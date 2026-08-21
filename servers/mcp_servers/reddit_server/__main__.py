"""Reddit MCP server.

    python -m mcp_servers.reddit_server
"""

from .server import build

build().run("stdio")
