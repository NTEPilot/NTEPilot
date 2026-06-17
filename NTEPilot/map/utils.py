from dataclasses import dataclass

CROP = (128, 88, 1154, 638)

class TeleportNotFoundError(KeyError):
    pass

class MapMatchError(RuntimeError):
    pass

@dataclass(frozen=True)
class TeleportPoint:
    number: int
    name: str
    level: str
    kind: str
    world_x: float
    world_y: float
    map_x: float
    map_y: float
    yaw: float
    camera_yaw: float

@dataclass(frozen=True)
class MapView:
    origin_x: float
    origin_y: float
    scale: float
    score: float
    crop: tuple[int, int, int, int]
    screen_size: tuple[int, int]

    def map_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.origin_x) * self.scale, (y - self.origin_y) * self.scale

    def screen_to_map(self, x: float, y: float) -> tuple[float, float]:
        return self.origin_x + x / self.scale, self.origin_y + y / self.scale

    def is_on_screen(self, x: float, y: float) -> bool:
        sx, sy = self.map_to_screen(x, y)
        left, top, right, bottom = CROP
        return left <= sx <= right and top <= sy <= bottom
