import ctypes
import threading
import traceback
from typing import Any

from NTEPilot.instance import Instance
from NTEPilot.tools.base import ToolSpec
from NTEPilot.tools.registry import get_tool
from utils.logger import logger


class TaskAbort(BaseException):
    pass


def raise_thread_exception(thread: threading.Thread, exception: type[BaseException]) -> None:
    if thread.ident is None:
        raise RuntimeError(f"Thread is not started: {thread.name}")
    result = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(thread.ident),
        ctypes.py_object(exception),
    )
    if result == 0:
        raise RuntimeError(f"Thread is not alive: {thread.name}")
    if result > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread.ident), None)
        raise RuntimeError(f"Failed to abort thread safely: {thread.name}")


class TaskRunner:
    def __init__(self, app):
        self.app = app
        self._threads: dict[str, tuple[str, threading.Thread]] = {}
        self._lock = threading.Lock()

    def active_task_id(self, instance: str) -> str:
        running = self._threads.get(instance)
        if running is not None:
            task_id, thread = running
            if thread.is_alive():
                return task_id
        return "idle"

    def start(self, instance: str, task_id: str, values: dict[str, Any] | None = None) -> dict[str, Any]:
        tool = get_tool(task_id)

        config = Instance(instance_name=instance, create_device=False).config
        if values:
            config.update(values, save=True)

        with self._lock:
            running = self._threads.get(config.name)
            if running is not None and running[1].is_alive():
                raise RuntimeError(f"Task already running for instance: {config.name}")

            thread = threading.Thread(
                target=self._run_task,
                args=(config, tool),
                name=f"NTEPilotTask-{tool.id}-{config.name}",
                daemon=True,
            )
            self._threads[config.name] = (tool.id, thread)
            thread.start()

        self.app.broadcast_threadsafe(self.task_event(config.name, tool.id, "running", "任务已启动"))
        self.app.broadcast_threadsafe(self.status_event(config.name))
        return {"instance": config.name, "taskId": tool.id, "status": "running"}

    def stop(self, instance: str, task_id: str) -> dict[str, Any]:
        tool = get_tool(task_id)

        config = Instance(instance_name=instance, create_device=False).config
        with self._lock:
            running = self._threads.get(config.name)
            if running is None:
                raise RuntimeError(f"No running task for instance: {config.name}")

            active_task_id, thread = running
            if active_task_id != tool.id:
                raise RuntimeError(f"Task {active_task_id} is running for instance: {config.name}")
            if not thread.is_alive():
                raise RuntimeError(f"No running task for instance: {config.name}")
            raise_thread_exception(thread, TaskAbort)

        self.app.broadcast_threadsafe(self.task_event(config.name, tool.id, "cancelled", "任务已强制中止"))
        self.app.broadcast_threadsafe(self.status_event(config.name))
        return {"instance": config.name, "taskId": tool.id, "status": "aborted"}

    def _run_task(self, config: Any, tool: ToolSpec) -> None:
        try:
            logger.info("开始运行任务 %s：%s", tool.title, config.name)
            tool.run(config=config)
            self.app.broadcast_threadsafe(self.task_event(config.name, tool.id, "done", "任务已完成"))
        except TaskAbort:
            logger.warning("任务 %s 已被强制中止：%s", tool.title, config.name)
            self.app.broadcast_threadsafe(self.task_event(config.name, tool.id, "cancelled", "任务已强制中止"))
        except Exception as exc:
            logger.error("任务 %s 失败：%s，%s", tool.title, config.name, exc)
            logger.debug(traceback.format_exc())
            self.app.broadcast_threadsafe(self.task_event(config.name, tool.id, "error", str(exc)))
        finally:
            with self._lock:
                self._threads.pop(config.name, None)
            self.app.broadcast_threadsafe(self.status_event(config.name))

    def task_event(self, instance: str, task_id: str, status: str, detail: str = "") -> dict[str, Any]:
        title = get_tool(task_id).title
        return {
            "type": "task",
            "instance": instance,
            "task": {
                "id": task_id,
                "title": title,
                "status": status,
                "detail": detail,
            },
        }

    def status_event(self, instance: str) -> dict[str, Any]:
        config = Instance(instance_name=instance, create_device=False).config
        return {
            "type": "status",
            "instance": config.name,
            "status": {
                "device": config.serial,
                "packageName": config.package_name,
                "activeTask": self.active_task_id(config.name),
            },
        }
