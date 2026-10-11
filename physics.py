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
class Flight:
    duration: float
    range: float
    closest_time: float
    closest_distance: float
    hit: bool


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


def flight_to(settings: Settings, target: Target) -> Flight:
    duration = 2 * settings.up / settings.gravity
    closest_time = 0.0
    closest_distance = math.inf
    # Fine enough for the visual target; sample independently of frame rate.
    for step in range(1001):
        time = duration * step / 1000
        x, y = position(settings, time)
        distance = math.hypot(x - target.x, y - target.y)
        if distance < closest_distance:
            closest_time, closest_distance = time, distance
    return Flight(duration, settings.speed * duration, closest_time,
                  closest_distance, closest_distance <= target.radius)
