"""JSON 源路线加载与受控执行。
Load and execute JSON source routes in a controlled runtime.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

import json
from pathlib import Path
from types import FunctionType
from typing import Any, Callable

from utils.exceptions import ScriptError
from utils.logger import logger


class RouteResult:
    """路线节点返回对象的最小结果结构。
    Minimal result structure for route node checks.
    """

    def __init__(self, succeeded: bool) -> None:
        """初始化状态。
        Initialize the status.

        Args:
            succeeded: 是否成功。
                       Whether the action succeeded.
        """
        self.status = self
        self.succeeded = succeeded
        self.hit = succeeded


class SourceRoute:
    """从 JSON 中加载的源码路线。
    Source route loaded from JSON.
    """

    def __init__(self, path: Path) -> None:
        """读取路线 JSON。
        Read route JSON.

        Args:
            path: 路线文件路径。
                  Route file path.
        """
        self.path = path
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.version = int(raw["version"])
        self.route_id = str(raw["route_id"])
        self.entry = str(raw["entry"])
        self.methods: dict[str, str] = dict(raw["methods"])

    def bind(self, runtime: Any) -> None:
        """把路线方法绑定到运行时对象。
        Bind route methods to a runtime object.

        Args:
            runtime: 路线运行时对象。
                     Route runtime object.
        """
        namespace = runtime.route_exec_namespace()
        for name, source in self.methods.items():
            if not isinstance(source, str):
                continue
            compiled = compile(source, f"{self.path}:{name}", "exec")
            local_ns: dict[str, Any] = {}
            exec(compiled, namespace, local_ns)
            fn = local_ns.get(name)
            if not isinstance(fn, FunctionType):
                raise ScriptError(f"Route method did not compile to function: {name}")
            setattr(runtime, name, fn.__get__(runtime, runtime.__class__))

    def run(self, runtime: Any) -> Any:
        """运行路线入口。
        Run the route entry.

        Args:
            runtime: 路线运行时对象。
                     Route runtime object.

        Returns:
            入口方法返回值。
            Entry method return value.
        """
        self.bind(runtime)
        entry = getattr(runtime, self.entry, None)
        if not callable(entry):
            raise ScriptError(f"Route entry not found: {self.entry}")
        logger.hr(f"PINKPAW ROUTE {self.route_id}", level=2)
        return entry()


def is_hit(result: Any) -> bool:
    """判断路线节点结果是否命中。
    Determine whether a route node result is a successful hit.
    """
    if result is None:
        return False
    succeeded = getattr(getattr(result, "status", None), "succeeded", None)
    if succeeded is not None:
        return bool(succeeded)
    if hasattr(result, "hit"):
        return bool(result.hit)
    if isinstance(result, bool):
        return result
    return bool(result)


def run_source_route(route_path: Path, runtime_factory: Callable[[], Any]) -> Any:
    """加载并运行一条源码路线。
    Load and run one source route.

    Args:
        route_path: 路线 JSON 路径。
                    Route JSON path.
        runtime_factory: 运行时对象工厂。
                         Runtime object factory.

    Returns:
        路线入口返回值。
        Route entry return value.
    """
    route = SourceRoute(route_path)
    runtime = runtime_factory()
    return route.run(runtime)
