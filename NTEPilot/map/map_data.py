import json
import math
from pathlib import Path

from .utils import TeleportPoint, TeleportNotFoundError
from utils.image import load_image, image_size

class MapData:
    BIG_MAP_FILE = Path('./NTEPilot/map/assets/bigmap_total_hires.png')
    TELEPORT_FILE = Path('./NTEPilot/map/assets/DT_TeleportPoint.json')

    # 从解包文件DataTable/MiniMap/DT_LevelMiniMap.json中得到 (XL_map_bigworld_test)
    CENTER_X = -40532.004
    CENTER_Y = 131446.33
    EDGE_X = 687134.0
    EDGE_Y = 687134.0

    def __init__(self):
        self.big_map = load_image(self.BIG_MAP_FILE)
        self.map_width, self.map_height = image_size(self.big_map)

        self.min_world_x = self.CENTER_X - self.EDGE_X / 2
        self.min_world_y = self.CENTER_Y - self.EDGE_Y / 2
        self.teleports = self._load_teleports()

    def _load_teleports(self) -> list[TeleportPoint]:
        with self.TELEPORT_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        rows = data[0]["Rows"]
        teleports: list[TeleportPoint] = []
        for number, (name, row) in enumerate(rows.items(), start=1):
            pos = row["Transform"]["Translation"]
            world_x = float(pos["X"])
            world_y = float(pos["Y"])
            map_x, map_y = self.world_to_map(world_x, world_y)
            yaw = self._teleport_yaw(row)
            camera_yaw = self._camera_yaw(row)
            teleports.append(
                TeleportPoint(
                    number=number,
                    name=name,
                    level=row.get("BelongsLevel", ""),
                    kind=row.get("TeleportPointType", ""),
                    world_x=world_x,
                    world_y=world_y,
                    map_x=map_x,
                    map_y=map_y,
                    yaw=yaw,
                    camera_yaw=camera_yaw,
                )
            )
        return teleports

    def _teleport_yaw(self, row: dict) -> float:
        override = row.get("TeleportTransformOverride") or {}
        rotation = override.get("Rotation") or row.get("Transform", {}).get("Rotation")
        if rotation:
            z = float(rotation.get("Z", 0.0))
            w = float(rotation.get("W", 1.0))
            yaw = math.degrees(math.atan2(2 * w * z, 1 - 2 * z * z))
        else:
            yaw = float(row.get("CameraRotation", {}).get("Yaw", 0.0))
        return self._ue_yaw_to_minimap(yaw)

    def _camera_yaw(self, row: dict) -> float:
        yaw = float(row.get("CameraRotation", {}).get("Yaw", 0.0))
        return self._ue_yaw_to_minimap(yaw)

    @staticmethod
    def _ue_yaw_to_minimap(yaw: float) -> float:
        return (yaw + 90) % 360

    def world_to_map(self, x: float, y: float) -> tuple[float, float]:
        # The exported coordinates match the visible map axes:
        # smaller X is west/left, smaller Y is north/up.
        map_x = (x - self.min_world_x) / self.EDGE_X * self.map_width
        map_y = (y - self.min_world_y) / self.EDGE_Y * self.map_height
        return map_x, map_y

    def get_teleport(self, number: int) -> TeleportPoint:
        if number < 1 or number > len(self.teleports):
            raise TeleportNotFoundError(f"Teleport #{number} does not exist")
        return self.teleports[number - 1]

    def iter_visible_teleports(self):
        for teleport in self.teleports:
            if 0 <= teleport.map_x <= self.map_width and 0 <= teleport.map_y <= self.map_height:
                yield teleport

map_data = MapData()
