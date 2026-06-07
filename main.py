from __future__ import annotations

import asyncio

import uvicorn

from api.server import create_app
from NTEPilot.config.config import DEFAULT_INSTANCE_NAME
from NTEPilot.instance import Instance


async def async_main() -> None:
    Instance.ensure_default_instance()
    config = Instance(instance_name=DEFAULT_INSTANCE_NAME, create_device=False).config
    server_config = uvicorn.Config(
        create_app(),
        host=config.websocket_host,
        port=int(config.websocket_port),
        log_level="info",
    )
    server = uvicorn.Server(server_config)
    await server.serve()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
