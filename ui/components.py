"""Reusable Pygame UI components: Buttons, Panels, Labels, and Modals."""
import pygame
from typing import Optional, Tuple, Callable, List

# Initialize font module safely
pygame.font.init()

_FONT_CACHE = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Retrieve or cache a Pygame font instance."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        # Use clean default system fonts
        try:
            font = pygame.font.SysFont("dejavusans,segoeui,arial", size, bold=bold)
        except Exception:
            font = pygame.font.Font(None, size)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        bg_color: Tuple[int, int, int] = (41, 128, 185),
        hover_color: Tuple[int, int, int] = (52, 152, 219),
        text_color: Tuple[int, int, int] = (255, 255, 255),
        disabled_color: Tuple[int, int, int] = (100, 100, 100),
        font_size: int = 18,
        border_radius: int = 6,
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

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse movement and click events."""
        if not self.is_enabled:
            self.is_hovered = False
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button on the given surface."""
        color = self.bg_color
        if not self.is_enabled:
            color = self.disabled_color
        elif self.is_hovered:
            color = self.hover_color

        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        # Highlight border
        border_col = (255, 255, 255, 60) if self.is_hovered and self.is_enabled else (30, 30, 30, 120)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, width=1, border_radius=self.border_radius)

        font = get_font(self.font_size, bold=True)
        txt_surf = font.render(self.text, True, self.text_color if self.is_enabled else (180, 180, 180))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)


class Panel:
    def __init__(
        self,
        rect: pygame.Rect,
        bg_color: Tuple[int, int, int] = (25, 30, 40),
        border_color: Tuple[int, int, int] = (60, 70, 90),
        border_width: int = 1,
        border_radius: int = 8
    ):
        self.rect = rect
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, self.rect, width=self.border_width, border_radius=self.border_radius)


class LogBox:
    """Displays a scrollable view of recent game events."""

    def __init__(self, rect: pygame.Rect, font_size: int = 14):
        self.rect = rect
        self.font_size = font_size
        self.scroll_offset = 0

    def draw(self, surface: pygame.Surface, messages: List[str]) -> None:
        # Draw background panel
        pygame.draw.rect(surface, (18, 22, 30), self.rect, border_radius=6)
        pygame.draw.rect(surface, (50, 60, 75), self.rect, width=1, border_radius=6)

        font = get_font(self.font_size)
        line_height = self.font_size + 6
        visible_lines = max(1, (self.rect.height - 12) // line_height)

        # Show the most recent lines
        recent = messages[-visible_lines:]
        y = self.rect.y + 8
        for msg in recent:
            color = (220, 225, 235)
            if "menerima" in msg.lower() or "bebas" in msg.lower() or "selamat" in msg.lower():
                color = (46, 204, 113)
            elif "bangkrut" in msg.lower() or "penjara" in msg.lower() or "utang" in msg.lower() or "denda" in msg.lower():
                color = (231, 76, 60)
            elif "membeli" in msg.lower() or "lelang" in msg.lower() or "membangun" in msg.lower():
                color = (241, 196, 15)

            # Truncate text if exceeds log width
            txt_surf = font.render(msg, True, color)
            if txt_surf.get_width() > self.rect.width - 16:
                # Truncate with ellipsis
                ellipsis = "..."
                while len(msg) > 5 and font.size(msg + ellipsis)[0] > self.rect.width - 20:
                    msg = msg[:-2]
                txt_surf = font.render(msg + ellipsis, True, color)

            surface.blit(txt_surf, (self.rect.x + 8, y))
            y += line_height
