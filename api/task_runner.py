from __future__ import annotations

import ctypes
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

from NTEPilot.config.schema import TaskSection, create_runner, get_task_title
from utils.exceptions import GameBugError, GameNotRunningError, GameStuckError, RequestHumanTakeover
from utils.logger import logger


class TaskAbort(BaseException):
    pass


class TaskBusyError(RuntimeError):
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


@dataclass
class TaskHandle:
    instance: str
    section: TaskSection
    task_id: str
    title: str
    source: str
    plan_id: str | None = None
    done: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None
    status: str = "queued"
    detail: str = ""


class TaskRunner:
    max_attempts = 3
    retry_delay = 3.0

    def __init__(self, app: Any, config_store: Any):
        self.app = app
        self.config_store = config_store
        self._tasks: dict[str, TaskHandle] = {}
        self._devices: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._device_lock = threading.Lock()

    def active_task_id(self, instance: str) -> str:
        handle = self._active_handle(instance)
        return handle.task_id if handle else "idle"

    def active_source(self, instance: str) -> str | None:
        handle = self._active_handle(instance)
        return handle.source if handle else None

    def is_idle(self, instance: str) -> bool:
        return self._active_handle(instance) is None

    def start(self, instance: str, task_id: str, values: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.config_store.get(instance)
        if values:
            config.update(values, save=True)

        handle = self._start(config.name, "tools", task_id, source="manual")
        return {"instance": config.name, "taskId": handle.task_id, "status": "running"}

    def start_scheduled(self, instance: str, task_id: str, plan_id: str) -> TaskHandle:
        config = self.config_store.get(instance)
        return self._start(config.name, "schedule", task_id, source="scheduler", plan_id=plan_id)

    def stop(self, instance: str, task_id: str | None = None) -> dict[str, Any]:
        config = self.config_store.get(instance)
        with self._lock:
            handle = self._tasks.get(config.name)
            if handle is None or handle.thread is None or not handle.thread.is_alive():
                raise RuntimeError(f"No running task for instance: {config.name}")
            if task_id and handle.task_id != task_id:
                raise RuntimeError(f"Task {handle.task_id} is running for instance: {config.name}")
            raise_thread_exception(handle.thread, TaskAbort)
            handle.status = "cancelled"
            handle.detail = "任务已强制中止"

        self.app.broadcast_threadsafe(self.task_event(handle, "cancelled", handle.detail))
        self.app.broadcast_threadsafe(self.status_event(config.name))
        return {"instance": config.name, "taskId": handle.task_id, "status": "aborted"}

    def close_app(self, instance: str) -> None:
        config = self.config_store.get(instance)
        try:
            device = self._device(config.name)
            device.app_stop_adb()
            logger.info("App closed for instance %s", config.name)
        except Exception as exc:
            logger.warning("Failed to close app for instance %s: %s", config.name, exc)
            logger.debug(traceback.format_exc())

    def _start(
        self,
        instance: str,
        section: TaskSection,
        task_id: str,
        source: str,
        plan_id: str | None = None,
    ) -> TaskHandle:
        title = get_task_title(section, task_id)
        handle = TaskHandle(instance=instance, section=section, task_id=task_id, title=title, source=source, plan_id=plan_id)
        thread = threading.Thread(
            target=self._run_task,
            args=(handle,),
            name=f"NTEPilotTask-{section}-{task_id}-{instance}",
            daemon=True,
        )
        handle.thread = thread

        with self._lock:
            running = self._tasks.get(instance)
            if running is not None and running.thread is not None and running.thread.is_alive():
                raise TaskBusyError(f"Task already running for instance: {instance}")
            self._tasks[instance] = handle
            thread.start()

        self.app.broadcast_threadsafe(self.task_event(handle, "running", "任务已启动"))
        self.app.broadcast_threadsafe(self.status_event(instance))
        return handle

    def _run_task(self, handle: TaskHandle) -> None:
        try:
            self._execute_with_retry(handle)
            handle.status = "done"
            handle.detail = "任务已完成"
            logger.info('Task completed')
            self.app.broadcast_threadsafe(self.task_event(handle, handle.status, handle.detail))
        except TaskAbort:
            handle.status = "cancelled"
            handle.detail = "任务已强制中止"
            logger.warning("任务 %s 已被强制中止：%s", handle.title, handle.instance)
            self.app.broadcast_threadsafe(self.task_event(handle, handle.status, handle.detail))
        except Exception as exc:
            handle.status = "error"
            handle.detail = str(exc)
            logger.error("任务 %s 失败：%s：%s", handle.title, handle.instance, exc)
            logger.debug(traceback.format_exc())
            self.app.broadcast_threadsafe(self.task_event(handle, handle.status, handle.detail))
        finally:
            with self._lock:
                if self._tasks.get(handle.instance) is handle:
                    self._tasks.pop(handle.instance, None)
            handle.done.set()
            self.app.broadcast_threadsafe(self.status_event(handle.instance))

    def _execute_with_retry(self, handle: TaskHandle) -> None:
        while True:
            runner = None
            try:
                logger.info("开始运行任务 %s：%s", handle.title, handle.instance)
                device = self._device(handle.instance)
                runner = create_runner(handle.section, handle.task_id, self.config_store.get(handle.instance), device=device)
                if not runner.device.app_is_running():
                    runner.restart_app()
                runner.run()
                return
            except TaskAbort:
                raise
            except RequestHumanTakeover as exc:
                raise
            except (GameStuckError, GameBugError, GameNotRunningError) as exc:
                self._safe_stop_runner_app(handle.instance, runner)
                self._retry_or_raise(handle, exc)
            except Exception as exc:
                self._retry_or_raise(handle, exc)

    def _retry_or_raise(self, handle: TaskHandle, exc: BaseException) -> None:
        detail = f"{self.retry_delay:g} 秒后重试：{exc}"
        logger.warning("任务 %s %s", handle.title, detail)
        self.app.broadcast_threadsafe(self.task_event(handle, "running", detail))
        time.sleep(self.retry_delay)

    def _safe_stop_runner_app(self, instance: str, runner: Any) -> None:
        try:
            if runner is not None:
                runner.device.app_stop_adb()
        except Exception as exc:
            logger.debug("Failed to stop app before retry", exc_info=True)

    def _device(self, instance: str) -> Any:
        config = self.config_store.get(instance)
        with self._device_lock:
            device = self._devices.get(config.name)
            if device is None:
                from NTEPilot.device.device import Device

                device = Device(config)
                self._devices[config.name] = device
            return device

    @staticmethod
    def _is_device_error(exc: BaseException) -> bool:
        if exc.__traceback__ is None:
            return False
        return any(
            "NTEPilot/device" in frame.filename.replace("\\", "/")
            for frame in traceback.extract_tb(exc.__traceback__)
        )

    def _active_handle(self, instance: str) -> TaskHandle | None:
        config = self.config_store.get(instance)
        with self._lock:
            handle = self._tasks.get(config.name)
            if handle is not None and handle.thread is not None and handle.thread.is_alive():
                return handle
            return None

    def task_event(self, handle: TaskHandle, status: str, detail: str = "") -> dict[str, Any]:
        return {
            "type": "task",
            "instance": handle.instance,
            "task": {
                "id": handle.task_id,
                "title": handle.title,
                "status": status,
                "detail": detail,
                "source": handle.source,
                "planId": handle.plan_id,
            },
        }

    def status_event(self, instance: str) -> dict[str, Any]:
        return {
            "type": "status",
            "instance": instance,
            "status": self.app.status_payload(instance),
        }
