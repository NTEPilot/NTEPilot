"""把 MaaNTE 粉爪脚本转换为 NTEPilot 可执行的 JSON 源路线。
Convert MaaNTE PinkPaw scripts into JSON source routes executable by NTEPilot.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "MaaNTE" / "agent" / "custom" / "action" / "pinkpaw"
ROUTE_DIR = PROJECT_ROOT / "NTEPilot" / "pinkpaw" / "routes"

KEY_ALIASES = {
    "w": "forward",
    "a": "left",
    "s": "back",
    "d": "right",
    "space": "jump",
    "f": "interact",
    "e": "skill_e",
    "q": "skill_q",
    "g": "skill_g",
    "r": "skill_r",
    "esc": "escape",
    "f5": "city_tycoon_menu",
    "lshift": "dodge",
    "shift": "dodge",
    "1": "switch_1",
    "2": "switch_2",
    "3": "switch_3",
    "4": "switch_4",
}

MOUSE_ALIASES = {
    "left": "attack",
    "right": "lock",
    "middle": "camera_reset",
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

DIRECTION_CALLS = {
    "wait_and_interact",
    "loot_safes_while_walking",
    "try_open_exit",
    "walk_until_extract_panel",
}

KEYWORD_KEY_ARGS = {
    "key",
    "key_str",
    "role_to_switch_back",
}

MAA_SETUP_NAMES = {
    "params",
    "auto_resize_default",
    "auto_resize",
}

MAA_SETUP_CALLS = {
    "_parse_custom_action_param",
    "_get_auto_resize_game_window",
    "_parse_bool",
    "ensure_game_window_resolution",
}

ROUTE_RESULT_NAMES = {
    "CustomAction.RunResult",
}

EXCEPTION_RENAMES = {
    "TaskerStoppedException": "AbortException",
    "StopActionException": "RouteStopException",
}

CORE3_ROUTE_METHODS = {
    "run_path",
    "goto_lg1",
    "goto_lg1_interrupted",
    "goto_lg1_skip_Sakiri",
    "goto_lg1_skip_Hotori",
    "lobby_open_door_check",
    "lg1_wp1",
    "lg1_wp1_safer",
    "lg1_wp2",
    "lg1_wp3",
    "lg1_wp4",
    "lg1_wp4_buster",
    "lg1_wp5_avoid_combat_01",
    "lg1_wp5_avoid_combat_02",
    "lg1_wp5_avoid_combat_03",
    "lg1_wp5_buster",
    "lg1_wp5_buster2",
    "lg2_wp1_to_exit1",
    "lg2_wp1_remains",
    "lg2_wp2_to_exit2",
    "lg2_wp2_to_exit2_safer",
    "lg2_wp3_to_layzer_room",
    "lg2_wp3_in_layzer_room",
    "lg2_wp4",
    "lg2_wp4_to_exit1",
    "lg2_wp4_to_exit2",
    "lg2_wp4_to_exit3",
}

RECOVERY_ROUTE_METHODS = {
    "_has_xiaozhi_prompt",
    "_is_in_world_by_node",
    "_is_in_city_tycoon_menu",
    "_is_in_hethereau_hobbies_menu",
    "_is_in_heist_round",
    "_clear_recovery_menu_blockers",
    "_close_f5_menu_with_esc",
    "_ensure_world_or_city_tycoon_menu",
    "_confirm_world_after_teleport",
    "_enter_recovery_hethereau_hobbies_menu",
    "_open_recovery_heist_map_from_hobbies",
    "_confirm_recovery_teleport",
    "_recovery_press_key",
    "_recovery_middle_click",
    "_focus_game_window",
    "_leave_unexpected_heist_round",
    "_leave_unexpected_heist_round_if_needed",
    "_run_heist_entrance_path_from_teleport",
    "recover_to_heist_entrance",
}


class SemanticKeyTransformer(ast.NodeTransformer):
    """把桌面按键字面量改写为语义键。
    Rewrite desktop key literals into semantic action keys.
    """

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """转换函数调用中的按键参数。
        Convert key arguments inside call expressions.
        """
        self.generic_visit(node)
        call_name = self._call_name(node.func)
        dotted_name = self._dotted_name(node.func)
        if dotted_name in ROUTE_RESULT_NAMES:
            node.func = ast.copy_location(
                ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="route_result", ctx=ast.Load()),
                node.func,
            )
        self._rewrite_key_keywords(node)
        if call_name in KEY_CALLS:
            self._rewrite_key_positional(node, call_name)
        if call_name in DIRECTION_CALLS:
            self._rewrite_direction_keywords(node)
        if call_name in {"click", "mouse_down", "mouse_up"}:
            self._rewrite_mouse_keywords(node)
        return node

    @staticmethod
    def _call_name(func: ast.expr) -> str:
        """获取调用名。
        Get the call name.
        """
        if isinstance(func, ast.Attribute):
            return func.attr
        if isinstance(func, ast.Name):
            return func.id
        return ""

    @staticmethod
    def _dotted_name(func: ast.expr) -> str:
        """获取完整调用名。
        Get the dotted call name.
        """
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            prefix = SemanticKeyTransformer._dotted_name(func.value)
            return f"{prefix}.{func.attr}" if prefix else func.attr
        return ""

    def _rewrite_key_positional(self, node: ast.Call, call_name: str) -> None:
        """重写位置参数中的按键。
        Rewrite key literals in positional arguments.
        """
        key_index = 1 if call_name == "sleep_send_key" else 0
        if len(node.args) <= key_index:
            return
        node.args[key_index] = self._semantic_key_node(node.args[key_index])

    def _rewrite_key_keywords(self, node: ast.Call) -> None:
        """重写关键字参数中的按键。
        Rewrite key literals in keyword arguments.
        """
        for keyword in node.keywords:
            if keyword.arg in KEYWORD_KEY_ARGS:
                keyword.value = self._semantic_key_node(keyword.value)

    def _rewrite_direction_keywords(self, node: ast.Call) -> None:
        """重写 direction 关键字。
        Rewrite direction keyword values.
        """
        for keyword in node.keywords:
            if keyword.arg == "direction":
                keyword.value = self._semantic_direction_node(keyword.value)

    def _rewrite_mouse_keywords(self, node: ast.Call) -> None:
        """重写鼠标按键关键字。
        Rewrite mouse button keyword values.
        """
        for keyword in node.keywords:
            if keyword.arg == "key":
                keyword.value = self._semantic_mouse_node(keyword.value)

    def _semantic_key_node(self, node: ast.expr) -> ast.expr:
        """将单个按键节点转换为语义键节点。
        Convert one key node into a semantic key node.
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return ast.copy_location(ast.Constant(KEY_ALIASES.get(node.value.lower(), node.value)), node)
        return node

    def _semantic_mouse_node(self, node: ast.expr) -> ast.expr:
        """将鼠标按键节点转换为语义键节点。
        Convert one mouse button node into a semantic key node.
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return ast.copy_location(ast.Constant(MOUSE_ALIASES.get(node.value.lower(), node.value)), node)
        return node

    def _semantic_direction_node(self, node: ast.expr) -> ast.expr:
        """将方向参数转换为语义方向列表。
        Convert direction arguments into semantic direction lists.
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            keys = self._split_direction_text(node.value)
            if len(keys) == 1:
                return ast.copy_location(ast.Constant(keys[0]), node)
            return ast.copy_location(ast.List(elts=[ast.Constant(key) for key in keys], ctx=ast.Load()), node)
        return node

    @staticmethod
    def _split_direction_text(text: str) -> list[str]:
        """把 WASD 组合拆成语义方向列表。
        Split WASD combinations into semantic direction lists.
        """
        normalized = text.strip().lower()
        if all(char in KEY_ALIASES for char in normalized):
            return [KEY_ALIASES[char] for char in normalized]
        return [KEY_ALIASES.get(normalized, text)]


