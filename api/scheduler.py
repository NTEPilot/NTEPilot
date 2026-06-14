from __future__ import annotations

import copy
import threading
import time
import traceback
import uuid
from datetime import datetime
from typing import Any

from NTEPilot.config.schema import get_task, get_task_catalog
from api.task_runner import TaskBusyError, TaskRunner
from utils.logger import logger


class Scheduler:
    poll_seconds = 5.0

    def __init__(self, app: Any, config_store: Any, task_runner: TaskRunner):
        self.app = app
        self.config_store = config_store
        self.task_runner = task_runner
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._active_plan: dict[str, str] = {}
        self._last_error: dict[str, str] = {}

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="NTEPilotScheduler", daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2)

    def catalog_payload(self) -> dict[str, Any]:
        return {"type": "scheduler.catalog", "tasks": get_task_catalog("schedule")}

    def state_payload(self, instance: str) -> dict[str, Any]:
        return {
            "type": "scheduler.state",
            "instance": self.config_store.get(instance).name,
            "scheduler": self.payload(instance),
        }

    def payload(self, instance: str) -> dict[str, Any]:
        config = self.config_store.get(instance)
        enabled = bool(config.get_value("scheduler.enabled", False))
        plans = self._plans(config.name)
        return {
            "enabled": enabled,
            "status": self.status(config.name),
            "plans": plans,
            "activePlanId": self._active_plan.get(config.name),
            "lastError": self._last_error.get(config.name),
        }

    def status(self, instance: str) -> str:
        config = self.config_store.get(instance)
        if not bool(config.get_value("scheduler.enabled", False)):
            return "disabled"
        if self._active_plan.get(config.name):
            return "running"
        if self._due_plans(config.name) and not self.task_runner.is_idle(config.name):
            return "waiting"
        if self._last_error.get(config.name):
            return "error"
        return "idle"

    def set_enabled(self, instance: str, enabled: bool) -> dict[str, Any]:
        config = self.config_store.get(instance)
        config["scheduler.enabled"] = bool(enabled)
        config.save()

        if not enabled and self.task_runner.active_source(config.name) == "scheduler":
            try:
                self.task_runner.stop(config.name)
            except Exception as exc:
                logger.warning("Failed to stop scheduled task while disabling scheduler: %s", exc)

        self._broadcast_state(config.name)
        return {"instance": config.name, "enabled": bool(enabled)}

    def add_plan(self, instance: str, task_id: str, run_time: str, priority: int, values: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.config_store.get(instance)
        get_task("schedule", task_id)
        plan = {
            "id": uuid.uuid4().hex,
            "taskId": task_id,
            "time": self._normalize_time(run_time),
            "priority": int(priority),
            "values": self._filter_plan_values(task_id, values),
        }
        plans = self._plans(config.name)
        plans.append(plan)
        config["scheduler.plans"] = self._sort_plans(plans)
        config.save()
        self._broadcast_state(config.name)
        return {"instance": config.name, "plan": plan}

    def update_plan(self, instance: str, plan_id: str, task_id: str, run_time: str, priority: int, values: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.config_store.get(instance)
        get_task("schedule", task_id)
        plans = self._plans(config.name)
        for plan in plans:
            if plan.get("id") == plan_id:
                plan["taskId"] = task_id
                plan["time"] = self._normalize_time(run_time)
                plan["priority"] = int(priority)
                plan["values"] = self._filter_plan_values(task_id, values)
                config["scheduler.plans"] = self._sort_plans(plans)
                config.save()
                self._broadcast_state(config.name)
                return {"instance": config.name, "plan": plan}
        raise ValueError(f"Unknown plan: {plan_id}")

    def remove_plan(self, instance: str, plan_id: str) -> dict[str, Any]:
        config = self.config_store.get(instance)
        active_plan = self._active_plan.get(config.name)
        if active_plan == plan_id:
            self.task_runner.stop(config.name)

        plans = [plan for plan in self._plans(config.name) if plan.get("id") != plan_id]
        config["scheduler.plans"] = plans
        config.save()
        self._broadcast_state(config.name)
        return {"instance": config.name, "removed": plan_id}

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                for item in self.config_store.list_instances():
                    self._run_due_plans(item["name"])
            except Exception as exc:
                logger.error("Scheduler loop failed: %s", exc)
                logger.debug(traceback.format_exc())
            self._stop_event.wait(self.poll_seconds)

    def _run_due_plans(self, instance: str) -> None:
        config = self.config_store.get(instance)
        if not bool(config.get_value("scheduler.enabled", False)):
            return

        due = self._due_plans(config.name)
        if not due:
            return
        if not self.task_runner.is_idle(config.name):
            self._broadcast_state(config.name)
            return

        ran_any = False
        while due and bool(config.get_value("scheduler.enabled", False)):
            plan = due[0]
            plan_id = str(plan["id"])
            task_id = str(plan["taskId"])

            with self._lock:
                self._active_plan[config.name] = plan_id
                self._last_error.pop(config.name, None)
            self._broadcast_state(config.name)

            try:
                handle = self.task_runner.start_scheduled(config.name, task_id, plan_id)
            except TaskBusyError:
                with self._lock:
                    self._active_plan.pop(config.name, None)
                self._broadcast_state(config.name)
                return
            except Exception as exc:
                logger.error("Failed to start scheduled plan %s: %s", plan_id, exc)
                logger.debug(traceback.format_exc())
                self._mark_plan(config.name, plan_id, "error", str(exc))
                with self._lock:
                    self._active_plan.pop(config.name, None)
                    self._last_error[config.name] = str(exc)
                self._broadcast_state(config.name)
                return

            handle.done.wait()
            ran_any = True
            status = handle.status if handle.status in {"done", "cancelled", "error"} else "error"
            detail = handle.detail
            self._mark_plan(config.name, plan_id, status, detail)
            with self._lock:
                self._active_plan.pop(config.name, None)
                if status == "error" and detail:
                    self._last_error[config.name] = detail
            self._broadcast_state(config.name)

            config = self.config_store.get(instance)
            if not self.task_runner.is_idle(config.name):
                return
            due = self._due_plans(config.name)

        if ran_any and not self._due_plans(config.name):
            self.task_runner.close_app(config.name)

    def _due_plans(self, instance: str) -> list[dict[str, Any]]:
        config = self.config_store.get(instance)
        if not bool(config.get_value("scheduler.enabled", False)):
            return []

        now = datetime.now()
        today = now.date().isoformat()
        current_time = now.strftime("%H:%M")
        due = [
            plan
            for plan in self._plans(config.name)
            if plan.get("lastRunDate") != today
            and str(plan.get("time", "23:59")) <= current_time
        ]
        due.sort(key=lambda item: (-int(item.get("priority", 0)), str(item.get("time", "00:00")), str(item.get("id", ""))))
        return due

    def _mark_plan(self, instance: str, plan_id: str, status: str, detail: str = "") -> None:
        config = self.config_store.get(instance)
        today = datetime.now().date().isoformat()
        now = datetime.now().isoformat(timespec="seconds")
        plans = self._plans(config.name)
        for plan in plans:
            if plan.get("id") == plan_id:
                plan["lastRunDate"] = today
                plan["lastRunAt"] = now
                plan["lastStatus"] = status
                if detail:
                    plan["lastDetail"] = detail
                else:
                    plan.pop("lastDetail", None)
                break
        config["scheduler.plans"] = plans
        config.save()

    def _plans(self, instance: str) -> list[dict[str, Any]]:
        config = self.config_store.get(instance)
        plans = config.get_value("scheduler.plans", [])
        if not isinstance(plans, list):
            plans = []
        return self._sort_plans(copy.deepcopy(plans))

    def _broadcast_state(self, instance: str) -> None:
        self.app.broadcast_threadsafe(self.state_payload(instance))
        self.app.broadcast_threadsafe({"type": "status", "instance": instance, "status": self.app.status_payload(instance)})

    @staticmethod
    def _sort_plans(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(plans, key=lambda plan: (str(plan.get("time", "00:00")), -int(plan.get("priority", 0)), str(plan.get("id", ""))))

    @staticmethod
    def _normalize_time(value: str) -> str:
        try:
            parsed = datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("Plan time must use HH:MM format") from exc
        return parsed.strftime("%H:%M")

    @staticmethod
    def _filter_plan_values(task_id: str, values: dict[str, Any] | None) -> dict[str, Any]:
        if not values:
            return {}
        prefix = f"schedule.{task_id}."
        return {k: v for k, v in values.items() if k.startswith(prefix)}
