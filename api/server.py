from __future__ import annotations

import asyncio
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from rich.console import Console
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount, Match
from starlette.types import Scope

from NTEPilot.config.config import DEFAULT_INSTANCE_NAME, PROJECT_ROOT
from NTEPilot.instance import Instance
from utils.logger import logger

from api.config import CONFIG_FIELDS, TASKS
from api.task_runner import TaskRunner

STATIC_DIR = PROJECT_ROOT / "frontend" / ".static"

class ConfigStore:
    def list_instances(self) -> list[dict[str, Any]]:
        return Instance.list_instances()

    def schema(self, instance: str) -> dict[str, Any]:
        config = Instance(instance_name=instance, create_device=False).config
        return {
            "type": "config.schema",
            "instance": config.name,
            "fields": [field.to_json(config) for field in CONFIG_FIELDS],
        }

    def update(self, instance: str, values: dict[str, Any]) -> dict[str, Any]:
        config = Instance(instance_name=instance, create_device=False).config
        config.update(values, save=True)
        return self.schema(config.name)


def render_rich_ansi(record: logging.LogRecord) -> str:
    stream = io.StringIO()
    console = Console(
        file=stream,
        force_terminal=True,
        color_system="truecolor",
        width=160,
        legacy_windows=False,
    )
    console.print(record.getMessage(), markup=True, highlight=False, end="")
    return stream.getvalue()


class BroadcastLogHandler(logging.Handler):
    def __init__(self, app: "NTEPilotWebSocketApp"):
        super().__init__()
        self.app = app

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.app.broadcast_threadsafe(
                {
                    "type": "log",
                    "event": {
                        "level": self._level(record.levelname),
                        "source": record.name,
                        "message": record.getMessage(),
                        "ansi": render_rich_ansi(record),
                    },
                }
            )
        except Exception:
            pass

    def _level(self, level_name: str) -> str:
        level = level_name.lower()
        if level == "warning":
            return "warning"
        if level in {"debug", "info", "error"}:
            return level
        return "info"

class HTTPMount(Mount):
    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        if scope["type"] != "http":
            return Match.NONE, {}
        return super().matches(scope)


