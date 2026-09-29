"""__APP_TITLE__ — a pygame arcade game.

Dodge the falling rocks and collect stars. Arrow keys / A-D to move, P or Esc
to pause, Enter or Space to start.

Run `python main.py --smoke-test` to simulate a few seconds of play headlessly.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

import settings as S  # noqa: E402

HIGHSCORE_PATH = Path.home() / S.HIGHSCORE_FILE


def load_high_score() -> int:
    try:
        return int(HIGHSCORE_PATH.read_text().strip())
    except (OSError, ValueError):
        return 0


def save_high_score(value: int) -> None:
    try:
        HIGHSCORE_PATH.write_text(str(value))
    except OSError:
        pass


def circles_hit(a, b) -> bool:
    return math.hypot(a.x - b.x, a.y - b.y) < a.r + b.r


class Player:
    def __init__(self) -> None:
        self.x = S.WIDTH / 2
        self.y = S.HEIGHT - 80
        self.r = 18
        self.invulnerable = 0.0

    def update(self, dt: float, direction: float) -> None:
        self.x = max(self.r, min(S.WIDTH - self.r, self.x + direction * S.PLAYER_SPEED * dt))
        self.invulnerable = max(0.0, self.invulnerable - dt)

    def draw(self, surf: pygame.Surface) -> None:
        if self.invulnerable > 0 and int(self.invulnerable * 10) % 2 == 0:
            return  # blink while invulnerable
        x, y, r = self.x, self.y, self.r
        pygame.draw.polygon(surf, S.ACCENT, [(x, y - r - 4), (x + r, y + r), (x, y + r * 0.5), (x - r, y + r)])
        pygame.draw.rect(surf, S.FLAME, (x - 4, y + r * 0.6, 8, 6 + random.random() * 6))


class Hazard:
    def __init__(self, speed: float) -> None:
        self.r = random.uniform(14, 30)
        self.x = random.uniform(self.r, S.WIDTH - self.r)
        self.y = -self.r
        self.vy = speed * random.uniform(0.8, 1.25)
        self.spin = random.uniform(-2, 2)
        self.angle = 0.0
        self.shape = [
            (i / 8 * math.tau, self.r * random.uniform(0.75, 1.05)) for i in range(8)
        ]

    def update(self, dt: float) -> None:
        self.y += self.vy * dt
        self.angle += self.spin * dt

    @property
    def gone(self) -> bool:
        return self.y - self.r > S.HEIGHT

    def draw(self, surf: pygame.Surface) -> None:
        pts = [(self.x + math.cos(a + self.angle) * d, self.y + math.sin(a + self.angle) * d) for a, d in self.shape]
        pygame.draw.polygon(surf, S.ROCK, pts)
        pygame.draw.polygon(surf, S.ROCK_EDGE, pts, 2)


class Pickup:
    def __init__(self, speed: float) -> None:
        self.r = 12
        self.x = random.uniform(self.r, S.WIDTH - self.r)
        self.y = -self.r
        self.vy = speed * 0.7
        self.t = 0.0

    def update(self, dt: float) -> None:
        self.y += self.vy * dt
        self.t += dt

    @property
    def gone(self) -> bool:
        return self.y - self.r > S.HEIGHT

    def draw(self, surf: pygame.Surface) -> None:
        pulse = 1 + math.sin(self.t * 8) * 0.15
        pts = []
        for i in range(10):
            a = i / 10 * math.tau - math.pi / 2
            rad = (self.r if i % 2 == 0 else self.r * 0.45) * pulse
            pts.append((self.x + math.cos(a) * rad, self.y + math.sin(a) * rad))
        pygame.draw.polygon(surf, S.STAR, pts)


class Game:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_big = pygame.font.SysFont(None, 56)
        self.font = pygame.font.SysFont(None, 28)
        self.font_small = pygame.font.SysFont(None, 22)
        self.high_score = load_high_score()
        self.state = "menu"  # menu | playing | paused | gameover
        self.stars = [
            [random.uniform(0, S.WIDTH), random.uniform(0, S.HEIGHT), random.uniform(1, 2), random.uniform(20, 80)]
            for _ in range(80)
        ]
        self.reset()

    def reset(self) -> None:
        self.player = Player()
        self.hazards: list[Hazard] = []
        self.pickups: list[Pickup] = []
        self.score = 0.0
        self.lives = S.START_LIVES
        self.level = 1
        self.hazard_timer = 0.0
        self.pickup_timer = S.PICKUP_SPAWN_EVERY

    # ------------------------------------------------------------ input

    def on_action(self) -> None:
        if self.state in ("menu", "gameover"):
            self.reset()
            self.state = "playing"

    def toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_action()
            elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                self.toggle_pause()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.on_action()
        elif event.type == pygame.WINDOWFOCUSLOST and self.state == "playing":
            self.state = "paused"

    def direction(self) -> float:
        keys = pygame.key.get_pressed()
        d = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            d -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            d += 1
        if pygame.mouse.get_pressed()[0]:
            d = max(-1.0, min(1.0, (pygame.mouse.get_pos()[0] - self.player.x) / 40))
        return d

    # ------------------------------------------------------------ simulation

    def hazard_speed(self) -> float:
        return S.HAZARD_BASE_SPEED + (self.level - 1) * S.HAZARD_SPEED_PER_LEVEL

    def update(self, dt: float, direction: float = 0.0) -> None:
        star_speed = 1 + self.level * 0.2 if self.state == "playing" else 0.5
        for s in self.stars:
            s[1] += s[3] * dt * star_speed
            if s[1] > S.HEIGHT:
                s[0], s[1] = random.uniform(0, S.WIDTH), 0
        if self.state != "playing":
            return

        self.player.update(dt, direction)

        self.hazard_timer -= dt
        if self.hazard_timer <= 0:
            self.hazards.append(Hazard(self.hazard_speed()))
            self.hazard_timer = max(0.25, S.HAZARD_SPAWN_EVERY - (self.level - 1) * 0.07)
        self.pickup_timer -= dt
        if self.pickup_timer <= 0:
            self.pickups.append(Pickup(self.hazard_speed()))
            self.pickup_timer = S.PICKUP_SPAWN_EVERY

        for h in self.hazards:
            h.update(dt)
        for p in self.pickups:
            p.update(dt)

        for h in self.hazards:
            if self.player.invulnerable == 0 and circles_hit(self.player, h):
                h.y = S.HEIGHT + 999
                self.lives -= 1
                self.player.invulnerable = S.INVULNERABLE_TIME
                if self.lives <= 0:
                    self.game_over()
                    return
        for p in self.pickups:
            if circles_hit(self.player, p):
                p.y = S.HEIGHT + 999
                self.score += 25

        self.score += dt * 10  # survival points
        self.level = 1 + int(self.score // S.POINTS_PER_LEVEL)
        self.hazards = [h for h in self.hazards if not h.gone]
        self.pickups = [p for p in self.pickups if not p.gone]

    def game_over(self) -> None:
        self.state = "gameover"
        if int(self.score) > self.high_score:
            self.high_score = int(self.score)
            save_high_score(self.high_score)

    # ------------------------------------------------------------ rendering

    def text(self, value: str, pos, font=None, color=S.TEXT, anchor: str = "center") -> None:
        img = (font or self.font).render(value, True, color)
        rect = img.get_rect(**{anchor: pos})
        self.screen.blit(img, rect)

    def draw(self) -> None:
        self.screen.fill(S.BG)
        for x, y, size, _ in self.stars:
            self.screen.fill((255, 255, 255), (x, y, size, size))

        cx, cy = S.WIDTH // 2, S.HEIGHT // 2
        if self.state == "menu":
            self.text(S.TITLE, (cx, cy - 60), self.font_big)
            self.text("Dodge the rocks, grab the stars", (cx, cy - 10), self.font_small, S.MUTED)
            self.text("Press Enter / Click to start", (cx, cy + 40), color=S.ACCENT)
            self.text(f"High score: {self.high_score}", (cx, cy + 90), self.font_small, S.MUTED)
            return

        for p in self.pickups:
            p.draw(self.screen)
        for h in self.hazards:
            h.draw(self.screen)
        self.player.draw(self.screen)

        self.text(f"Score {int(self.score)}", (16, 20), anchor="midleft")
        self.text(f"Level {self.level}", (cx, 20))
        self.text("<3 " * max(0, self.lives), (S.WIDTH - 16, 20), color=S.DANGER, anchor="midright")

        if self.state == "paused":
            self.text("Paused", (cx, cy), self.font_big)
            self.text("Press P to resume", (cx, cy + 45), self.font_small, S.MUTED)
        elif self.state == "gameover":
            shade = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            self.screen.blit(shade, (0, 0))
            self.text("Game over", (cx, cy - 40), self.font_big, S.DANGER)
            self.text(f"Score: {int(self.score)}   Best: {self.high_score}", (cx, cy + 5))
            self.text("Press Enter / Click to play again", (cx, cy + 50), self.font_small, S.ACCENT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=S.TITLE)
    parser.add_argument("--smoke-test", action="store_true", help="Simulate a few seconds of play and exit")
    args = parser.parse_args(argv)

    pygame.init()
    pygame.display.set_caption(S.TITLE)
    screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
    clock = pygame.time.Clock()
    game = Game(screen)

    if args.smoke_test:
        game.on_action()
        for frame in range(S.FPS * 5):
            game.update(1 / S.FPS, direction=math.sin(frame / 20))
            game.draw()
        pygame.quit()
        print(f"Smoke test OK: state={game.state} score={int(game.score)} level={game.level}")
        return 0

    running = True
    while running:
        dt = min(0.05, clock.tick(S.FPS) / 1000)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)
        game.update(dt, game.direction())
        game.draw()
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
