from .server import serve


def main():
    """MCP Reddit Server - Reddit API functionality for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to access Reddit public API"
    )

    args = parser.parse_args()
    asyncio.run(serve())


if __name__ == "__main__":
    main()
