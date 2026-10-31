"""
Animation systems for Nusantara Property Tycoon:
- Cinematic 2.5D Dice Rolling with bounce and tumbling
- Token Hop and Movement Animation with landing feedback
- Floating Coin & Money Transactions with particle bursts
- Property Construction & Hotel upgrade visual effects
- Smooth Screen and Modal Transitions
- Toast Notification Manager
"""
import math
import random
import pygame
from typing import List, Tuple, Optional, Callable, Dict, Any
from ui.audio import AudioManager


class DiceAnimation:
    """Cinematic 2.5D dice rolling animation with tumbling, bounce, and shadow."""

    def __init__(self, duration: float = 0.85):
        self.default_duration = duration
        self.current_duration = duration
        self.time_elapsed: float = 0.0
        self.is_active: bool = False
        self.face1: int = 1
        self.face2: int = 1
        self.target1: int = 1
        self.target2: int = 1
        self.on_complete: Optional[Callable[[], None]] = None
        self._last_face_swap: float = 0.0

        # 2.5D vertical bounce height
        self.bounce_y: float = 0.0
        self.rotation_deg: float = 0.0

    def start(self, target1: int, target2: int, speed: str = "Normal", on_complete: Optional[Callable[[], None]] = None) -> None:
        if speed == "Instant":
            self.face1 = target1
            self.face2 = target2
            self.target1 = target1
            self.target2 = target2
            self.is_active = False
            self.bounce_y = 0.0
            AudioManager.get_instance().play_sfx("dice_land")
            if on_complete:
                on_complete()
            return

        self.current_duration = 0.42 if speed == "Fast" else self.default_duration
        self.time_elapsed = 0.0
        self.is_active = True
        self.target1 = target1
        self.target2 = target2
        self.face1 = random.randint(1, 6)
        self.face2 = random.randint(1, 6)
        self.on_complete = on_complete
        self._last_face_swap = 0.0
        self.bounce_y = 0.0
        self.rotation_deg = 0.0

        AudioManager.get_instance().play_sfx("dice_roll")

    def update(self, dt: float) -> None:
        if not self.is_active:
            return

        self.time_elapsed += dt
        self._last_face_swap += dt

        # Progress ratio 0.0 -> 1.0
        progress = min(1.0, self.time_elapsed / self.current_duration)

        # Dampened bounce curve: multiple bounces settling down
        bounce_envelope = max(0.0, 1.0 - progress)
        self.bounce_y = -abs(math.sin(progress * math.pi * 3.5)) * 32.0 * bounce_envelope
        self.rotation_deg = math.sin(progress * math.pi * 4.0) * 15.0 * bounce_envelope

        # Randomize faces during tumble
        swap_interval = 0.06 + progress * 0.05
        if self._last_face_swap >= swap_interval:
            self._last_face_swap = 0.0
            self.face1 = random.randint(1, 6)
            self.face2 = random.randint(1, 6)

        # Finished rolling
        if self.time_elapsed >= self.current_duration:
            self.is_active = False
            self.face1 = self.target1
            self.face2 = self.target2
            self.bounce_y = 0.0
            self.rotation_deg = 0.0
            AudioManager.get_instance().play_sfx("dice_land")
            if self.on_complete:
                cb = self.on_complete
                self.on_complete = None
                cb()


