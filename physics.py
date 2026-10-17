"""Small, safe Python-code and projectile model for Motion Lab."""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass


NAMES = ("speed", "up", "gravity")


class CodeError(ValueError):
    """An error the game can explain to a young player."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Settings:
    speed: float
    up: float
    gravity: float


@dataclass(frozen=True)
class Target:
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class Obstacle:
    x_left: float
    x_right: float
    y_bottom: float
    y_top: float
    kind: str = "wall"


@dataclass(frozen=True)
class Flight:
    duration: float
    range: float
    closest_time: float
    closest_distance: float
    hit: bool
    blocked: bool
    stop_time: float
    obstacle_index: int | None


def read_code(source: str) -> Settings:
    """Read simple, real Python assignments without executing arbitrary code."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise CodeError("syntax") from exc
    values: dict[str, float] = {}
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            raise CodeError("syntax")
        name_node = statement.targets[0]
        if not isinstance(name_node, ast.Name) or name_node.id not in NAMES:
            raise CodeError("name")
        name = name_node.id
        if name in values:
            raise CodeError("duplicate")
        node = statement.value
        sign = 1
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            sign = -1 if isinstance(node.op, ast.USub) else 1
            node = node.operand
        if not isinstance(node, ast.Constant) or type(node.value) not in (int, float):
            raise CodeError("number")
        value = sign * float(node.value)
        if not math.isfinite(value) or not 0 < value <= 30:
            raise CodeError("range")
        values[name] = value
    if set(values) != set(NAMES):
        raise CodeError("missing")
    return Settings(**values)


def position(settings: Settings, time: float) -> tuple[float, float]:
    return settings.speed * time, settings.up * time - 0.5 * settings.gravity * time**2


def motion_data(settings: Settings, time: float) -> tuple[float, float, float]:
    """Total speed, height above launch, and gravitational acceleration."""
    vertical_speed = settings.up - settings.gravity * time
    _, height = position(settings, time)
    return math.hypot(settings.speed, vertical_speed), max(0.0, height), settings.gravity


def obstacle_hit_time(settings: Settings, obstacle: Obstacle, duration: float) -> float | None:
    """First time the rocket's center enters an obstacle rectangle."""
    start = max(0.0, obstacle.x_left / settings.speed)
    end = min(duration, obstacle.x_right / settings.speed)
    if start > end:
        return None
    candidates = [start, end]
    for height in (obstacle.y_bottom, obstacle.y_top):
        discriminant = settings.up**2 - 2 * settings.gravity * height
        if discriminant >= 0:
            root = math.sqrt(discriminant)
            candidates.extend(((settings.up - root) / settings.gravity,
                               (settings.up + root) / settings.gravity))
    for time in sorted(candidates):
        if start - 1e-9 <= time <= end + 1e-9:
            _, y = position(settings, time)
            if obstacle.y_bottom - 1e-9 <= y <= obstacle.y_top + 1e-9:
                return max(start, time)
    return None


def flight_to(settings: Settings, target: Target,
              obstacles: tuple[Obstacle, ...] = ()) -> Flight:
    duration = 2 * settings.up / settings.gravity
    closest_time = 0.0
    closest_distance = math.inf
    target_time = None
    steps = max(1000, math.ceil(settings.speed * duration / max(target.radius / 4, 0.1)))
    for step in range(steps + 1):
        time = duration * step / steps
        x, y = position(settings, time)
        distance = math.hypot(x - target.x, y - target.y)
        if distance < closest_distance:
            closest_time, closest_distance = time, distance
        if target_time is None and distance <= target.radius:
            target_time = time
    first_obstacle = None
    obstacle_index = None
    for index, obstacle in enumerate(obstacles):
        impact = obstacle_hit_time(settings, obstacle, duration)
        if impact is not None and (first_obstacle is None or impact < first_obstacle):
            first_obstacle, obstacle_index = impact, index
    hit = target_time is not None and (first_obstacle is None or target_time < first_obstacle)
    blocked = first_obstacle is not None and not hit
    stop_time = target_time if hit else first_obstacle if blocked else duration
    return Flight(duration, settings.speed * duration, closest_time,
                  closest_distance, hit, blocked, stop_time, obstacle_index if blocked else None)