class RouteCleanupTransformer(ast.NodeTransformer):
    """清理 Maa 入口残留并改写桌面控制调用。
    Clean Maa entry leftovers and rewrite desktop control calls.
    """

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """清理单个方法。
        Clean one function.
        """
        self.generic_visit(node)
        _strip_annotations(node)
        if node.name == "run":
            node.args.args = node.args.args[:1]
            node.args.posonlyargs = []
            node.args.kwonlyargs = []
            node.args.kw_defaults = []
            node.args.defaults = []
        node.body = self._clean_body(node.body)
        if node.name == "run":
            node.body.insert(
                0,
                ast.Assign(
                    targets=[ast.Name(id="ah", ctx=ast.Store())],
                    value=ast.Name(id="self", ctx=ast.Load()),
                ),
            )
        for handler in ast.walk(node):
            if isinstance(handler, ast.ExceptHandler):
                self._rewrite_exception_handler(handler)
        return node

    def visit_Try(self, node: ast.Try) -> ast.AST | None:
        """递归清理 try 块。
        Recursively clean try blocks.
        """
        self.generic_visit(node)
        node.body = self._clean_body(node.body)
        node.orelse = self._clean_body(node.orelse) if node.orelse else []
        node.finalbody = self._clean_body(node.finalbody) if node.finalbody else []
        for handler in node.handlers:
            handler.body = self._clean_body(handler.body)
        if not node.body and not node.handlers and not node.finalbody:
            return None
        return node

    def visit_If(self, node: ast.If) -> ast.AST | None:
        """递归清理 if 块。
        Recursively clean if blocks.
        """
        self.generic_visit(node)
        if self._is_maa_setup_stmt(node):
            return None
        node.body = self._clean_body(node.body)
        node.orelse = self._clean_body(node.orelse) if node.orelse else []
        return node

    def visit_For(self, node: ast.For) -> ast.AST:
        """递归清理 for 块。
        Recursively clean for blocks.
        """
        self.generic_visit(node)
        node.body = self._clean_body(node.body)
        node.orelse = self._clean_body(node.orelse) if node.orelse else []
        return node

    def visit_While(self, node: ast.While) -> ast.AST:
        """递归清理 while 块。
        Recursively clean while blocks.
        """
        self.generic_visit(node)
        node.body = self._clean_body(node.body)
        node.orelse = self._clean_body(node.orelse) if node.orelse else []
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """改写 Maa 调用和 post_key 调用。
        Rewrite Maa calls and post_key calls.
        """
        self.generic_visit(node)
        screenshot_call = self._rewrite_screencap_wait_get(node)
        if screenshot_call is not None:
            return ast.copy_location(screenshot_call, node)
        dotted = SemanticKeyTransformer._dotted_name(node.func)
        if dotted in {"ah.ctx.run_task", "self.ctx.run_task"}:
            node.func = ast.copy_location(
                ast.Attribute(value=ast.Name(id="ah", ctx=ast.Load()), attr="run_task", ctx=ast.Load()),
                node.func,
            )
        elif dotted in {"ah.ctx.run_recognition", "self.ctx.run_recognition"}:
            node.func = ast.copy_location(
                ast.Attribute(value=ast.Name(id="ah", ctx=ast.Load()), attr="run_recognition", ctx=ast.Load()),
                node.func,
            )
        elif dotted == "notify_pinkpaw_reward":
            node.func = ast.copy_location(
                ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="notify_pinkpaw_reward", ctx=ast.Load()),
                node.func,
            )
            if node.args:
                node.args = node.args[1:]
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        """简化属性链并改写旧上下文引用。
        Simplify attribute chains and rewrite old context references.
        """
        self.generic_visit(node)
        dotted = SemanticKeyTransformer._dotted_name(node)
        if dotted in {"PinkPawHeistScheme1Action._adaptive_timeout_ms", "PinkPawHeistScheme1Action._calibrated"}:
            return ast.copy_location(
                ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=node.attr, ctx=node.ctx),
                node,
            )
        if dotted in {"ah.ctx.tasker.stopping", "self.ctx.tasker.stopping"}:
            return ast.copy_location(
                ast.Call(
                    func=ast.Attribute(value=ast.Name(id="ah", ctx=ast.Load()), attr="is_stopping", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
                node,
            )
        if dotted in {"ah.tasker.stopping", "self.tasker.stopping"}:
            return ast.copy_location(
                ast.Call(
                    func=ast.Attribute(value=ast.Name(id="ah", ctx=ast.Load()), attr="is_stopping", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
                node,
            )
        if dotted in {"ah.ctx", "self.ctx"}:
            return ast.copy_location(ast.Name(id="ah", ctx=ast.Load()), node)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """清理路线日志里的旧运行时称呼。
        Clean old runtime wording in route log strings.
        """
        if isinstance(node.value, str):
            return ast.copy_location(ast.Constant(node.value.replace("tasker", "route")), node)
        return node

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        """剥掉注释字符串并改写 post_key 表达式。
        Strip doc/comment strings and rewrite post_key expressions.
        """
        self.generic_visit(node)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        rewritten = self._rewrite_post_key_expr(node.value)
        if rewritten is not None:
            return ast.copy_location(ast.Expr(value=rewritten), node)
        return node

    @staticmethod
    def _clean_body(body: list[ast.stmt]) -> list[ast.stmt]:
        """删除 Maa 初始化语句。
        Remove Maa setup statements.
        """
        cleaned: list[ast.stmt] = []
        for stmt in body:
            if RouteCleanupTransformer._is_maa_setup_stmt(stmt):
                continue
            cleaned.append(stmt)
        return cleaned or [ast.Pass()]

    @staticmethod
    def _is_maa_setup_stmt(stmt: ast.stmt) -> bool:
        """判断语句是否为 Maa 初始化残留。
        Determine whether a statement is Maa setup leftover.
        """
        if isinstance(stmt, ast.Assign):
            targets = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
            if any(target in MAA_SETUP_NAMES or target == "current_ctrl" for target in targets):
                return True
            if targets == ["ah"] and isinstance(stmt.value, ast.Call):
                return SemanticKeyTransformer._call_name(stmt.value.func) == "ActionHelper"
        if isinstance(stmt, ast.If):
            return RouteCleanupTransformer._stmt_contains_call(stmt, MAA_SETUP_CALLS)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return SemanticKeyTransformer._call_name(stmt.value.func) in MAA_SETUP_CALLS
        return False

    @staticmethod
    def _stmt_contains_call(stmt: ast.stmt, names: set[str]) -> bool:
        """判断语句内是否包含指定调用。
        Determine whether a statement contains named calls.
        """
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call) and SemanticKeyTransformer._call_name(child.func) in names:
                return True
        return False

    @staticmethod
    def _rewrite_exception_handler(handler: ast.ExceptHandler) -> None:
        """改写异常类型名。
        Rewrite exception type names.
        """
        if isinstance(handler.type, ast.Name) and handler.type.id in EXCEPTION_RENAMES:
            handler.type.id = EXCEPTION_RENAMES[handler.type.id]

    @staticmethod
    def _rewrite_screencap_wait_get(node: ast.Call) -> ast.Call | None:
        """把旧截图 future 链改成运行时截图方法。
        Rewrite old screenshot future chains into the runtime screenshot method.
        """
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "get":
            return None
        wait_call = node.func.value
        if not isinstance(wait_call, ast.Call):
            return None
        if not isinstance(wait_call.func, ast.Attribute) or wait_call.func.attr != "wait":
            return None
        screencap_call = wait_call.func.value
        if not isinstance(screencap_call, ast.Call):
            return None
        if not isinstance(screencap_call.func, ast.Attribute) or screencap_call.func.attr != "post_screencap":
            return None
        owner = SemanticKeyTransformer._dotted_name(screencap_call.func.value)
        if owner not in {"ah.tasker.controller", "self.tasker.controller", "ah.ctx.tasker.controller", "self.ctx.tasker.controller"}:
            return None
        return ast.Call(
            func=ast.Attribute(value=ast.Name(id="ah", ctx=ast.Load()), attr="screenshot_image", ctx=ast.Load()),
            args=[],
            keywords=[],
        )

    @staticmethod
    def _rewrite_post_key_expr(expr: ast.expr) -> ast.expr | None:
        """把 current_ctrl.post_key_xxx(...).wait() 改成语义按键调用。
        Rewrite current_ctrl.post_key_xxx(...).wait() into semantic key calls.
        """
        if not isinstance(expr, ast.Call):
            return None
        wait_func = expr.func
        if not isinstance(wait_func, ast.Attribute) or wait_func.attr != "wait":
            return None
        inner = wait_func.value
        if not isinstance(inner, ast.Call) or not isinstance(inner.func, ast.Attribute):
            return None
        method_name = inner.func.attr
        if method_name not in {"post_key_down", "post_key_up", "post_click_key"}:
            return None
        if not inner.args or not isinstance(inner.args[0], ast.Constant) or not isinstance(inner.args[0].value, int):
            return None
        semantic_key = _desktop_vk_to_semantic(inner.args[0].value)
        if method_name == "post_key_down":
            call_name = "key_down"
        elif method_name == "post_key_up":
            call_name = "key_up"
        else:
            call_name = "click_key"
        return ast.Call(
            func=ast.Attribute(value=ast.Name(id="ah", ctx=ast.Load()), attr=call_name, ctx=ast.Load()),
            args=[ast.Constant(semantic_key)],
            keywords=[],
        )


def _desktop_vk_to_semantic(vk: int) -> str:
    """把 Maa 桌面虚拟键码转换成语义键。
    Convert Maa desktop virtual-key code into a semantic key.
    """
    mapping = {
        0x57: "forward",
        0x41: "left",
        0x53: "back",
        0x44: "right",
        0x20: "jump",
        0x45: "skill_e",
        0x46: "interact",
        0x31: "switch_1",
        0x32: "switch_2",
        0x33: "switch_3",
        0x34: "switch_4",
        0x74: "city_tycoon_menu",
        0x1B: "escape",
        0x02: "lock",
    }
    if vk not in mapping:
        raise ValueError(f"Unsupported desktop virtual key: {vk}")
    return mapping[vk]


def _load_tree(path: Path) -> ast.Module:
    """读取并解析 Python 源文件。
    Read and parse one Python source file.
    """
    return ast.parse(path.read_text(encoding="utf-8"))


def _class_by_name(tree: ast.Module, class_name: str) -> ast.ClassDef:
    """按类名查找类节点。
    Find a class node by name.
    """
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise ValueError(f"Class not found: {class_name}")


def _extract_methods(source_path: Path, class_name: str, names: set[str] | None = None) -> dict[str, str]:
    """抽取类方法源码并转换按键语义。
    Extract class method sources and convert key literals to semantic keys.
    """
    tree = _load_tree(source_path)
    class_node = _class_by_name(tree, class_name)
    transformer = SemanticKeyTransformer()
    cleanup = RouteCleanupTransformer()
    methods: dict[str, str] = {}
    for item in class_node.body:
        if not isinstance(item, ast.FunctionDef):
            continue
        if names is not None and item.name not in names:
            continue
        method = cleanup.visit(ast.fix_missing_locations(item))
        method = transformer.visit(ast.fix_missing_locations(method))
        ast.fix_missing_locations(method)
        methods[item.name] = ast.unparse(method)
    return methods


def _strip_annotations(method: ast.FunctionDef) -> None:
    """删除 Maa 类型注解，避免运行时依赖 Maa 模块。
    Remove Maa type annotations to avoid runtime dependency on Maa modules.
    """
    method.returns = None
    for arg in [*method.args.args, *method.args.kwonlyargs]:
        arg.annotation = None
    if method.args.vararg is not None:
        method.args.vararg.annotation = None
    if method.args.kwarg is not None:
        method.args.kwarg.annotation = None


def _route_payload(route_id: str, entry: str, methods: dict[str, str], source: str) -> dict[str, Any]:
    """创建单个路线 JSON 载荷。
    Create one route JSON payload.
    """
    return {
        "version": 1,
        "route_id": route_id,
        "source": source,
        "entry": entry,
        "methods": methods,
        "semantic_keys": {
            "directions": ["forward", "back", "left", "right"],
            "actions": [
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
                "switch_1",
                "switch_2",
                "switch_3",
                "switch_4",
            ],
        },
    }


def build_routes() -> dict[str, dict[str, Any]]:
    """构建全部粉爪路线。
    Build all PinkPaw routes.
    """
    core1_path = SOURCE_DIR / "pinkpaw_core1.py"
    core2_path = SOURCE_DIR / "pinkpaw_core2.py"
    core3_path = SOURCE_DIR / "pinkpaw_core3.py"
    recovery_path = SOURCE_DIR / "pinkpaw_entrance_recovery.py"

    core1_methods = _extract_methods(
        core1_path,
        "PinkPawHeistScheme1Action",
        {"run", "_wait_for_xiaozhi_adaptive", "_log_to_frontend", "_exit_to_main"},
    )
    core2_methods = _extract_methods(
        core2_path,
        "PinkPawHeistScheme2Action",
        {"run", "_exit_to_main"},
    )
    core3_methods = _extract_methods(core3_path, "PinkPawHeistCore3Path", CORE3_ROUTE_METHODS)
    recovery_methods = _extract_methods(recovery_path, "PinkPawHeistEntranceRecoveryPath", RECOVERY_ROUTE_METHODS)

    return {
        "core1": _route_payload("core1", "run", core1_methods, str(core1_path.relative_to(PROJECT_ROOT))),
        "core2": _route_payload("core2", "run", core2_methods, str(core2_path.relative_to(PROJECT_ROOT))),
        "core3_dash": _route_payload("core3_dash", "run_path", core3_methods, str(core3_path.relative_to(PROJECT_ROOT))),
        "core3_attack": _route_payload("core3_attack", "run_path", core3_methods, str(core3_path.relative_to(PROJECT_ROOT))),
        "entrance_recovery": _route_payload(
            "entrance_recovery",
            "recover_to_heist_entrance",
            recovery_methods,
            str(recovery_path.relative_to(PROJECT_ROOT)),
        ),
    }


def main() -> None:
    """转换并写入路线 JSON 文件。
    Convert and write route JSON files.
    """
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    for route_name, payload in build_routes().items():
        route_path = ROUTE_DIR / f"{route_name}.json"
        route_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {route_path}")


if __name__ == "__main__":
    main()
