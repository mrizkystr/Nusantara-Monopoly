"""
Reusable Pygame UI components: 2.5D Buttons, Panels, and LogBox.
Designed with modern casual-game visual depth, drop shadows, and bevel highlights.
"""
import pygame
from typing import Optional, Tuple, Callable, List

pygame.font.init()
_FONT_CACHE = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Retrieve or cache a Pygame font instance."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        try:
            font = pygame.font.SysFont("dejavusans,segoeui,arial,helvetica", size, bold=bold)
        except Exception:
            font = pygame.font.Font(None, size)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]


class Button:
    """2.5D push button with bevel, drop shadow, hover glow, and press depth."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        bg_color: Tuple[int, int, int] = (41, 128, 185),
        hover_color: Tuple[int, int, int] = (52, 152, 219),
        text_color: Tuple[int, int, int] = (255, 255, 255),
        disabled_color: Tuple[int, int, int] = (70, 75, 85),
        font_size: int = 16,
        border_radius: int = 8,
        is_enabled: bool = True
    ):
        self.rect = rect
        self.text = text
        self.on_click = on_click
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.disabled_color = disabled_color
        self.font_size = font_size
        self.border_radius = border_radius
        self.is_enabled = is_enabled
        self.is_hovered = False
        self.is_pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_enabled:
            self.is_hovered = False
            self.is_pressed = False
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_hovered = True
                self.is_pressed = True
                if self.on_click:
                    self.on_click()
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_pressed = False
        return False

    def draw(self, surface: pygame.Surface) -> None:
        draw_rect = self.rect.copy()
        is_pushed = self.is_pressed or (self.is_enabled and self.is_hovered and pygame.mouse.get_pressed()[0])
        if is_pushed and self.is_enabled:
            draw_rect.y += 2  # Physical push down

        # Guard against zero or negative dimensions
        if draw_rect.width <= 0 or draw_rect.height <= 0:
            return

        # 1. Drop Shadow (under button)
        if self.is_enabled and not is_pushed:
            shadow_surf = pygame.Surface((draw_rect.width + 4, draw_rect.height + 4), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 70), (0, 0, draw_rect.width + 4, draw_rect.height + 4), border_radius=self.border_radius + 2)
            surface.blit(shadow_surf, (draw_rect.x, draw_rect.y + 3))

        # Base color
        base_col = self.bg_color
        if not self.is_enabled:
            base_col = self.disabled_color
        elif self.is_hovered:
            base_col = self.hover_color

        # 2. Main button body
        pygame.draw.rect(surface, base_col, draw_rect, border_radius=self.border_radius)

        # 3. 2.5D Top bevel highlight
        if self.is_enabled:
            light_col = (
                min(255, base_col[0] + 50),
                min(255, base_col[1] + 50),
                min(255, base_col[2] + 50)
            )
            top_bevel = pygame.Rect(draw_rect.x + 2, draw_rect.y + 2, draw_rect.width - 4, max(3, draw_rect.height // 4))
            pygame.draw.rect(surface, light_col, top_bevel, border_radius=max(2, self.border_radius - 2))

            # Bottom shadow strip
            dark_col = (
                max(0, base_col[0] - 45),
                max(0, base_col[1] - 45),
                max(0, base_col[2] - 45)
            )
            bottom_bevel = pygame.Rect(draw_rect.x + 2, draw_rect.bottom - 4, draw_rect.width - 4, 3)
            pygame.draw.rect(surface, dark_col, bottom_bevel, border_radius=max(1, self.border_radius - 3))

        # 4. Outer border
        bdr_col = (255, 255, 255, 90) if self.is_hovered and self.is_enabled else (30, 40, 50, 100)
        pygame.draw.rect(surface, (230, 235, 245) if self.is_hovered and self.is_enabled else (80, 95, 110), draw_rect, width=1, border_radius=self.border_radius)

        # 5. Text with shadow for readability
        font = get_font(self.font_size, bold=True)
        txt_col = self.text_color if self.is_enabled else (150, 155, 165)

        # Text drop shadow
        shadow_surf = font.render(self.text, True, (20, 25, 30))
        surface.blit(shadow_surf, shadow_surf.get_rect(center=(draw_rect.centerx + 1, draw_rect.centery + 1)))

        txt_surf = font.render(self.text, True, txt_col)
        surface.blit(txt_surf, txt_surf.get_rect(center=draw_rect.center))


class Panel:
    def __init__(
        self,
        rect: pygame.Rect,
        bg_color: Tuple[int, int, int] = (25, 30, 40),
        border_color: Tuple[int, int, int] = (60, 70, 90),
        border_width: int = 1,
        border_radius: int = 10
    ):
        self.rect = rect
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

    def draw(self, surface: pygame.Surface) -> None:
        # Shadow
        shadow_surf = pygame.Surface((self.rect.width + 6, self.rect.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 75), (0, 0, self.rect.width + 6, self.rect.height + 6), border_radius=self.border_radius + 2)
        surface.blit(shadow_surf, (self.rect.x, self.rect.y + 3))

        # Body
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, self.rect, width=self.border_width, border_radius=self.border_radius)


class LogBox:
    """Displays a scrollable view of recent game events."""

    def __init__(self, rect: pygame.Rect, font_size: int = 13):
        self.rect = rect
        self.font_size = font_size
        self.scroll_offset = 0

    def draw(self, surface: pygame.Surface, messages: List[str]) -> None:
        # Background panel
        pygame.draw.rect(surface, (14, 24, 32), self.rect, border_radius=8)
        pygame.draw.rect(surface, (45, 65, 80), self.rect, width=1, border_radius=8)

        font = get_font(self.font_size)
        line_height = self.font_size + 6
        visible_lines = max(1, (self.rect.height - 12) // line_height)

        recent = messages[-visible_lines:]
        y = self.rect.y + 6
        for msg in recent:
            color = (220, 225, 235)
            if "menerima" in msg.lower() or "bebas" in msg.lower() or "selamat" in msg.lower():
                color = (72, 195, 130)
            elif "bangkrut" in msg.lower() or "penjara" in msg.lower() or "utang" in msg.lower() or "denda" in msg.lower():
                color = (235, 85, 85)
            elif "membeli" in msg.lower() or "lelang" in msg.lower() or "membangun" in msg.lower():
                color = (245, 205, 55)

            # Truncate if exceeds width
            txt_surf = font.render(msg, True, color)
            if txt_surf.get_width() > self.rect.width - 16:
                ellipsis = "..."
                while len(msg) > 5 and font.size(msg + ellipsis)[0] > self.rect.width - 20:
                    msg = msg[:-2]
                txt_surf = font.render(msg + ellipsis, True, color)

            surface.blit(txt_surf, (self.rect.x + 8, y))
            y += line_height