class NTEPilotWebSocketApp:
    def __init__(self, static_dir: Path = STATIC_DIR):
        self.static_dir = static_dir
        self.clients: set[WebSocket] = set()
        self.config_store = ConfigStore()
        self.task_runner = TaskRunner(self)
        self.loop: asyncio.AbstractEventLoop | None = None
        self.log_handler = BroadcastLogHandler(self)
        logger.addHandler(self.log_handler)

    def asgi_app(self) -> FastAPI:
        app = FastAPI()

        @app.on_event("startup")
        async def startup() -> None:
            self.loop = asyncio.get_running_loop()

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await self.websocket_handler(websocket)

        app.routes.append(HTTPMount("/", StaticFiles(directory=str(self.static_dir), html=True), name="frontend"))
        return app

    async def websocket_handler(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.clients.add(websocket)
        await self.send_initial_state(websocket)
        try:
            while True:
                raw = await websocket.receive_text()
                await self.handle_message(websocket, raw)
        except WebSocketDisconnect:
            self.clients.discard(websocket)

    async def send_initial_state(self, websocket: WebSocket) -> None:
        instance = DEFAULT_INSTANCE_NAME
        await self.send(
            websocket,
            {
                "type": "hello",
                "app": "NTEPilot",
                "version": "0.4.0",
                "currentInstance": instance,
                "instances": self.config_store.list_instances(),
                "status": self.status_payload(instance),
            },
        )
        await self.send(websocket, {"type": "instance.list", "instances": self.config_store.list_instances()})
        await self.send(websocket, self.config_store.schema(instance))
        await self.send(websocket, {"type": "task.catalog", "tasks": TASKS})

    async def handle_message(self, websocket: WebSocket, raw: str | bytes) -> None:
        message: dict[str, Any] = {}
        try:
            message = json.loads(raw)
            message_type = message.get("type")
            request_id = message.get("requestId")
            instance = str(message.get("instance") or DEFAULT_INSTANCE_NAME)

            if message_type == "hello":
                return
            if message_type == "instance.list":
                await self.send(websocket, {"type": "instance.list", "instances": self.config_store.list_instances()})
                return
            if message_type == "instance.create":
                name = str(message.get("name") or DEFAULT_INSTANCE_NAME)
                config = Instance.create(name, create_device=False).config
                await self.broadcast({"type": "instance.list", "instances": self.config_store.list_instances()})
                await self.send(websocket, self.config_store.schema(config.name))
                await self.send_result(websocket, request_id, True, {"instance": config.name})
                return
            if message_type == "config.get":
                await self.send(websocket, self.config_store.schema(instance))
                return
            if message_type == "config.update":
                payload = self.config_store.update(instance, message.get("values", {}))
                logger.info("Config saved for instance %s", payload["instance"])
                await self.send(websocket, payload)
                await self.broadcast({"type": "status", "instance": payload["instance"], "status": self.status_payload(payload["instance"])})
                await self.send_result(websocket, request_id, True, {"updated": True, "instance": payload["instance"]})
                return
            if message_type == "task.list":
                await self.send(websocket, {"type": "task.catalog", "tasks": TASKS})
                return
            if message_type == "task.start":
                result = self.task_runner.start(
                    instance,
                    str(message.get("taskId", "")),
                    message.get("values") if isinstance(message.get("values"), dict) else None,
                )
                await self.send_result(websocket, request_id, True, result)
                return
            if message_type == "task.stop":
                result = self.task_runner.stop(instance, str(message.get("taskId", "")))
                await self.send_result(websocket, request_id, True, result)
                return

            raise ValueError(f"Unknown message type: {message_type}")
        except Exception as exc:
            logger.error("WebSocket message failed: %s", exc)
            await self.send_result(websocket, message.get("requestId"), False, error=str(exc))

    async def send_result(
        self,
        websocket: WebSocket,
        request_id: str | None,
        ok: bool,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        if not request_id:
            return
        payload: dict[str, Any] = {"type": "call.result", "requestId": request_id, "ok": ok}
        if ok:
            payload["result"] = result
        else:
            payload["error"] = error
        await self.send(websocket, payload)

    def status_payload(self, instance: str) -> dict[str, Any]:
        config = Instance(instance_name=instance, create_device=False).config
        return {
            "device": config.serial,
            "packageName": config.package_name,
            "activeTask": self.task_runner.active_task_id(config.name),
        }

    async def send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        await websocket.send_text(json.dumps(self.with_time(payload), ensure_ascii=False))

    async def broadcast(self, payload: dict[str, Any]) -> None:
        if not self.clients:
            return
        message = json.dumps(self.with_time(payload), ensure_ascii=False)
        disconnected: list[WebSocket] = []
        for client in list(self.clients):
            try:
                await client.send_text(message)
            except Exception:
                disconnected.append(client)
        for client in disconnected:
            self.clients.discard(client)

    def broadcast_threadsafe(self, payload: dict[str, Any]) -> None:
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(payload), self.loop)

    def with_time(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("type") == "log":
            payload.setdefault("event", {}).setdefault("time", datetime.now().isoformat())
        if payload.get("type") == "task":
            payload.setdefault("task", {}).setdefault("updatedAt", datetime.now().isoformat())
        return payload


def create_app() -> FastAPI:
    return NTEPilotWebSocketApp().asgi_app()


def main() -> None:
    import uvicorn

    config = Instance(instance_name=DEFAULT_INSTANCE_NAME, create_device=False).config
    uvicorn.run(create_app(), host=config.websocket_host, port=int(config.websocket_port), log_level="info")


if __name__ == "__main__":
    main()
