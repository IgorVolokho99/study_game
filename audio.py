"""Small synthesized sound effects; no downloaded audio files needed."""

from __future__ import annotations

import math
import random
from array import array
from collections.abc import Callable

import pygame


SAMPLE_RATE = 22_050


def _sound(duration: float, sample: Callable[[float], float]) -> pygame.mixer.Sound:
    samples = array("h")
    for index in range(int(SAMPLE_RATE * duration)):
        value = max(-1.0, min(1.0, sample(index / SAMPLE_RATE)))
        samples.append(round(value * 32767))
    return pygame.mixer.Sound(buffer=samples.tobytes())


class Sounds:
    def __init__(self) -> None:
        self.enabled = True
        self.available = False
        self.effects: dict[str, pygame.mixer.Sound] = {}
        self.last_key_ms = -100
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=256)
            self.effects = self._build_effects()
            self.available = True
        except pygame.error:
            pygame.mixer.quit()

    def _build_effects(self) -> dict[str, pygame.mixer.Sound]:
        rng = random.Random(12)

        def key(t: float) -> float:
            fade = min(1.0, t / 0.003) * math.exp(-65 * t)
            return fade * (0.3 * math.sin(2 * math.pi * 710 * t)
                           + 0.1 * math.sin(2 * math.pi * 1040 * t))

        def click(t: float) -> float:
            return 0.22 * math.exp(-48 * t) * math.sin(2 * math.pi * 550 * t)

        def launch(t: float) -> float:
            duration = 0.42
            phase = 2 * math.pi * (130 * t + 590 * t * t)
            envelope = min(1.0, t / 0.04) * max(0.0, 1 - t / duration)**0.7
            return envelope * (0.38 * math.sin(phase) + 0.08 * rng.uniform(-1, 1))

        def success(t: float) -> float:
            note = min(int(t / 0.13), 2)
            local_time = t - 0.13 * note
            frequency = (523, 659, 784)[note]
            fade = min(1.0, local_time / 0.008) * math.exp(-9 * local_time)
            return 0.3 * fade * (math.sin(2 * math.pi * frequency * local_time)
                                 + 0.18 * math.sin(4 * math.pi * frequency * local_time))

        def impact(t: float) -> float:
            phase = 2 * math.pi * (135 * t - 150 * t * t)
            fade = math.exp(-17 * t)
            return fade * (0.42 * math.sin(phase) + 0.09 * rng.uniform(-1, 1))

        def miss(t: float) -> float:
            phase = 2 * math.pi * (340 * t - 220 * t * t)
            return 0.2 * math.exp(-10 * t) * math.sin(phase)

        effects = {
            "key": _sound(0.05, key),
            "click": _sound(0.07, click),
            "launch": _sound(0.42, launch),
            "success": _sound(0.40, success),
            "impact": _sound(0.24, impact),
            "miss": _sound(0.22, miss),
        }
        for effect in effects.values():
            effect.set_volume(0.38)
        effects["key"].set_volume(0.26)
        return effects

    def play(self, name: str) -> None:
        if not self.available or not self.enabled:
            return
        if name == "key":
            now = pygame.time.get_ticks()
            if now - self.last_key_ms < 25:
                return
            self.last_key_ms = now
        self.effects[name].play()

    def toggle(self) -> None:
        if self.available:
            self.enabled = not self.enabled
            if self.enabled:
                self.play("click")
            else:
                pygame.mixer.stop()
