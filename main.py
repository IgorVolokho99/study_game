"""Mika's Motion Lab — a small Pygame game about Python and motion."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import pygame

from physics import CodeError, Settings, Target, flight_to, motion_data, position, read_code


WIDTH, HEIGHT = 1200, 760
SAVE_FILE = Path(__file__).with_name(".motion_lab_progress.json")

INK = (27, 48, 68)
MUTED = (93, 115, 124)
TEAL = (28, 150, 124)
CREAM = (248, 247, 239)
PEACH = (244, 139, 100)
WHITE = (255, 255, 255)
DATA_BUTTON = pygame.Rect(613, 661, 143, 35)

MISSIONS = [
    dict(name="Earth launch", icon="01", title="Reach the landing pad",
         description="The pad is 16 meters away. Can you land on it?",
         instruction="Change speed. More speed means more distance sideways.",
         science="Speed goes sideways. Gravity pulls down.",
         target=Target(16, 0, 1.15), xmax=25, ymax=14,
         starter="# Change a number!\nspeed = 6\nup = 10\ngravity = 10", world="EARTH"),
    dict(name="Moon bounce", icon="02", title="Catch the moon star",
         description="The star is 40 meters across and 25 meters up.",
         instruction="Change gravity. The Moon pulls much less strongly.",
         science="Less gravity means more time in the air.",
         target=Target(40, 25, 2.2), xmax=85, ymax=32,
         starter="# Try smaller gravity!\nspeed = 8\nup = 10\ngravity = 10", world="MOON"),
    dict(name="Planet puzzle", icon="03", title="Find the floating crystal",
         description="The crystal is 36 meters across and 9 meters up.",
         instruction="Try speed and up. Change one number at a time.",
         science="Up starts a climb; gravity slows it.",
         target=Target(36, 9, 1.8), xmax=55, ymax=27,
         starter="# Tune your rocket!\nspeed = 8\nup = 12\ngravity = 6", world="NEW PLANET"),
    dict(name="Sky bridge", icon="04", title="Fly over the canyon",
         description="A bridge floats 24 meters across and 15 meters up.",
         instruction="Change up. A stronger push makes a higher arc.",
         science="More up makes the rocket climb higher.",
         target=Target(24, 15, 1.5), xmax=42, ymax=26,
         starter="# Reach the high bridge!\nspeed = 8\nup = 10\ngravity = 10", world="SKY BRIDGE"),
    dict(name="Heavy planet", icon="05", title="Beat the strong gravity",
         description="A beacon is 30 meters across and 6 meters up.",
         instruction="Gravity is strong here. Tune speed and up together.",
         science="A stronger pull needs a bigger upward push.",
         target=Target(30, 6, 1.6), xmax=48, ymax=23,
         starter="# Strong gravity!\nspeed = 8\nup = 12\ngravity = 12", world="HEAVY PLANET"),
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
        return {n for n in data if isinstance(n, int) and 0 <= n < len(MISSIONS)}
    except (OSError, ValueError, TypeError):
        return set()


def save_progress(completed: set[int]) -> None:
    try:
        SAVE_FILE.write_text(json.dumps(sorted(completed)), encoding="utf-8")
    except OSError:
        pass  # The game still works in a read-only folder.


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Mika's Motion Lab · Python + Physics")
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans", 16)
        self.small = pygame.font.SysFont("dejavusans", 13)
        self.tiny = pygame.font.SysFont("dejavusans", 11, bold=True)
        self.medium = pygame.font.SysFont("dejavusans", 21, bold=True)
        self.heading = pygame.font.SysFont("dejavusans", 38, bold=True)
        self.code_font = pygame.font.SysFont("dejavusansmono", 19)
        self.completed = load_progress()
        self.index = 0
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
        self.stars = [(random.randrange(75, 735), random.randrange(370, 590), random.choice((1, 1, 2))) for _ in range(45)]
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
        return int(94 + x / self.mission["xmax"] * 622), int(614 - y / self.mission["ymax"] * 230)

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
        self.box(pygame.Rect(524, 360, 220, 128), (18, 43, 61), 13, (105, 165, 161))
        heading = "LIVE PHYSICS" if self.animation else "LAST FLIGHT" if self.flight else "AT LAUNCH"
        self.text(heading, 538, 370, (142, 222, 190), self.tiny)
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
                stop = self.flight.closest_time if self.flight.hit else self.flight.duration
                time = stop * self.flight_progress
            speed, height, gravity = motion_data(settings, time)
            values = (f"{speed:.1f} m/s", f"{height:.1f} m", f"{gravity:.1f} m/s²")
        for row, (label, value) in enumerate(zip(("SPEED", "HEIGHT", "GRAVITY"), values)):
            y = 394 + row * 29
            self.text(label, 538, y, (172, 202, 204), self.tiny)
            image = self.small.render(value, True, WHITE)
            self.canvas.blit(image, (731 - image.get_width(), y - 1))

    def draw_scene(self) -> None:
        scene = pygame.Rect(57, 349, 699, 302)
        self.box(scene, (21, 48, 74), 17)
        self.canvas.set_clip(scene)
        for x, y, r in self.stars:
            pygame.draw.circle(self.canvas, (183, 226, 223), (x, y), r)
        pygame.draw.circle(self.canvas, (252, 224, 163), (669, 416), 31)
        pygame.draw.circle(self.canvas, (252, 224, 163, 35), (669, 416), 43, 2)
        pygame.draw.ellipse(self.canvas, (41, 93, 105), (-85, 586, 510, 115))
        pygame.draw.ellipse(self.canvas, (48, 106, 111), (245, 587, 640, 115))
        pygame.draw.ellipse(self.canvas, (68, 143, 130), (-70, 625, 930, 91))
        target = self.mission["target"]
        tx, ty = self.map_point(target.x, target.y)
        pygame.draw.circle(self.canvas, (124, 197, 172), (94, 614), 21)
        pygame.draw.circle(self.canvas, (251, 211, 126), (tx, ty), 24, 2)
        pygame.draw.circle(self.canvas, (255, 228, 161), (tx, ty), 14)
        pygame.draw.circle(self.canvas, (229, 148, 99), (tx, ty), 5)
        self.centered("TARGET", tx, max(356, ty - 43), (255, 239, 192), self.tiny)
        if self.show_path and self.settings and self.flight:
            points = [self.map_point(*position(self.settings, self.flight.duration * i / 100)) for i in range(101)]
            for i in range(0, 100, 2):
                pygame.draw.line(self.canvas, (177, 236, 217), points[i], points[i + 1], 2)
        if self.animation and self.settings and self.flight:
            stop = self.flight.closest_time if self.flight.hit else self.flight.duration
            t = stop * self.flight_progress
            x, y = position(self.settings, t)
            slope = self.settings.up - self.settings.gravity * t
            angle = -math.degrees(math.atan2(slope, self.settings.speed))
            self.draw_rocket(*self.map_point(x, y), angle)
        elif self.flight and self.flight_progress >= 1 and self.settings:
            stop = self.flight.closest_time if self.flight.hit else self.flight.duration
            self.draw_rocket(*self.map_point(*position(self.settings, stop)))
        else:
            self.draw_rocket(94, 614)
        self.draw_telemetry()
        self.canvas.set_clip(None)
        self.box(pygame.Rect(69, 571, 76, 27), (239, 250, 235), 13)
        self.centered("LAUNCH", 107, 577, (49, 104, 101), self.tiny)

    def draw_editor(self) -> None:
        self.box(pygame.Rect(806, 405, 344, 159), (22, 43, 64), 12)
        self.box(pygame.Rect(806, 405, 344, 32), (34, 61, 78), 12)
        pygame.draw.rect(self.canvas, (34, 61, 78), (806, 423, 344, 14))
        for i, color in enumerate(((246, 156, 114), (244, 207, 129), (117, 207, 165))):
            pygame.draw.circle(self.canvas, color, (823 + i * 14, 421), 4)
        self.text("rocket.py", 1060, 411, (192, 210, 209), self.small)
        line_height = 28
        for i, line in enumerate(self.code.split("\n")[:4]):
            color = (119, 174, 173) if line.lstrip().startswith("#") else (216, 244, 226)
            self.text(line[:30], 825, 443 + i * line_height, color, self.code_font)
        if self.editor_focus and pygame.time.get_ticks() % 1000 < 550:
            before = self.code[:self.cursor]
            row = min(before.count("\n"), 3)
            fragment = before.split("\n")[-1][:30]
            cx = 825 + self.code_font.size(fragment)[0]
            cy = 443 + row * line_height
            pygame.draw.line(self.canvas, (255, 222, 135), (cx, cy + 2), (cx, cy + 22), 2)
        if self.select_all and self.editor_focus:
            self.box(pygame.Rect(1049, 541, 89, 18), (247, 203, 121), 7)
            self.centered("selected", 1093, 543, INK, self.tiny)

    def draw(self) -> None:
        self.canvas.fill(CREAM)
        pygame.draw.circle(self.canvas, (232, 243, 234), (-42, 90), 166)
        pygame.draw.line(self.canvas, (220, 229, 220), (0, 81), (WIDTH, 81))
        self.box(pygame.Rect(38, 25, 36, 36), TEAL, 11)
        self.centered("✦", 56, 28, WHITE, self.medium)
        self.text("Mika'S", 86, 28, INK, self.medium)
        self.text("MOTION LAB", 171, 28, TEAL, self.medium)
        self.text("PYTHON + PHYSICS", 1002, 32, MUTED, self.tiny)

        self.text("MAKE IDEAS FLY.", 38, 112, INK, self.heading)
        self.text("Change Python numbers. Launch a rocket. Discover why it flies.", 40, 159, MUTED)
        self.box(pygame.Rect(962, 107, 199, 73), WHITE, 14, (222, 233, 222))
        self.text("MISSIONS COMPLETE", 979, 120, MUTED, self.tiny)
        self.text(f"{len(self.completed)} / {len(MISSIONS)}", 980, 137, TEAL, self.medium)
        self.box(pygame.Rect(1041, 151, 101, 8), (230, 239, 231), 4)
        if self.completed:
            self.box(pygame.Rect(1041, 151, 101 * len(self.completed) // len(MISSIONS), 8), TEAL, 4)

        for i, mission in enumerate(MISSIONS):
            rect = pygame.Rect(38 + i * 226, 205, 215, 43)
            active = i == self.index
            self.box(rect, TEAL if active else WHITE, 11, None if active else (221, 231, 223))
            label = f"{mission['icon']}   {mission['name']}{'  ★' if i in self.completed else ''}"
            self.centered(label, rect.centerx, 216, WHITE if active else MUTED, self.small)

        self.box(pygame.Rect(38, 265, 738, 455), WHITE, 20, (226, 233, 226))
        self.box(pygame.Rect(788, 265, 374, 455), WHITE, 20, (226, 233, 226))
        self.text(f"MISSION {self.mission['icon']}", 58, 283, TEAL, self.tiny)
        self.text(self.mission["title"], 58, 299, INK, self.medium)
        self.text(self.mission["description"], 58, 328, MUTED, self.small)
        badge_width = max(98, self.tiny.size(self.mission["world"])[0] + 24)
        badge_x = 752 - badge_width
        self.box(pygame.Rect(badge_x, 282, badge_width, 27), (238, 246, 236), 13)
        self.centered(self.mission["world"], badge_x + badge_width // 2, 290, (58, 123, 112), self.tiny)
        self.draw_scene()
        target = self.mission["target"]
        self.text(f"TARGET  {target.x:g} m across  ·  {target.y:g} m up", 58, 672, (73, 113, 116), self.small)
        flight_label = f"FLIGHT  {self.flight.range:.1f} m" if self.flight else "FLIGHT  —"
        self.text(flight_label, 349, 672, (73, 113, 116), self.small)
        self.button(DATA_BUTTON, "HIDE DATA" if self.show_telemetry else "SHOW DATA",
                    TEAL if self.show_telemetry else (231, 243, 236),
                    WHITE if self.show_telemetry else (42, 112, 99))

        self.box(pygame.Rect(806, 286, 39, 39), (229, 245, 237), 11)
        self.centered("</>", 825, 296, TEAL, self.small)
        self.text("YOUR CODE", 855, 287, TEAL, self.tiny)
        self.text("Rocket controls", 855, 300, INK, self.medium)
        self.wrapped(self.mission["instruction"], 806, 342, 340, MUTED, self.small)
        self.text("Click the code to edit it. Ctrl+Enter launches.", 806, 383, (131, 148, 151), self.tiny)
        self.draw_editor()
        self.button(pygame.Rect(806, 579, 211, 44), "▶  RUN & LAUNCH", PEACH)
        self.button(pygame.Rect(1026, 579, 124, 44), "RESET CODE", (236, 244, 236), (70, 110, 103))
        feedback_fill = (232, 247, 235) if self.message_kind == "success" else (255, 239, 230) if self.message_kind == "error" else (242, 248, 242)
        self.box(pygame.Rect(806, 639, 344, 63), feedback_fill, 11)
        self.text("★" if self.message_kind == "success" else "!" if self.message_kind == "error" else "?", 819, 648, TEAL if self.message_kind == "success" else PEACH, self.medium)
        self.text(self.message[:46], 849, 648, (60, 103, 94), self.small)
        self.wrapped(self.mission["science"], 849, 674, 292, (125, 142, 123), self.tiny, 13)
        self.text("Experiment first. Then explain what changed.", 39, 738, (139, 154, 146), self.tiny)

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
        self.index = index
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
            return
        self.flight = flight_to(self.settings, self.mission["target"])
        self.animation = True
        self.show_path = True
        self.flight_progress = 0
        self.message, self.message_kind = "Watch the flight!", "tip"

    def finish_flight(self) -> None:
        self.animation = False
        flight = self.flight
        target = self.mission["target"]
        if flight.hit:
            self.completed.add(self.index)
            save_progress(self.completed)
            self.message = f"All {len(MISSIONS)} done! Make your own experiment!" if len(self.completed) == len(MISSIONS) else "Great hit! What did your change do?"
            self.message_kind = "success"
            return
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

    def handle_mouse(self, point: tuple[float, float]) -> None:
        x, y = point
        for i in range(len(MISSIONS)):
            if pygame.Rect(38 + i * 226, 205, 215, 43).collidepoint(x, y):
                self.select_mission(i)
                return
        if DATA_BUTTON.collidepoint(x, y):
            self.show_telemetry = not self.show_telemetry
        elif pygame.Rect(806, 579, 211, 44).collidepoint(x, y):
            self.launch()
        elif pygame.Rect(1026, 579, 124, 44).collidepoint(x, y):
            self.code = self.mission["starter"]
            self.cursor = len(self.code)
            self.message, self.message_kind = "Code reset. Try a new number!", "tip"
        elif pygame.Rect(806, 437, 344, 127).collidepoint(x, y):
            self.editor_focus = True
            self.select_all = False
            row = min(max(int((y - 443) // 28), 0), len(self.code.split("\n")) - 1)
            lines = self.code.split("\n")
            col = min(len(lines[row]), max(0, round((x - 825) / max(1, self.code_font.size("0")[0]))))
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
