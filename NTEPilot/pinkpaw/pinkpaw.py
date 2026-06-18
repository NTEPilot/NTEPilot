"""粉爪大劫案任务入口。
Task entry for PinkPaw Heist.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from NTEPilot.macro.route import SourceRoute
from NTEPilot.pinkpaw.runtime import AbortException, EarlyExtractException, PinkPawRouteRuntime
from NTEPilot.ui.ui import UI
from utils.logger import logger


ROUTE_DIR = Path(__file__).resolve().parent / "routes"


class PinkPawHeist(UI):
    """粉爪大劫案 runner。
    PinkPaw Heist runner.
    """

    ROUTE_BY_SCHEME = {
        "方案一": "core1.json",
        "方案二": "core2.json",
        "方案三": "core3_dash.json",
    }

    CORE3_BRANCH_ROUTE = {
        "1早雾 2翳 3薄荷 4任意": "core3_dash.json",
        "1翳 2浔 3薄荷 4任意": "core3_attack.json",
    }

    def run(self) -> None:
        """运行粉爪大劫案。
        Run PinkPaw Heist.
        """
        logger.hr("PINKPAW HEIST", level=1)
        loop_count = int(self.config["tools.pinkpaw.loop_count"])
        for index in range(loop_count):
            logger.info("粉爪大劫案第 %s/%s 轮", index + 1, loop_count)
            runtime = self._runtime()
            route_path = self._route_path()
            try:
                route = SourceRoute(route_path)
                route.run(runtime)
                if route_path.name.startswith("core3_"):
                    runtime.release_controls()
                    runtime.exit_heist()
            except EarlyExtractException as exc:
                logger.info("粉爪提前撤离：%s", exc)
            except AbortException:
                raise
            except Exception:
                runtime.release_controls()
                if route_path.name.startswith("core3_"):
                    runtime.abort_heist()
                raise
            finally:
                runtime.release_controls()

    def _runtime(self) -> PinkPawRouteRuntime:
        """创建粉爪路线运行时。
        Create PinkPaw route runtime.
        """
        return PinkPawRouteRuntime(
            config=self.config,
            device=self.device,
            params={
                "avoid_method": self._avoid_method(),
                "timing_scale": self.config["tools.pinkpaw.timing_scale"],
                "interaction_pause": self.config["tools.pinkpaw.interaction_pause"],
                "early_extract_exit1": self.config["tools.pinkpaw.early_extract_exit1"],
                "early_extract_exit2": self.config["tools.pinkpaw.early_extract_exit2"],
            },
        )

    def _route_path(self) -> Path:
        """根据配置选择路线文件。
        Select route file from config.
        """
        scheme = str(self.config["tools.pinkpaw.scheme"])
        if scheme == "方案三":
            route_name = self.CORE3_BRANCH_ROUTE[str(self.config["tools.pinkpaw.core3_branch"])]
        else:
            route_name = self.ROUTE_BY_SCHEME[scheme]
        return ROUTE_DIR / route_name

    def _avoid_method(self) -> str:
        """根据方案三分支选择避战方式。
        Select avoid method by Core3 branch.
        """
        branch = str(self.config["tools.pinkpaw.core3_branch"])
        if branch == "1翳 2浔 3薄荷 4任意":
            return "attack"
        return "dash"
