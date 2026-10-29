"""Animation systems for Dice rolling, Token movement, Card reveals, and Toast notifications."""
import random
import pygame
from typing import List, Tuple, Optional, Callable, Dict, Any
from ui.audio import AudioManager


class DiceAnimation:
    """Non-blocking delta-time based dice rolling animation."""

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

    def start(self, target1: int, target2: int, speed: str = "Normal", on_complete: Optional[Callable[[], None]] = None) -> None:
        if speed == "Instant":
            self.face1 = target1
            self.face2 = target2
            self.target1 = target1
            self.target2 = target2
            self.is_active = False
            AudioManager.get_instance().play_sfx("dice_land")
            if on_complete:
                on_complete()
            return

        self.current_duration = 0.45 if speed == "Fast" else self.default_duration
        self.time_elapsed = 0.0
        self.is_active = True
        self.target1 = target1
        self.target2 = target2
        self.face1 = random.randint(1, 6)
        self.face2 = random.randint(1, 6)
        self.on_complete = on_complete
        self._last_face_swap = 0.0

        AudioManager.get_instance().play_sfx("dice_roll")

    def update(self, dt: float) -> None:
        if not self.is_active:
            return

        self.time_elapsed += dt
        self._last_face_swap += dt

        # Randomize faces during roll
        if self._last_face_swap >= 0.07:
            self._last_face_swap = 0.0
            self.face1 = random.randint(1, 6)
            self.face2 = random.randint(1, 6)

        # Finished rolling
        if self.time_elapsed >= self.current_duration:
            self.is_active = False
            self.face1 = self.target1
            self.face2 = self.target2
            AudioManager.get_instance().play_sfx("dice_land")
            if self.on_complete:
                cb = self.on_complete
                self.on_complete = None
                cb()


class MovementAnimation:
    """Step-by-step tile movement animation around the board."""

    def __init__(self, step_duration: float = 0.14):
        self.default_step_duration = step_duration
        self.current_step_duration = step_duration
        self.is_active: bool = False
        self.path: List[int] = []
        self.current_step_idx: int = 0
        self.step_timer: float = 0.0
        self.current_tile: int = 0
        self.target_tile: int = 0
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
            if on_complete:
                on_complete()
            return

        self.current_step_duration = 0.08 if speed == "Fast" else self.default_step_duration
        self.is_active = True
        self.path = list(path)
        self.current_step_idx = 0
        self.step_timer = 0.0
        self.current_tile = start_tile
        self.target_tile = target_tile
        self.on_step = on_step
        self.on_complete = on_complete

    def skip(self) -> None:
        """Immediately complete movement animation."""
        if not self.is_active:
            return
        self.is_active = False
        self.current_tile = self.target_tile
        if self.on_complete:
            cb = self.on_complete
            self.on_complete = None
            cb()

    def update(self, dt: float) -> None:
        if not self.is_active:
            return

        self.step_timer += dt
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
                if self.on_complete:
                    cb = self.on_complete
                    self.on_complete = None
                    cb()

    @property
    def remaining_steps(self) -> int:
        if not self.is_active:
            return 0
        return max(0, len(self.path) - self.current_step_idx)


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
        # Fade in 0.3s, stay, fade out last 0.5s
        if self.time_alive < 0.3:
            return int(255 * (self.time_alive / 0.3))
        elif self.time_alive > self.duration - 0.5:
            remain = self.duration - self.time_alive
            return max(0, int(255 * (remain / 0.5)))
        return 255


class ToastManager:
    """Floating transaction and status popups."""

    def __init__(self):
        self.toasts: List[ToastItem] = []

    def add(self, text: str, color: Tuple[int, int, int] = (248, 245, 238)) -> None:
        # Avoid duplicate consecutive toasts
        if self.toasts and self.toasts[-1].text == text and self.toasts[-1].time_alive < 0.5:
            return
        self.toasts.append(ToastItem(text, color))
        if len(self.toasts) > 5:
            self.toasts.pop(0)

    def update(self, dt: float) -> None:
        for t in self.toasts:
            t.time_alive += dt
            t.y_offset += dt * 14  # Gentle drift upwards
        self.toasts = [t for t in self.toasts if t.is_alive]

    def draw(self, surface: pygame.Surface, base_x: int, base_y: int, font: pygame.font.Font) -> None:
        cur_y = base_y
        for t in reversed(self.toasts):
            alpha = t.alpha
            txt_surf = font.render(t.text, True, t.color)

            # Container pill background with alpha
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
