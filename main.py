"""Mika's Motion Lab — a small Pygame game about Python and motion."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import pygame

from audio import Sounds
from physics import CodeError, Obstacle, Settings, Target, flight_to, motion_data, position, read_code


WIDTH, HEIGHT = 900, 700
SAVE_FILE = Path(__file__).with_name(".motion_lab_progress.json")

INK = (27, 48, 68)
MUTED = (93, 115, 124)
TEAL = (28, 150, 124)
CREAM = (248, 247, 239)
PEACH = (244, 139, 100)
WHITE = (255, 255, 255)
DATA_BUTTON = pygame.Rect(402, 617, 126, 34)
RUN_BUTTON = pygame.Rect(570, 514, 176, 42)
RESET_BUTTON = pygame.Rect(754, 514, 108, 42)
EDITOR_RECT = pygame.Rect(570, 352, 292, 150)
SCENE_RECT = pygame.Rect(38, 315, 492, 285)
PREV_PAGE_BUTTON = pygame.Rect(24, 166, 34, 39)
NEXT_PAGE_BUTTON = pygame.Rect(842, 166, 34, 39)
SOUND_BUTTON = pygame.Rect(642, 16, 112, 32)
MISSIONS_PER_PAGE = 5
PROGRESS_VERSION = 2

MISSIONS = [
    dict(name="Wall jump", icon="01", title="Clear the stone wall",
         description="Fly over the wall, then land 24 meters away.",
         instruction="The wall blocks low flights. Give the rocket more up.",
         science="More up makes a taller arc over the wall.",
         target=Target(24, 0, 1.2), xmax=37, ymax=17,
         obstacles=(Obstacle(10, 12, 0, 6, "wall"),),
         starter="# Clear the wall!\nspeed = 8\nup = 10\ngravity = 10", world="WALL"),
    dict(name="Underpass", icon="02", title="Fly under the gate",
         description="The gate hangs above the path to a 24-meter pad.",
         instruction="A high arc hits the gate. Try a faster, lower flight.",
         science="Speed changes where the rocket is along its arc.",
         target=Target(24, 0, 1.2), xmax=37, ymax=17,
         obstacles=(Obstacle(9, 15, 7.5, 13.5, "gate"),),
         starter="# Stay below the gate!\nspeed = 8\nup = 15\ngravity = 10", world="LOW GATE"),
    dict(name="Two gates", icon="03", title="Thread the safe path",
         description="Go over the wall and under the floating gate.",
         instruction="Both obstacles matter. Try changing speed and up.",
         science="The same landing spot can have different arcs.",
         target=Target(30, 0, 1.2), xmax=43, ymax=18,
         obstacles=(Obstacle(8, 10, 0, 3.5, "wall"),
                    Obstacle(17, 21, 11, 17, "gate")),
         starter="# Find the gap!\nspeed = 10\nup = 15\ngravity = 10", world="TWO GATES"),
    dict(name="Window shot", icon="04", title="Fly through the window",
         description="Pass between the low wall and the upper gate.",
         instruction="Too low or too high will hit. Shape a middle arc.",
         science="Different speed and up can land at the same spot.",
         target=Target(28, 0, 1.2), xmax=40, ymax=21,
         obstacles=(Obstacle(12, 14, 0, 4, "wall"),
                    Obstacle(12, 14, 13, 19, "gate")),
         starter="# Find the window!\nspeed = 20\nup = 7\ngravity = 10", world="WINDOW"),
    dict(name="Cloud tunnel", icon="05", title="Stay below both clouds",
         description="Two floating gates guard the 32-meter pad.",
         instruction="Your first arc is too high. Make it lower and faster.",
         science="A faster sideways speed can flatten the arc.",
         target=Target(32, 0, 1.2), xmax=45, ymax=20,
         obstacles=(Obstacle(8, 13, 8, 16, "gate"),
                    Obstacle(19, 24, 8, 16, "gate")),
         starter="# Under both clouds!\nspeed = 8\nup = 16\ngravity = 8", world="CLOUDS"),
    dict(name="Moon wall", icon="06", title="Leap in weak gravity",
         description="Clear the wall and reach the far moon pad.",
         instruction="Gravity is weak. Give the rocket enough up to clear it.",
         science="Weak gravity keeps the rocket airborne longer.",
         target=Target(60, 0, 1.8), xmax=85, ymax=15,
         obstacles=(Obstacle(25, 29, 0, 5, "wall"),),
         starter="# Moon leap!\nspeed = 10\nup = 4\ngravity = 2", world="MOON WALL"),
    dict(name="Crystal gate", icon="07", title="Catch the floating crystal",
         description="Reach a high crystal without touching the gate.",
         instruction="The gate catches tall arcs. Change up a little.",
         science="Up controls height at each point of the flight.",
         target=Target(30, 12, 1.5), xmax=43, ymax=27,
         obstacles=(Obstacle(14, 18, 17.5, 23, "gate"),),
         starter="# Catch the crystal!\nspeed = 10\nup = 16\ngravity = 6", world="CRYSTAL"),
    dict(name="Twin towers", icon="08", title="Clear two tall walls",
         description="The second wall is taller than the first.",
         instruction="Keep the same speed, but raise the arc enough.",
         science="The rocket loses height after the top of its arc.",
         target=Target(36, 0, 1.3), xmax=49, ymax=17,
         obstacles=(Obstacle(10, 12, 0, 3.5, "wall"),
                    Obstacle(23, 25, 0, 5, "wall")),
         starter="# Two towers!\nspeed = 12\nup = 10\ngravity = 8", world="TOWERS"),
    dict(name="Over the gate", icon="09", title="Climb above the gate",
         description="This time the safe path goes over the gate.",
         instruction="Try less speed and more up for a taller arc.",
         science="A high arc can reach the same landing pad.",
         target=Target(28, 0, 1.2), xmax=40, ymax=25,
         obstacles=(Obstacle(12, 18, 7, 13, "gate"),),
         gate_hint="The gate stopped the rocket. Fly higher!",
         starter="# Go over this time!\nspeed = 10\nup = 14\ngravity = 10", world="HIGH GATE"),
    dict(name="Final course", icon="10", title="Complete the star course",
         description="Clear two walls, pass a gate, and catch the star.",
         instruction="Plan the whole arc: over walls, under the gate.",
         science="One change can affect every obstacle on the path.",
         target=Target(40, 12, 1.6), xmax=57, ymax=32,
         obstacles=(Obstacle(8, 10, 0, 5, "wall"),
                    Obstacle(19, 23, 23.5, 29.5, "gate"),
                    Obstacle(31, 33, 0, 10, "wall")),
         starter="# Final course!\nspeed = 10\nup = 18\ngravity = 6", world="FINAL COURSE"),
]

ERRORS = {
    "syntax": "Use one line per variable: speed = 8",
    "name": "Use only speed, up, and gravity.",
    "duplicate": "Each variable needs just one value.",
    "number": "Use a number after the = sign.",
    "range": "Choose numbers above 0 and at most 30.",
    "missing": "Your rocket needs speed, up, and gravity.",
}


def load_progress() -> set[int]:
    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # Old saves used indices 0-7; only old missions 6-8 remain.
            return {n - 5 for n in data if type(n) is int and 5 <= n <= 7}
        if isinstance(data, dict) and data.get("version") == PROGRESS_VERSION:
            completed = data.get("completed", [])
            if isinstance(completed, list):
                return {n for n in completed if type(n) is int and 0 <= n < len(MISSIONS)}
    except (OSError, ValueError, TypeError):
        pass
    return set()


def save_progress(completed: set[int]) -> None:
    try:
        SAVE_FILE.write_text(json.dumps({"version": PROGRESS_VERSION,
                                         "completed": sorted(completed)}), encoding="utf-8")
    except OSError:
        pass  # The game still works in a read-only folder.


class Game:
    def __init__(self) -> None:
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Mika's Motion Lab · Python + Physics")
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.sounds = Sounds()
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans", 15)
        self.small = pygame.font.SysFont("dejavusans", 12)
        self.tiny = pygame.font.SysFont("dejavusans", 10, bold=True)
        self.medium = pygame.font.SysFont("dejavusans", 19, bold=True)
        self.heading = pygame.font.SysFont("dejavusans", 33, bold=True)
        self.code_font = pygame.font.SysFont("dejavusansmono", 17)
        self.completed = load_progress()
        self.index = 0
        self.page_start = 0
        self.drafts = [m["starter"] for m in MISSIONS]
        self.cursor = len(self.drafts[0])
        self.editor_focus = False
        self.select_all = False
        self.message = "Try changing a number. What do you predict?"
        self.message_kind = "tip"
        self.flight = None
        self.settings = None
        self.flight_progress = 0.0
        self.animation = False
        self.show_path = False
        self.show_telemetry = False
        self.stars = [(random.randrange(50, 520), random.randrange(328, 550), random.choice((1, 1, 2))) for _ in range(35)]
        pygame.key.start_text_input()

    @property
    def mission(self) -> dict:
        return MISSIONS[self.index]

    @property
    def code(self) -> str:
        return self.drafts[self.index]

    @code.setter
    def code(self, value: str) -> None:
        self.drafts[self.index] = value
        self.cursor = min(self.cursor, len(value))

    def text(self, value: str, x: int, y: int, color=INK, font=None) -> None:
        face = font or self.font
        self.canvas.blit(face.render(value, True, color), (x, y))

    def centered(self, value: str, x: int, y: int, color=INK, font=None) -> None:
        face = font or self.font
        image = face.render(value, True, color)
        self.canvas.blit(image, (x - image.get_width() // 2, y))

    def wrapped(self, value: str, x: int, y: int, max_width: int, color=MUTED, font=None, line_height=18) -> None:
        face = font or self.small
        line = ""
        for word in value.split():
            candidate = f"{line} {word}".strip()
            if line and face.size(candidate)[0] > max_width:
                self.text(line, x, y, color, face)
                y += line_height
                line = word
            else:
                line = candidate
        if line:
            self.text(line, x, y, color, face)

    def box(self, rect, color, radius=15, border=None, border_width=1) -> None:
        pygame.draw.rect(self.canvas, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.canvas, border, rect, border_width, border_radius=radius)

    def button(self, rect, label, fill, color=WHITE, border=None) -> None:
        self.box(rect, fill, 11, border)
        self.centered(label, rect.centerx, rect.y + (rect.height - self.font.get_height()) // 2, color)

    def map_point(self, x: float, y: float) -> tuple[int, int]:
        return int(65 + x / self.mission["xmax"] * 430), int(563 - y / self.mission["ymax"] * 214)

    def draw_rocket(self, x: int, y: int, angle: float = -35) -> None:
        rocket = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(rocket, (225, 248, 232, 45), (32, 32), 28)
        pygame.draw.polygon(rocket, (248, 247, 229), [(33, 7), (44, 30), (37, 46), (27, 46), (20, 30)])
        pygame.draw.polygon(rocket, PEACH, [(33, 7), (39, 17), (27, 17)])
        pygame.draw.polygon(rocket, PEACH, [(24, 34), (16, 49), (28, 44)])
        pygame.draw.polygon(rocket, PEACH, [(42, 34), (49, 49), (37, 44)])
        pygame.draw.circle(rocket, (101, 195, 202), (32, 29), 6)
        pygame.draw.polygon(rocket, (255, 199, 99), [(28, 45), (33, 59), (38, 45)])
        rotated = pygame.transform.rotozoom(rocket, angle, 0.9)
        self.canvas.blit(rotated, rotated.get_rect(center=(x, y)))

    def draw_telemetry(self) -> None:
        if not self.show_telemetry:
            return
        self.box(pygame.Rect(350, 326, 170, 118), (18, 43, 61), 13, (105, 165, 161))
        heading = "LIVE PHYSICS" if self.animation else "LAST FLIGHT" if self.flight else "AT LAUNCH"
        self.text(heading, 361, 336, (142, 222, 190), self.tiny)
        settings = self.settings if self.flight else None
        if settings is None:
            try:
                settings = read_code(self.code)
            except CodeError:
                settings = None
        if settings is None:
            values = ("—", "—", "—")
        else:
            time = 0.0
            if self.flight:
                time = self.flight.stop_time * self.flight_progress
            speed, height, gravity = motion_data(settings, time)
            values = (f"{speed:.1f} m/s", f"{height:.1f} m", f"{gravity:.1f} m/s²")
        for row, (label, value) in enumerate(zip(("SPEED", "HEIGHT", "GRAVITY"), values)):
            y = 359 + row * 26
            self.text(label, 361, y, (172, 202, 204), self.tiny)
            image = self.small.render(value, True, WHITE)
            self.canvas.blit(image, (509 - image.get_width(), y - 1))

    def draw_obstacles(self) -> None:
        for obstacle in self.mission.get("obstacles", ()):
            left, top = self.map_point(obstacle.x_left, obstacle.y_top)
            right, bottom = self.map_point(obstacle.x_right, obstacle.y_bottom)
            rect = pygame.Rect(left, top, right - left, bottom - top)
            if obstacle.kind == "wall":
                self.box(rect, (124, 93, 101), 4, (245, 166, 127), 2)
                for line_y in range(top + 15, bottom, 18):
                    pygame.draw.line(self.canvas, (174, 127, 123), (left + 3, line_y), (right - 3, line_y), 2)
                label = "WALL"
            else:
                self.box(rect, (69, 95, 128), 5, (152, 216, 231), 2)
                for dot_x in range(left + 10, right - 4, 18):
                    pygame.draw.circle(self.canvas, (185, 228, 233), (dot_x, top + 9), 2)
                label = "GATE"
            self.centered(label, rect.centerx, max(SCENE_RECT.y + 5, top - 17),
                          (255, 221, 177) if obstacle.kind == "wall" else (193, 238, 241), self.tiny)

    def draw_scene(self) -> None:
        self.box(SCENE_RECT, (21, 48, 74), 17)
        self.canvas.set_clip(SCENE_RECT)
        for x, y, r in self.stars:
            pygame.draw.circle(self.canvas, (183, 226, 223), (x, y), r)
        pygame.draw.circle(self.canvas, (252, 224, 163), (469, 381), 26)
        pygame.draw.circle(self.canvas, (252, 224, 163), (469, 381), 36, 2)
        pygame.draw.ellipse(self.canvas, (41, 93, 105), (-55, 538, 370, 95))
        pygame.draw.ellipse(self.canvas, (48, 106, 111), (184, 542, 455, 92))
        pygame.draw.ellipse(self.canvas, (68, 143, 130), (-50, 577, 640, 72))
        self.draw_obstacles()
        target = self.mission["target"]
        tx, ty = self.map_point(target.x, target.y)
        pygame.draw.circle(self.canvas, (124, 197, 172), (65, 563), 21)
        pygame.draw.circle(self.canvas, (251, 211, 126), (tx, ty), 24, 2)
        pygame.draw.circle(self.canvas, (255, 228, 161), (tx, ty), 14)
        pygame.draw.circle(self.canvas, (229, 148, 99), (tx, ty), 5)
        self.centered("TARGET", tx, max(321, ty - 40), (255, 239, 192), self.tiny)
        if self.show_path and self.settings and self.flight:
            points = [self.map_point(*position(self.settings, self.flight.stop_time * i / 100)) for i in range(101)]
            for i in range(0, 100, 2):
                pygame.draw.line(self.canvas, (177, 236, 217), points[i], points[i + 1], 2)
        if self.animation and self.settings and self.flight:
            t = self.flight.stop_time * self.flight_progress
            x, y = position(self.settings, t)
            slope = self.settings.up - self.settings.gravity * t
            angle = -math.degrees(math.atan2(slope, self.settings.speed))
            self.draw_rocket(*self.map_point(x, y), angle)
        elif self.flight and self.flight_progress >= 1 and self.settings:
            rocket_position = self.map_point(*position(self.settings, self.flight.stop_time))
            self.draw_rocket(*rocket_position)
            if self.flight.blocked:
                pygame.draw.circle(self.canvas, (255, 161, 119), rocket_position, 27, 3)
                self.centered("BONK!", rocket_position[0], max(SCENE_RECT.y + 6, rocket_position[1] - 46),
                              (255, 225, 174), self.tiny)
        else:
            self.draw_rocket(65, 563)
        self.draw_telemetry()
        self.canvas.set_clip(None)
        self.box(pygame.Rect(47, 505, 70, 24), (239, 250, 235), 12)
        self.centered("LAUNCH", 82, 511, (49, 104, 101), self.tiny)

    def draw_editor(self) -> None:
        self.box(EDITOR_RECT, (22, 43, 64), 12)
        self.box(pygame.Rect(570, 352, 292, 29), (34, 61, 78), 12)
        pygame.draw.rect(self.canvas, (34, 61, 78), (570, 369, 292, 12))
        for i, color in enumerate(((246, 156, 114), (244, 207, 129), (117, 207, 165))):
            pygame.draw.circle(self.canvas, color, (586 + i * 13, 367), 4)
        self.text("rocket.py", 783, 359, (192, 210, 209), self.small)
        line_height = 26
        for i, line in enumerate(self.code.split("\n")[:4]):
            color = (119, 174, 173) if line.lstrip().startswith("#") else (216, 244, 226)
            self.text(line[:27], 586, 386 + i * line_height, color, self.code_font)
        if self.editor_focus and pygame.time.get_ticks() % 1000 < 550:
            before = self.code[:self.cursor]
            row = min(before.count("\n"), 3)
            fragment = before.split("\n")[-1][:27]
            cx = 586 + self.code_font.size(fragment)[0]
            cy = 386 + row * line_height
            pygame.draw.line(self.canvas, (255, 222, 135), (cx, cy + 1), (cx, cy + 20), 2)
        if self.select_all and self.editor_focus:
            self.box(pygame.Rect(772, 478, 77, 18), (247, 203, 121), 7)
            self.centered("selected", 810, 481, INK, self.tiny)

    def draw(self) -> None:
        self.canvas.fill(CREAM)
        pygame.draw.circle(self.canvas, (232, 243, 234), (-36, 72), 130)
        pygame.draw.line(self.canvas, (220, 229, 220), (0, 65), (WIDTH, 65))
        self.box(pygame.Rect(24, 16, 32, 32), TEAL, 10)
        self.centered("✦", 40, 18, WHITE, self.medium)
        self.text("MIKA'S", 67, 20, INK, self.medium)
        self.text("MOTION LAB", 147, 20, TEAL, self.medium)
        sound_label = ("SOUND ON" if self.sounds.enabled else "SOUND OFF") if self.sounds.available else "NO AUDIO"
        self.button(SOUND_BUTTON, sound_label,
                    (228, 244, 235) if self.sounds.available and self.sounds.enabled else (235, 239, 234),
                    (31, 124, 101) if self.sounds.available and self.sounds.enabled else MUTED)
        self.text("PYTHON + PHYSICS", 768, 25, MUTED, self.tiny)

        self.text("MAKE IDEAS FLY.", 24, 83, INK, self.heading)
        self.text("Change Python numbers. Launch a rocket. Discover why it flies.", 26, 128, MUTED, self.small)
        self.box(pygame.Rect(718, 81, 158, 70), WHITE, 13, (222, 233, 222))
        self.text("MISSIONS COMPLETE", 730, 92, MUTED, self.tiny)
        self.text(f"{len(self.completed)} / {len(MISSIONS)}", 730, 111, TEAL, self.medium)
        self.box(pygame.Rect(789, 134, 75, 7), (230, 239, 231), 4)
        if self.completed:
            self.box(pygame.Rect(789, 134, 75 * len(self.completed) // len(MISSIONS), 7), TEAL, 4)

        self.box(PREV_PAGE_BUTTON, TEAL if self.page_start else (233, 240, 233), 10)
        self.centered("‹", PREV_PAGE_BUTTON.centerx, 173,
                      WHITE if self.page_start else (151, 169, 157), self.medium)
        has_next = self.page_start + MISSIONS_PER_PAGE < len(MISSIONS)
        self.box(NEXT_PAGE_BUTTON, TEAL if has_next else (233, 240, 233), 10)
        self.centered("›", NEXT_PAGE_BUTTON.centerx, 173,
                      WHITE if has_next else (151, 169, 157), self.medium)
        for slot, i in enumerate(range(self.page_start, min(self.page_start + MISSIONS_PER_PAGE, len(MISSIONS)))):
            mission = MISSIONS[i]
            rect = pygame.Rect(64 + slot * 155, 166, 150, 39)
            active = i == self.index
            self.box(rect, TEAL if active else WHITE, 10, None if active else (221, 231, 223))
            label = f"{mission['icon']}   {mission['name']}{'  ★' if i in self.completed else ''}"
            self.centered(label, rect.centerx, 177, WHITE if active else MUTED, self.small)

        self.box(pygame.Rect(24, 225, 520, 439), WHITE, 18, (226, 233, 226))
        self.box(pygame.Rect(556, 225, 320, 439), WHITE, 18, (226, 233, 226))
        self.text(f"MISSION {self.mission['icon']}", 40, 239, TEAL, self.tiny)
        self.text(self.mission["title"], 40, 255, INK, self.medium)
        self.text(self.mission["description"], 40, 286, MUTED, self.small)
        badge_width = max(82, self.tiny.size(self.mission["world"])[0] + 20)
        badge_x = 528 - badge_width
        self.box(pygame.Rect(badge_x, 239, badge_width, 24), (238, 246, 236), 12)
        self.centered(self.mission["world"], badge_x + badge_width // 2, 245, (58, 123, 112), self.tiny)
        self.draw_scene()
        target = self.mission["target"]
        self.text(f"TARGET  {target.x:g} m across · {target.y:g} m up", 40, 625, (73, 113, 116), self.small)
        flight_label = f"FLIGHT  {self.flight.range:.1f} m" if self.flight else "FLIGHT  —"
        self.text(flight_label, 279, 625, (73, 113, 116), self.small)
        self.button(DATA_BUTTON, "HIDE DATA" if self.show_telemetry else "SHOW DATA",
                    TEAL if self.show_telemetry else (231, 243, 236),
                    WHITE if self.show_telemetry else (42, 112, 99))

        self.box(pygame.Rect(570, 241, 35, 35), (229, 245, 237), 10)
        self.centered("</>", 587, 250, TEAL, self.small)
        self.text("YOUR CODE", 614, 241, TEAL, self.tiny)
        self.text("Rocket controls", 614, 253, INK, self.medium)
        self.wrapped(self.mission["instruction"], 570, 290, 290, MUTED, self.small, 17)
        self.text("Click code to edit · Ctrl+Enter launches", 570, 332, (131, 148, 151), self.tiny)
        self.draw_editor()
        self.button(RUN_BUTTON, "▶  RUN & LAUNCH", PEACH)
        self.button(RESET_BUTTON, "RESET", (236, 244, 236), (70, 110, 103))
        feedback_fill = (232, 247, 235) if self.message_kind == "success" else (255, 239, 230) if self.message_kind == "error" else (242, 248, 242)
        self.box(pygame.Rect(570, 569, 292, 80), feedback_fill, 11)
        self.text("★" if self.message_kind == "success" else "!" if self.message_kind == "error" else "?", 582, 578, TEAL if self.message_kind == "success" else PEACH, self.medium)
        self.wrapped(self.message, 608, 578, 242, (60, 103, 94), self.small, 16)
        self.wrapped(self.mission["science"], 608, 616, 240, (125, 142, 123), self.tiny, 12)
        self.text("Experiment first. Then explain what changed.", 24, 680, (139, 154, 146), self.tiny)

        window_size = self.window.get_size()
        scale = min(window_size[0] / WIDTH, window_size[1] / HEIGHT)
        size = (round(WIDTH * scale), round(HEIGHT * scale))
        offset = ((window_size[0] - size[0]) // 2, (window_size[1] - size[1]) // 2)
        self.window.fill((224, 233, 227))
        self.window.blit(pygame.transform.smoothscale(self.canvas, size), offset)
        pygame.display.flip()

    def mouse_point(self, event_pos: tuple[int, int]) -> tuple[float, float]:
        w, h = self.window.get_size()
        scale = min(w / WIDTH, h / HEIGHT)
        return (event_pos[0] - (w - WIDTH * scale) / 2) / scale, (event_pos[1] - (h - HEIGHT * scale) / 2) / scale

    def select_mission(self, index: int) -> None:
        self.sounds.play("click")
        self.index = index
        self.page_start = (index // MISSIONS_PER_PAGE) * MISSIONS_PER_PAGE
        self.cursor = len(self.code)
        self.editor_focus = False
        self.select_all = False
        self.flight = None
        self.settings = None
        self.animation = False
        self.show_path = False
        self.flight_progress = 0
        self.message = "Try changing a number. What do you predict?"
        self.message_kind = "tip"

    def launch(self) -> None:
        try:
            self.settings = read_code(self.code)
        except CodeError as exc:
            self.message, self.message_kind = ERRORS[exc.code], "error"
            self.sounds.play("miss")
            return
        self.sounds.play("launch")
        self.flight = flight_to(self.settings, self.mission["target"], self.mission.get("obstacles", ()))
        self.animation = True
        self.show_path = True
        self.flight_progress = 0
        self.message, self.message_kind = "Watch the flight!", "tip"

    def finish_flight(self) -> None:
        self.animation = False
        flight = self.flight
        target = self.mission["target"]
        if flight.hit:
            self.sounds.play("success")
            self.completed.add(self.index)
            save_progress(self.completed)
            self.message = f"All {len(MISSIONS)} done! Make your own experiment!" if len(self.completed) == len(MISSIONS) else "Great hit! What did your change do?"
            self.message_kind = "success"
            return
        if flight.blocked:
            self.sounds.play("impact")
            obstacle = self.mission["obstacles"][flight.obstacle_index]
            self.message = ("The wall stopped the rocket. Aim higher!" if obstacle.kind == "wall"
                            else self.mission.get("gate_hint", "The gate stopped the rocket. Fly lower!"))
            self.message_kind = "error"
            return
        self.sounds.play("miss")
        if flight.range < target.x - target.radius:
            self.message = "Too short. Try more speed or more up."
        elif target.y < 2 and flight.range > target.x + target.radius:
            self.message = "Too far. Try less speed."
        else:
            _, y = position(self.settings, target.x / self.settings.speed)
            self.message = "Too low. Try more up or less gravity." if y < target.y else "Too high. Try less up or more gravity."
        self.message_kind = "error"

    def edit_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_CTRL:
            self.launch()
            return
        self.sounds.play("key")
        if event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
            self.select_all = True
            return
        if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            if self.select_all:
                self.code, self.cursor, self.select_all = "", 0, False
            elif event.key == pygame.K_BACKSPACE and self.cursor:
                self.code = self.code[:self.cursor - 1] + self.code[self.cursor:]
                self.cursor -= 1
            elif event.key == pygame.K_DELETE:
                self.code = self.code[:self.cursor] + self.code[self.cursor + 1:]
        elif event.key == pygame.K_LEFT:
            self.cursor = max(0, self.cursor - 1)
            self.select_all = False
        elif event.key == pygame.K_RIGHT:
            self.cursor = min(len(self.code), self.cursor + 1)
            self.select_all = False
        elif event.key == pygame.K_HOME:
            self.cursor -= len(self.code[:self.cursor].split("\n")[-1])
        elif event.key == pygame.K_END:
            self.cursor += len(self.code[self.cursor:].split("\n")[0])
        elif event.key == pygame.K_RETURN and self.code.count("\n") < 3:
            self.insert("\n")

    def insert(self, text: str) -> None:
        if self.select_all:
            self.code, self.cursor, self.select_all = "", 0, False
        if len(self.code) + len(text) > 120:
            return
        self.code = self.code[:self.cursor] + text + self.code[self.cursor:]
        self.cursor += len(text)
        self.sounds.play("key")

    def handle_mouse(self, point: tuple[float, float]) -> None:
        x, y = point
        if SOUND_BUTTON.collidepoint(x, y):
            self.sounds.toggle()
            return
        if PREV_PAGE_BUTTON.collidepoint(x, y) and self.page_start:
            self.select_mission(self.page_start - MISSIONS_PER_PAGE)
            return
        if NEXT_PAGE_BUTTON.collidepoint(x, y) and self.page_start + MISSIONS_PER_PAGE < len(MISSIONS):
            self.select_mission(self.page_start + MISSIONS_PER_PAGE)
            return
        for slot, i in enumerate(range(self.page_start, min(self.page_start + MISSIONS_PER_PAGE, len(MISSIONS)))):
            if pygame.Rect(64 + slot * 155, 166, 150, 39).collidepoint(x, y):
                self.select_mission(i)
                return
        if DATA_BUTTON.collidepoint(x, y):
            self.show_telemetry = not self.show_telemetry
            self.sounds.play("click")
        elif RUN_BUTTON.collidepoint(x, y):
            self.launch()
        elif RESET_BUTTON.collidepoint(x, y):
            self.code = self.mission["starter"]
            self.cursor = len(self.code)
            self.message, self.message_kind = "Code reset. Try a new number!", "tip"
            self.sounds.play("click")
        elif pygame.Rect(570, 381, 292, 121).collidepoint(x, y):
            self.editor_focus = True
            self.select_all = False
            row = min(max(int((y - 386) // 26), 0), len(self.code.split("\n")) - 1)
            lines = self.code.split("\n")
            col = min(len(lines[row]), max(0, round((x - 586) / max(1, self.code_font.size("0")[0]))))
            self.cursor = sum(len(line) + 1 for line in lines[:row]) + col
        else:
            self.editor_focus = False

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(60) / 1000, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode((max(760, event.w), max(500, event.h)), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse(self.mouse_point(event.pos))
                elif event.type == pygame.KEYDOWN and self.editor_focus:
                    self.edit_key(event)
                elif event.type == pygame.TEXTINPUT and self.editor_focus:
                    if event.text.isprintable() and event.text not in "\r\n":
                        self.insert(event.text)
            if self.animation:
                self.flight_progress = min(1.0, self.flight_progress + dt / 2.8)
                if self.flight_progress >= 1:
                    self.finish_flight()
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