class MovementAnimation:
    """Step-by-step token movement with vertical hop arc and landing squash."""

    def __init__(self, step_duration: float = 0.14):
        self.default_step_duration = step_duration
        self.current_step_duration = step_duration
        self.is_active: bool = False
        self.path: List[int] = []
        self.current_step_idx: int = 0
        self.step_timer: float = 0.0
        self.current_tile: int = 0
        self.target_tile: int = 0

        # Hop offset: vertical bounce during step
        self.hop_offset_y: float = 0.0
        self.landing_scale: float = 1.0

        self.on_step: Optional[Callable[[int], None]] = None
        self.on_complete: Optional[Callable[[], None]] = None

    def start(
        self,
        path: List[int],
        start_tile: int,
        target_tile: int,
        speed: str = "Normal",
        on_step: Optional[Callable[[int], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ) -> None:
        if speed == "Instant" or not path:
            self.is_active = False
            self.current_tile = target_tile
            self.target_tile = target_tile
            self.hop_offset_y = 0.0
            if on_complete:
                on_complete()
            return

        self.current_step_duration = 0.07 if speed == "Fast" else self.default_step_duration
        self.is_active = True
        self.path = list(path)
        self.current_step_idx = 0
        self.step_timer = 0.0
        self.current_tile = start_tile
        self.target_tile = target_tile
        self.hop_offset_y = 0.0
        self.landing_scale = 1.0
        self.on_step = on_step
        self.on_complete = on_complete

    def skip(self) -> None:
        """Immediately complete movement animation."""
        if not self.is_active:
            return
        self.is_active = False
        self.current_tile = self.target_tile
        self.hop_offset_y = 0.0
        if self.on_complete:
            cb = self.on_complete
            self.on_complete = None
            cb()

    def update(self, dt: float) -> None:
        if not self.is_active:
            return

        self.step_timer += dt
        step_progress = min(1.0, self.step_timer / self.current_step_duration)

        # Parabolic hop arc (up and down between tiles)
        self.hop_offset_y = -math.sin(step_progress * math.pi) * 16.0

        if self.step_timer >= self.current_step_duration:
            self.step_timer = 0.0
            if self.current_step_idx < len(self.path):
                self.current_tile = self.path[self.current_step_idx]
                self.current_step_idx += 1
                AudioManager.get_instance().play_sfx("step")
                if self.on_step:
                    self.on_step(self.current_tile)

            # Check completion
            if self.current_step_idx >= len(self.path):
                self.is_active = False
                self.current_tile = self.target_tile
                self.hop_offset_y = 0.0
                if self.on_complete:
                    cb = self.on_complete
                    self.on_complete = None
                    cb()

    @property
    def remaining_steps(self) -> int:
        if not self.is_active:
            return 0
        return max(0, len(self.path) - self.current_step_idx)


class CoinParticle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = 0.0
        self.max_life = random.uniform(0.6, 1.1)

    @property
    def is_alive(self) -> bool:
        return self.life < self.max_life

    def update(self, dt: float) -> None:
        self.life += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 320.0 * dt  # Gravity


class FloatingTransaction:
    def __init__(self, text: str, x: int, y: int, color: Tuple[int, int, int], amount: int):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.amount = amount
        self.duration = 2.0
        self.time_alive = 0.0
        self.particles: List[CoinParticle] = []

        # Spawn gold or red coin burst particles
        burst_color = (255, 215, 0) if amount > 0 else (220, 70, 70)
        num_coins = min(12, max(4, abs(amount) // 500000))
        for _ in range(num_coins):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 180)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 80
            self.particles.append(CoinParticle(self.x, self.y, vx, vy, burst_color))

    @property
    def is_alive(self) -> bool:
        return self.time_alive < self.duration

    @property
    def alpha(self) -> int:
        if self.time_alive < 0.2:
            return int(255 * (self.time_alive / 0.2))
        elif self.time_alive > self.duration - 0.4:
            rem = self.duration - self.time_alive
            return max(0, int(255 * (rem / 0.4)))
        return 255

    def update(self, dt: float) -> None:
        self.time_alive += dt
        self.y -= 28.0 * dt  # Drift upward
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive]

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Draw particles
        for p in self.particles:
            alpha = int(255 * (1.0 - p.life / p.max_life))
            psurf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(psurf, (*p.color, alpha), (4, 4), 3)
            surface.blit(psurf, (int(p.x - 4), int(p.y - 4)))

        # Draw glowing pill badge with transaction text
        txt_s = font.render(self.text, True, self.color)
        px, py = 12, 6
        bw = txt_s.get_width() + px * 2
        bh = txt_s.get_height() + py * 2
        bx = int(self.x - bw // 2)
        by = int(self.y - bh // 2)

        pill_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pill_surf.fill((15, 25, 35, min(230, self.alpha)))
        pygame.draw.rect(pill_surf, (*self.color, min(200, self.alpha)), (0, 0, bw, bh), width=2, border_radius=12)
        txt_s.set_alpha(self.alpha)
        pill_surf.blit(txt_s, (px, py))
        surface.blit(pill_surf, (bx, by))


class ConstructionEffect:
    """Puff / sparkle animation when a house or hotel is built."""

    def __init__(self, center: Tuple[int, int], is_hotel: bool = False):
        self.cx, self.cy = center
        self.is_hotel = is_hotel
        self.life = 0.0
        self.duration = 0.85
        self.particles = []

        # Gold or teal construction dust particles
        color = (255, 215, 80) if is_hotel else (80, 220, 140)
        for _ in range(16 if is_hotel else 10):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(30, 90)
            self.particles.append({
                "x": float(self.cx),
                "y": float(self.cy),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd - 30,
                "col": color,
                "size": random.randint(2, 5)
            })

    @property
    def is_alive(self) -> bool:
        return self.life < self.duration

    def update(self, dt: float) -> None:
        self.life += dt
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 120 * dt

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, int(255 * (1.0 - self.life / self.duration)))
        for p in self.particles:
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["col"], alpha), (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"] - p["size"]), int(p["y"] - p["size"])))


class ScreenFadeTransition:
    """Smooth fade in/out alpha transition between screens."""

    def __init__(self, duration: float = 0.30):
        self.duration = duration
        self.timer = 0.0
        self.is_active = False
        self.fade_type = "out"  # 'in' or 'out'
        self.on_complete: Optional[Callable[[], None]] = None

    def start(self, fade_type: str = "out", on_complete: Optional[Callable[[], None]] = None) -> None:
        self.is_active = True
        self.fade_type = fade_type
        self.timer = 0.0
        self.on_complete = on_complete

    def update(self, dt: float) -> None:
        if not self.is_active:
            return
        self.timer += dt
        if self.timer >= self.duration:
            self.is_active = False
            if self.on_complete:
                cb = self.on_complete
                self.on_complete = None
                cb()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_active:
            return
        progress = min(1.0, self.timer / self.duration)
        if self.fade_type == "out":
            alpha = int(255 * progress)
        else:
            alpha = int(255 * (1.0 - progress))

        w, h = surface.get_size()
        fade_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        fade_surf.fill((10, 18, 28, alpha))
        surface.blit(fade_surf, (0, 0))


class ToastItem:
    def __init__(self, text: str, color: Tuple[int, int, int], duration: float = 2.2):
        self.text = text
        self.color = color
        self.duration = duration
        self.time_alive: float = 0.0
        self.y_offset: float = 0.0

    @property
    def is_alive(self) -> bool:
        return self.time_alive < self.duration

    @property
    def alpha(self) -> int:
        if self.time_alive < 0.25:
            return int(255 * (self.time_alive / 0.25))
        elif self.time_alive > self.duration - 0.4:
            remain = self.duration - self.time_alive
            return max(0, int(255 * (remain / 0.4)))
        return 255


class ToastManager:
    """Floating transaction and status popups."""

    def __init__(self):
        self.toasts: List[ToastItem] = []
        self.transactions: List[FloatingTransaction] = []
        self.effects: List[ConstructionEffect] = []

    def add(self, text: str, color: Tuple[int, int, int] = (248, 245, 238)) -> None:
        if self.toasts and self.toasts[-1].text == text and self.toasts[-1].time_alive < 0.5:
            return
        self.toasts.append(ToastItem(text, color))
        if len(self.toasts) > 5:
            self.toasts.pop(0)

    def add_transaction(self, text: str, x: int, y: int, color: Tuple[int, int, int], amount: int) -> None:
        self.transactions.append(FloatingTransaction(text, x, y, color, amount))

    def add_construction(self, center: Tuple[int, int], is_hotel: bool = False) -> None:
        self.effects.append(ConstructionEffect(center, is_hotel))

    def update(self, dt: float) -> None:
        for t in self.toasts:
            t.time_alive += dt
            t.y_offset += dt * 14
        self.toasts = [t for t in self.toasts if t.is_alive]

        for tx in self.transactions:
            tx.update(dt)
        self.transactions = [tx for tx in self.transactions if tx.is_alive]

        for ef in self.effects:
            ef.update(dt)
        self.effects = [ef for ef in self.effects if ef.is_alive]

    def draw(self, surface: pygame.Surface, base_x: int, base_y: int, font: pygame.font.Font) -> None:
        # Draw construction effects
        for ef in self.effects:
            ef.draw(surface)

        # Draw floating transaction coins and badges
        for tx in self.transactions:
            tx.draw(surface, font)

        # Draw toasts
        cur_y = base_y
        for t in reversed(self.toasts):
            alpha = t.alpha
            txt_surf = font.render(t.text, True, t.color)
            padding_x, padding_y = 14, 6
            bg_rect = pygame.Rect(
                base_x - (txt_surf.get_width() // 2) - padding_x,
                int(cur_y - t.y_offset) - padding_y,
                txt_surf.get_width() + (padding_x * 2),
                txt_surf.get_height() + (padding_y * 2)
            )

            pill_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pill_surf.fill((20, 32, 43, min(230, alpha)))
            pygame.draw.rect(pill_surf, (232, 184, 109, min(200, alpha)), (0, 0, bg_rect.width, bg_rect.height), width=1, border_radius=12)

            txt_surf.set_alpha(alpha)
            pill_surf.blit(txt_surf, (padding_x, padding_y))
            surface.blit(pill_surf, bg_rect.topleft)
            cur_y -= bg_rect.height + 6
