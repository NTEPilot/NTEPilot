"""校验粉爪大劫案 JSON 源路线。
Validate PinkPaw Heist JSON source routes.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from NTEPilot.pinkpaw.runtime import PinkPawRouteRuntime
from utils.exceptions import ScriptError

ROUTE_DIR = PROJECT_ROOT / "NTEPilot" / "pinkpaw" / "routes"
REQUIRED_ROUTES = {
    "core1.json",
    "core2.json",
    "core3_dash.json",
    "core3_attack.json",
    "entrance_recovery.json",
}
FORBIDDEN_TEXT = (
    "CustomAction",
    "ActionHelper",
    "Context",
    "TaskerStoppedException",
    "StopActionException",
    "current_ctrl",
    "post_key_",
    "ah.ctx",
    "self.ctx",
    "PinkPawHeistScheme1Action",
    "post_screencap",
    "run_recognition_direct",
)
FORBIDDEN_ATTRIBUTES = {"ctx", "tasker", "controller"}
FORBIDDEN_KEYS = {"W", "A", "S", "D", "Space", "Esc", "lshift", "shift"}
ALLOWED_SEMANTIC_KEYS = {
    "forward",
    "back",
    "left",
    "right",
    "attack",
    "interact",
    "jump",
    "dodge",
    "lock",
    "camera_reset",
    "skill_e",
    "skill_q",
    "skill_g",
    "skill_r",
    "escape",
    "city_tycoon_menu",
    "switch_1",
    "switch_2",
    "switch_3",
    "switch_4",
}
KEY_CALLS = {
    "click_key",
    "key_down",
    "key_up",
    "send_key",
    "send_key_down",
    "send_key_up",
    "sleep_send_key",
    "_recovery_press_key",
}
KEYWORD_KEY_ARGS = {"key", "key_str", "role_to_switch_back"}


def _load_route(path: Path) -> dict[str, Any]:
    """读取路线 JSON。
    Load one route JSON.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _call_name(func: ast.expr) -> str:
    """获取调用名。
    Get a call name.
    """
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _collect_self_calls(tree: ast.AST) -> set[str]:
    """收集 self/ah 方法调用。
    Collect self/ah method calls.
    """
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id in {"self", "ah"}:
                calls.add(node.func.attr)
    return calls


def _check_forbidden_nodes(path: Path, name: str, tree: ast.AST) -> None:
    """校验路线源码没有旧控制链或空实现残留。
    Validate that route source has no old control chains or empty implementations.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES:
            raise ScriptError(f"{path.name}:{name} contains forbidden attribute: {node.attr}")
        if isinstance(node, ast.Pass):
            raise ScriptError(f"{path.name}:{name} contains pass statement")


def _check_semantic_keys(path: Path, name: str, tree: ast.AST) -> None:
    """校验按键参数已经语义化。
    Validate that key arguments are semantic.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _call_name(node.func)
        if call_name in KEY_CALLS and node.args:
            key_arg = node.args[1] if call_name == "sleep_send_key" and len(node.args) > 1 else node.args[0]
            _check_key_node(path, name, key_arg)
        for keyword in node.keywords:
            if keyword.arg in KEYWORD_KEY_ARGS:
                _check_key_node(path, name, keyword.value)


def _check_key_node(path: Path, method: str, node: ast.expr) -> None:
    """校验单个按键节点。
    Validate one key node.
    """
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return
    key = node.value
    if key in FORBIDDEN_KEYS or key.lower() in {item.lower() for item in FORBIDDEN_KEYS}:
        raise ScriptError(f"{path.name}:{method} contains desktop key {key!r}")
    if key not in ALLOWED_SEMANTIC_KEYS:
        raise ScriptError(f"{path.name}:{method} contains unknown semantic key {key!r}")


def check_routes() -> None:
    """校验全部粉爪路线。
    Validate all PinkPaw routes.
    """
    found_routes = {path.name for path in ROUTE_DIR.glob("*.json")}
    missing_routes = REQUIRED_ROUTES - found_routes
    if missing_routes:
        raise ScriptError(f"Missing PinkPaw routes: {sorted(missing_routes)}")

    runtime_methods = set(dir(PinkPawRouteRuntime))
    for route_path in sorted(ROUTE_DIR.glob("*.json")):
        text = route_path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in text:
                raise ScriptError(f"{route_path.name} contains forbidden text: {forbidden}")
        route = _load_route(route_path)
        methods = route.get("methods")
        if not isinstance(methods, dict):
            raise ScriptError(f"{route_path.name} methods must be an object")
        entry = str(route.get("entry"))
        if entry not in methods:
            raise ScriptError(f"{route_path.name} entry method not found: {entry}")
        route_method_names = set(methods)
        for method_name, source in methods.items():
            if not isinstance(source, str):
                raise ScriptError(f"{route_path.name}:{method_name} source must be a string")
            tree = ast.parse(source)
            if not source.startswith("def "):
                raise ScriptError(f"{route_path.name}:{method_name} is not a function source")
            _check_forbidden_nodes(route_path, method_name, tree)
            _check_semantic_keys(route_path, method_name, tree)
            missing_calls = sorted(_collect_self_calls(tree) - route_method_names - runtime_methods)
            if missing_calls:
                raise ScriptError(f"{route_path.name}:{method_name} missing runtime calls: {missing_calls}")


def main() -> None:
    """入口函数。
    Entry point.
    """
    check_routes()
    print("PinkPaw routes OK")


if __name__ == "__main__":
    main()
