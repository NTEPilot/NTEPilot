from __future__ import annotations

import argparse
import asyncio

import uvicorn

from api.server import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NTEPilot server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server listen host.")
    parser.add_argument("--port", default=9150, type=int, help="Server listen port.")
    return parser.parse_args()


async def async_main(host: str, port: int) -> None:
    server_config = uvicorn.Config(
        create_app(),
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(server_config)
    await server.serve()


def main() -> None:
    args = parse_args()
    asyncio.run(async_main(args.host, args.port))


if __name__ == "__main__":
    main()
