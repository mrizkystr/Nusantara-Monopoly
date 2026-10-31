"""
Visual Assets — Procedural 2.5D art generation for Nusantara Property Tycoon.
Generates backgrounds, building sprites, board decorations, and environmental art.
All surfaces are cached for performance.
"""
import math
import random
import pygame
from typing import Dict, Tuple, Optional, List

# =============================================================================
# COLOUR PALETTE — Warm Tropical Indonesian Theme
# =============================================================================
C_BG             = (15, 25, 38)       # Deep ocean night
C_BG_WARM        = (22, 35, 28)       # Tropical night forest
C_BOARD_BG       = (28, 100, 60)      # Lush green felt
C_BOARD_FELT     = (32, 110, 65)      # Board surface
C_BOARD_BORDER   = (160, 120, 55)     # Wooden border gold
C_BOARD_INNER    = (240, 220, 160)    # Parchment center
C_TILE_LIGHT     = (252, 248, 238)    # Cream tile
C_TILE_SHADOW    = (180, 165, 140)    # Tile bottom-edge shadow
C_TILE_BORDER    = (140, 120, 90)     # Tile border warm
C_CORNER_BG      = (255, 252, 235)    # Corner tile cream
C_GOLD           = (232, 184, 80)     # Indonesian gold
C_GOLD_LIGHT     = (255, 215, 100)    # Bright gold
C_TEAL           = (72, 175, 148)     # Batik teal
C_RED            = (210, 60, 55)      # Flag red
C_TEXT_DARK      = (30, 25, 20)       # Very dark text
C_TEXT_MED       = (75, 60, 45)       # Medium text
C_TEXT_LIGHT     = (250, 245, 235)    # Light text
C_SUCCESS        = (72, 185, 120)     # Money green
C_DANGER         = (210, 70, 65)      # Danger red
C_SURFACE        = (28, 45, 60)       # Dark surface
C_SURFACE_MED    = (38, 60, 78)       # Medium surface
C_SURFACE_LIGHT  = (52, 80, 100)      # Light surface

# Property group accent colors (rich, tropical-inspired)
GROUP_COLORS_RICH: Dict = {
    "brown":      (120, 75, 35),
    "light_blue": (80, 185, 220),
    "pink":       (225, 100, 155),
    "orange":     (240, 135, 40),
    "red":        (215, 50, 50),
    "yellow":     (240, 205, 30),
    "green":      (55, 165, 75),
    "dark_blue":  (35, 75, 185),
}

GROUP_NAMES: Dict = {
    "brown":      "Bogor",
    "light_blue": "Depok",
    "pink":       "Bandung",
    "orange":     "Semarang",
    "red":        "Surabaya",
    "yellow":     "Bali",
    "green":      "Kalimantan",
    "dark_blue":  "Jakarta",
}

# =============================================================================
# SURFACE CACHE
# =============================================================================
_surf_cache: Dict = {}


def _cache_key(*args) -> str:
    return str(args)


# =============================================================================
# DRAWING HELPERS
# =============================================================================
def draw_rounded_rect_with_shadow(
    surf: pygame.Surface,
    rect: pygame.Rect,
    color: Tuple,
    radius: int = 8,
    shadow_offset: int = 3,
    shadow_color: Tuple = (0, 0, 0, 80),
    border_color: Optional[Tuple] = None,
    border_width: int = 1
) -> None:
    """Draw a rounded rect with a soft drop shadow."""
    # Shadow
    shadow_surf = pygame.Surface((rect.width + shadow_offset * 2, rect.height + shadow_offset * 2), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, shadow_color,
                     (0, 0, rect.width + shadow_offset * 2, rect.height + shadow_offset * 2),
                     border_radius=radius + 2)
    surf.blit(shadow_surf, (rect.x - shadow_offset + shadow_offset, rect.y - shadow_offset + shadow_offset))

    # Main rect
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surf, border_color, rect, width=border_width, border_radius=radius)


def draw_bevel_rect(
    surf: pygame.Surface,
    rect: pygame.Rect,
    base_color: Tuple,
    bevel: int = 3,
    radius: int = 4
) -> None:
    """Draw a beveled rectangle — lighter top-left, darker bottom-right."""
    r, g, b = base_color[0], base_color[1], base_color[2]
    light = (min(255, r + 45), min(255, g + 40), min(255, b + 30))
    dark  = (max(0, r - 35),   max(0, g - 30),   max(0, b - 25))
    # Base
    pygame.draw.rect(surf, base_color, rect, border_radius=radius)
    # Top highlight
    pygame.draw.rect(surf, light, pygame.Rect(rect.x, rect.y, rect.width, bevel), border_radius=radius)
    # Bottom shadow
    pygame.draw.rect(surf, dark, pygame.Rect(rect.x, rect.bottom - bevel, rect.width, bevel), border_radius=radius)
    # Left highlight
    pygame.draw.rect(surf, light, pygame.Rect(rect.x, rect.y, bevel, rect.height), border_radius=radius)
    # Right shadow
    pygame.draw.rect(surf, dark, pygame.Rect(rect.right - bevel, rect.y, bevel, rect.height), border_radius=radius)


def lerp_color(c1: Tuple, c2: Tuple, t: float) -> Tuple:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# =============================================================================
# BACKGROUND GENERATORS
# =============================================================================
def make_menu_background(w: int, h: int) -> pygame.Surface:
    """Generate a rich Indonesian tropical night cityscape background."""
    key = _cache_key("menu_bg", w, h)
    if key in _surf_cache:
        return _surf_cache[key]

    surf = pygame.Surface((w, h))
    rng = random.Random(42)  # deterministic

    # Sky gradient — deep blue to warm purple/gold horizon
    for y in range(h):
        t = y / h
        if t < 0.6:
            col = lerp_color((10, 18, 45), (30, 55, 90), t / 0.6)
        else:
            col = lerp_color((30, 55, 90), (60, 40, 25), (t - 0.6) / 0.4)
        pygame.draw.line(surf, col, (0, y), (w, y))

    # Stars
    for _ in range(180):
        sx = rng.randint(0, w)
        sy = rng.randint(0, int(h * 0.55))
        bright = rng.randint(150, 255)
        r = rng.choice([1, 1, 1, 2])
        pygame.draw.circle(surf, (bright, bright, bright * 9 // 10), (sx, sy), r)

    # Distant city silhouette (dark layer)
    _draw_city_silhouette(surf, w, h, rng, int(h * 0.62), (15, 28, 45))
    # Closer city silhouette (slightly lighter)
    _draw_city_silhouette(surf, w, h, rng, int(h * 0.72), (22, 40, 60), scale=0.7)

    # Ground / water reflection
    ground_rect = pygame.Rect(0, int(h * 0.78), w, h)
    pygame.draw.rect(surf, (18, 32, 25), ground_rect)

    # Monas silhouette center
    _draw_monas_bg(surf, w // 2, int(h * 0.72), int(h * 0.22))

    # Palm trees
    for i in range(6):
        px = int(w * (0.05 + i * 0.17)) + rng.randint(-20, 20)
        py = int(h * 0.78)
        _draw_palm_tree(surf, px, py, rng.randint(55, 85))

    # Batik border strips at top and bottom
    _draw_batik_strip(surf, pygame.Rect(0, 0, w, 8))
    _draw_batik_strip(surf, pygame.Rect(0, h - 8, w, 8))

    # Warm glow at horizon
    glow_surf = pygame.Surface((w, int(h * 0.2)), pygame.SRCALPHA)
    for gy in range(glow_surf.get_height()):
        alpha = int(60 * (1 - gy / glow_surf.get_height()))
        pygame.draw.line(glow_surf, (200, 140, 60, alpha), (0, gy), (w, gy))
    surf.blit(glow_surf, (0, int(h * 0.65)))

    _surf_cache[key] = surf
    return surf


def _draw_city_silhouette(surf, w, h, rng, base_y, color, scale=1.0):
    """Draw a simple city building silhouette."""
    x = 0
    while x < w:
        bw = rng.randint(int(25 * scale), int(65 * scale))
        bh = rng.randint(int(30 * scale), int(110 * scale))
        # building
        pygame.draw.rect(surf, color, (x, base_y - bh, bw, bh + 10))
        # window rows
        wc = (max(0, color[0] + 15), max(0, color[1] + 12), min(255, color[2] + 18))
        for wy in range(base_y - bh + 4, base_y - 4, int(10 * scale)):
            for wx in range(x + 3, x + bw - 3, int(9 * scale)):
                if rng.random() > 0.5:
                    pygame.draw.rect(surf, wc, (wx, wy, int(4 * scale), int(5 * scale)))
        x += bw + rng.randint(2, 8)


def _draw_monas_bg(surf, cx, base_y, height):
    """Draw a stylized Monas silhouette."""
    color = (35, 55, 45)
    gold = (160, 120, 40)
    # Base platform
    pw = height // 2
    ph = height // 10
    pygame.draw.rect(surf, color, (cx - pw // 2, base_y - ph, pw, ph))
    # Obelisk body
    pts = [
        (cx - height // 14, base_y - ph),
        (cx + height // 14, base_y - ph),
        (cx + height // 22, base_y - int(height * 0.82)),
        (cx - height // 22, base_y - int(height * 0.82))
    ]
    pygame.draw.polygon(surf, color, pts)
    # Golden flame
    flame = [
        (cx, base_y - height),
        (cx + height // 12, base_y - int(height * 0.82)),
        (cx - height // 12, base_y - int(height * 0.82))
    ]
    pygame.draw.polygon(surf, gold, flame)


def _draw_palm_tree(surf, cx, base_y, height):
    """Draw a simple stylized palm tree."""
    trunk_color = (55, 40, 22)
    leaf_color  = (30, 90, 45)
    # Trunk (slightly curved)
    for i in range(height):
        t = i / height
        x_off = int(8 * math.sin(t * math.pi * 1.5))
        pygame.draw.circle(surf, trunk_color, (cx + x_off, base_y - i), max(2, int(4 * (1 - t * 0.6))))

    # Palm fronds
    top_x = cx + int(8 * math.sin(math.pi * 1.5))
    top_y = base_y - height
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        fx = int(math.cos(rad) * height * 0.45)
        fy = int(math.sin(rad) * height * 0.25)
        # Draw frond as thick line
        pygame.draw.line(surf, leaf_color, (top_x, top_y), (top_x + fx, top_y + fy), 3)
        # Leaf tip accent
        pygame.draw.circle(surf, (40, 110, 55), (top_x + fx, top_y + fy), 4)


def _draw_batik_strip(surf, rect):
    """Draw a repeating batik geometric strip."""
    color_base = (140, 100, 40)
    color_acc  = (200, 150, 60)
    pygame.draw.rect(surf, color_base, rect)
    step = rect.height
    for xi in range(rect.x, rect.right, step * 2):
        mid_y = rect.y + rect.height // 2
        pygame.draw.polygon(surf, color_acc, [
            (xi + step // 2, rect.y),
            (xi + step, mid_y),
            (xi + step // 2, rect.bottom),
            (xi, mid_y)
        ])


def make_game_background(w: int, h: int) -> pygame.Surface:
    """Dark felt-like table surface for the game screen background."""
    key = _cache_key("game_bg", w, h)
    if key in _surf_cache:
        return _surf_cache[key]

    surf = pygame.Surface((w, h))

    # Dark green baize / felt table
    for y in range(h):
        t = y / h
        col = lerp_color((18, 48, 32), (12, 35, 22), t)
        pygame.draw.line(surf, col, (0, y), (w, y))

    # Subtle felt texture (random noise)
    rng = random.Random(7)
    for _ in range(w * h // 30):
        fx = rng.randint(0, w - 1)
        fy = rng.randint(0, h - 1)
        bright = rng.randint(2, 8)
        c = surf.get_at((fx, fy))
        nc = (min(255, c[0] + bright), min(255, c[1] + bright), min(255, c[2] + bright))
        surf.set_at((fx, fy), nc)

    _surf_cache[key] = surf
    return surf


# =============================================================================
# BOARD SURFACE — 2.5D LAYERED BOARD
# =============================================================================
def make_board_frame(size: int) -> pygame.Surface:
    """
    Generate the outer wooden frame/border of the board.
    Returns a surface of (size x size) with a decorative wooden border.
    """
    key = _cache_key("board_frame", size)
    if key in _surf_cache:
        return _surf_cache[key]

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    border = int(size * 0.022)

    # Outer wooden border — golden brown gradient
    for i in range(border):
        t = i / border
        col = lerp_color((90, 60, 20), (160, 120, 55), t)
        alpha = 255
        rect = pygame.Rect(i, i, size - 2 * i, size - 2 * i)
        pygame.draw.rect(surf, (*col, alpha), rect, width=1, border_radius=max(2, 12 - i // 2))

    # Inner green felt
    inner = pygame.Rect(border, border, size - 2 * border, size - 2 * border)
    pygame.draw.rect(surf, (32, 110, 65), inner, border_radius=8)

    # Decorative corner motifs
    motif_size = int(size * 0.045)
    corners = [
        (border + 4, border + 4),
        (size - border - motif_size - 4, border + 4),
        (border + 4, size - border - motif_size - 4),
        (size - border - motif_size - 4, size - border - motif_size - 4),
    ]
    for cx, cy in corners:
        _draw_batik_corner_motif(surf, cx, cy, motif_size)

    _surf_cache[key] = surf
    return surf


def _draw_batik_corner_motif(surf, x, y, size):
    """Small decorative batik diamond motif for board corners."""
    gold = (200, 155, 55, 200)
    cx, cy = x + size // 2, y + size // 2
    # Diamond
    pygame.draw.polygon(surf, gold, [
        (cx, y),
        (x + size, cy),
        (cx, y + size),
        (x, cy)
    ])
    pygame.draw.polygon(surf, (255, 215, 90, 180), [
        (cx, y + size // 4),
        (x + size * 3 // 4, cy),
        (cx, y + size * 3 // 4),
        (x + size // 4, cy)
    ])


# =============================================================================
# BUILDING SPRITES — 2.5D House / Hotel
# =============================================================================
def draw_house_sprite(surf: pygame.Surface, cx: int, cy: int, size: int, color: Tuple) -> None:
    """Draw a 2.5D house sprite centered at (cx, cy)."""
    r, g, b = color
    # Shadow
    shadow_pts = [
        (cx - size, cy + size // 2 + 3),
        (cx + size, cy + size // 2 + 3),
        (cx + size - 2, cy + size // 2 + 6),
        (cx - size + 2, cy + size // 2 + 6),
    ]
    shadow_surf = pygame.Surface((size * 2 + 4, 8), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 0))
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, size * 2 + 4, 8))
    surf.blit(shadow_surf, (cx - size - 2, cy + size // 2))

    # House walls
    wall_rect = pygame.Rect(cx - size + 2, cy, size * 2 - 4, size // 2 + 2)
    wall_color = (min(255, r + 20), min(255, g + 18), min(255, b + 15))
    pygame.draw.rect(surf, wall_color, wall_rect, border_radius=1)
    # Wall shading (right side darker)
    shade_rect = pygame.Rect(cx, cy, size - 2, size // 2 + 2)
    dark_wall = (max(0, r - 30), max(0, g - 25), max(0, b - 20))
    pygame.draw.rect(surf, dark_wall, shade_rect, border_radius=1)

    # Roof (triangle)
    roof_pts = [
        (cx - size, cy),
        (cx + size, cy),
        (cx, cy - size * 2 // 3)
    ]
    roof_color = (max(0, r - 15), max(0, g - 12), max(0, b - 10))
    pygame.draw.polygon(surf, roof_color, roof_pts)
    # Roof highlight edge
    light_roof = (min(255, r + 30), min(255, g + 28), min(255, b + 25))
    pygame.draw.line(surf, light_roof, roof_pts[0], roof_pts[2], 1)

    # Door
    door_w, door_h = max(3, size // 4), max(4, size // 3)
    door_rect = pygame.Rect(cx - door_w // 2, cy + size // 2 + 2 - door_h, door_w, door_h)
    pygame.draw.rect(surf, (80, 50, 25), door_rect, border_radius=1)

    # Window
    win_size = max(2, size // 5)
    win_rect = pygame.Rect(cx - size + size // 3, cy + size // 8, win_size, win_size)
    pygame.draw.rect(surf, (200, 230, 255), win_rect, border_radius=1)


def draw_hotel_sprite(surf: pygame.Surface, cx: int, cy: int, size: int) -> None:
    """Draw a 2.5D hotel building sprite."""
    color = (185, 45, 45)  # Rich red hotel
    light = (220, 80, 80)
    dark  = (140, 25, 25)

    # Shadow
    shadow_surf = pygame.Surface((size * 3, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 55), (0, 0, size * 3, 10))
    surf.blit(shadow_surf, (cx - size * 3 // 2, cy + size // 2))

    # Main building block
    main_rect = pygame.Rect(cx - size, cy - size // 3, size * 2, size)
    pygame.draw.rect(surf, color, main_rect, border_radius=2)
    # Right-side shade
    shade = pygame.Rect(cx, cy - size // 3, size, size)
    pygame.draw.rect(surf, dark, shade, border_radius=2)
    # Top edge highlight
    pygame.draw.rect(surf, light, pygame.Rect(cx - size, cy - size // 3, size * 2, 3), border_radius=2)

    # Tower / upper floor
    tower_rect = pygame.Rect(cx - size // 2, cy - size * 2 // 3, size, size // 3)
    pygame.draw.rect(surf, color, tower_rect, border_radius=2)
    pygame.draw.rect(surf, light, pygame.Rect(cx - size // 2, cy - size * 2 // 3, size, 2), border_radius=2)

    # Roof
    pygame.draw.rect(surf, (140, 100, 40), pygame.Rect(cx - size // 2 - 2, cy - size * 2 // 3 - 4, size + 4, 5), border_radius=1)

    # Windows (2 rows)
    for row in range(2):
        wy = cy - size // 4 + row * (size // 3)
        for col in range(3):
            wx = cx - size + size // 2 + col * (size // 2) - size // 6
            win_r = pygame.Rect(wx, wy, max(3, size // 6), max(4, size // 5))
            pygame.draw.rect(surf, (200, 230, 255), win_r, border_radius=1)

    # "H" sign on building
    from ui.components import get_font
    try:
        f = get_font(max(8, size // 3), bold=True)
        h_surf = f.render("H", True, (255, 240, 180))
        surf.blit(h_surf, h_surf.get_rect(center=(cx, cy)))
    except Exception:
        pass


# =============================================================================
# TILE DECORATIONS — Regional art per color group
# =============================================================================
def draw_region_deco(surf: pygame.Surface, rect: pygame.Rect, group_key: str, side: str) -> None:
    """
    Draw a small cultural/architectural decoration on a tile
    based on its property color group and which edge it's on.
    side: 'top', 'bottom', 'left', 'right'
    """
    fn_map = {
        "brown":      _deco_bogor,
        "light_blue": _deco_depok,
        "pink":       _deco_bandung,
        "orange":     _deco_semarang,
        "red":        _deco_surabaya,
        "yellow":     _deco_bali,
        "green":      _deco_kalimantan,
        "dark_blue":  _deco_jakarta,
    }
    fn = fn_map.get(group_key)
    if fn:
        try:
            fn(surf, rect, side)
        except Exception:
            pass


def _get_deco_center(rect: pygame.Rect, side: str) -> Tuple[int, int]:
    """Get center point of the deco area based on which edge the tile is on."""
    if side == "top":    return rect.centerx, rect.y + rect.height // 4
    if side == "bottom": return rect.centerx, rect.bottom - rect.height // 4
    if side == "left":   return rect.x + rect.width // 4, rect.centery
    if side == "right":  return rect.right - rect.width // 4, rect.centery
    return rect.centerx, rect.centery


def _deco_bogor(surf, rect, side):
    """Bogor: tropical tree silhouette."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 5
    # Tree trunk
    pygame.draw.rect(surf, (100, 65, 25), (cx - 1, cy, 3, s))
    # Canopy
    pygame.draw.circle(surf, (50, 130, 60, 180), (cx, cy), s, 0)
    pygame.draw.circle(surf, (70, 160, 75, 150), (cx - s // 2, cy), int(s * 0.7), 0)


def _deco_depok(surf, rect, side):
    """Depok: small residential house."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 6
    wall_col = (220, 200, 170)
    roof_col  = (160, 60, 40)
    pygame.draw.rect(surf, wall_col, (cx - s, cy, s * 2, s))
    pygame.draw.polygon(surf, roof_col, [(cx - s - 1, cy), (cx + s + 1, cy), (cx, cy - s)])


def _deco_bandung(surf, rect, side):
    """Bandung: Gedung Sate-inspired dome."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 6
    col = (200, 180, 140)
    # Column base
    pygame.draw.rect(surf, col, (cx - s, cy, s * 2, s))
    # Dome
    pygame.draw.ellipse(surf, col, (cx - s, cy - s, s * 2, s))
    # Spire
    pygame.draw.line(surf, (160, 120, 60), (cx, cy - s), (cx, cy - s * 2), 2)
    pygame.draw.circle(surf, (220, 165, 40), (cx, cy - s * 2), 3)


def _deco_semarang(surf, rect, side):
    """Semarang: Lawang Sewu gate silhouette."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 7
    col = (180, 165, 130)
    # Two towers
    pygame.draw.rect(surf, col, (cx - s * 2, cy, s, s * 2))
    pygame.draw.rect(surf, col, (cx + s, cy, s, s * 2))
    # Arch connecting them
    pygame.draw.arc(surf, col,
                    pygame.Rect(cx - s * 2, cy - s, s * 3, s * 2),
                    0, math.pi, 3)


def _deco_surabaya(surf, rect, side):
    """Surabaya: modern building silhouette."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 7
    col = (140, 180, 210)
    # Two buildings
    pygame.draw.rect(surf, col, (cx - s * 2, cy, s, s * 2))
    pygame.draw.rect(surf, (160, 200, 230), (cx, cy - s // 2, s, s * 2 + s // 2))
    # Windows
    for i in range(3):
        pygame.draw.rect(surf, (255, 240, 180), (cx + 2, cy - s // 2 + i * s // 2 + 2, s - 4, s // 4))


def _deco_bali(surf, rect, side):
    """Bali: Candi Bentar gate silhouette."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 7
    col = (160, 120, 80)
    # Left gate half
    pts_l = [(cx - s * 2, cy + s), (cx - s, cy + s), (cx - s, cy - s),
             (cx - s * 2, cy - s // 2)]
    pygame.draw.polygon(surf, col, pts_l)
    # Right gate half (mirrored)
    pts_r = [(cx + s * 2, cy + s), (cx + s, cy + s), (cx + s, cy - s),
             (cx + s * 2, cy - s // 2)]
    pygame.draw.polygon(surf, col, pts_r)
    # Decorative top carvings
    pygame.draw.line(surf, (200, 165, 110), (cx - s * 2, cy - s // 2), (cx - s, cy - s), 2)
    pygame.draw.line(surf, (200, 165, 110), (cx + s * 2, cy - s // 2), (cx + s, cy - s), 2)


def _deco_kalimantan(surf, rect, side):
    """Kalimantan: river/longhouse motif."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 7
    # Longhouse silhouette
    col = (120, 90, 55)
    pygame.draw.rect(surf, col, (cx - s * 2, cy, s * 4, s))
    # Curved roof
    pygame.draw.arc(surf, (150, 110, 65),
                    pygame.Rect(cx - s * 2, cy - s, s * 4, s * 2),
                    0, math.pi, 3)
    # River wavy line below
    for xi in range(-s * 2, s * 2, 4):
        wave_y = cy + s + int(3 * math.sin(xi * 0.4))
        pygame.draw.circle(surf, (70, 130, 180), (cx + xi, wave_y), 1)


def _deco_jakarta(surf, rect, side):
    """Jakarta: Monas miniature."""
    cx, cy = _get_deco_center(rect, side)
    s = min(rect.width, rect.height) // 7
    col = (180, 175, 160)
    gold = (220, 175, 50)
    # Platform
    pygame.draw.rect(surf, col, (cx - s, cy + s, s * 2, s // 2))
    # Obelisk
    pts = [
        (cx - s // 3, cy + s),
        (cx + s // 3, cy + s),
        (cx + s // 5, cy - s),
        (cx - s // 5, cy - s)
    ]
    pygame.draw.polygon(surf, col, pts)
    # Flame
    pygame.draw.polygon(surf, gold, [(cx, cy - s * 2), (cx + s // 4, cy - s), (cx - s // 4, cy - s)])


# =============================================================================
# CARD ARTWORK — Styled card background surfaces
# =============================================================================
def make_card_surf(w: int, h: int, is_chance: bool) -> pygame.Surface:
    """Generate a styled card background for Kesempatan / Dana Umum."""
    key = _cache_key("card", w, h, is_chance)
    if key in _surf_cache:
        return _surf_cache[key]

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    if is_chance:
        # Kesempatan: warm gold-orange Indonesian scrollwork
        bg_color = (45, 35, 15)
        accent = (210, 160, 55)
        accent2 = (255, 210, 80)
    else:
        # Dana Umum: teal/green community feel
        bg_color = (15, 45, 40)
        accent = (72, 175, 148)
        accent2 = (100, 210, 180)

    # Background
    pygame.draw.rect(surf, bg_color, (0, 0, w, h), border_radius=14)

    # Header band
    pygame.draw.rect(surf, accent, (0, 0, w, h // 5), border_radius=14)
    pygame.draw.rect(surf, accent, (0, h - h // 7, w, h // 7), border_radius=14)

    # Decorative inner border
    inner = pygame.Rect(8, 8, w - 16, h - 16)
    pygame.draw.rect(surf, (*accent2, 100), inner, width=2, border_radius=10)

    # Corner diamonds
    diamond_size = 14
    corners = [(10, 10), (w - 10 - diamond_size, 10),
               (10, h - 10 - diamond_size), (w - 10 - diamond_size, h - 10 - diamond_size)]
    for dcx, dcy in corners:
        cx, cy = dcx + diamond_size // 2, dcy + diamond_size // 2
        pygame.draw.polygon(surf, accent2, [
            (cx, dcy), (dcx + diamond_size, cy), (cx, dcy + diamond_size), (dcx, cy)
        ])

    # Scrollwork pattern (simple repeated arcs along sides)
    for xi in range(0, w, 22):
        pygame.draw.arc(surf, (*accent, 80),
                        pygame.Rect(xi, h // 5 - 4, 20, 12), 0, math.pi, 2)
        pygame.draw.arc(surf, (*accent, 80),
                        pygame.Rect(xi, h - h // 7 - 8, 20, 12), math.pi, 2 * math.pi, 2)

    _surf_cache[key] = surf
    return surf


# =============================================================================
# PLAYER AVATARS — Compact player card background
# =============================================================================
def make_player_card_bg(w: int, h: int, color: Tuple, is_active: bool) -> pygame.Surface:
    """Generate a styled player card background."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    if is_active:
        # Glowing gold border
        bg = (38, 58, 48)
        border = (220, 175, 55)
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*border, 40), (0, 0, w, h), border_radius=10)
        surf.blit(glow, (0, 0))
    else:
        bg = (22, 38, 30)
        border = (55, 85, 70)

    pygame.draw.rect(surf, bg, (0, 0, w, h), border_radius=10)

    # Left color accent bar
    bar_w = 5
    pygame.draw.rect(surf, color, (0, 0, bar_w, h), border_radius=5)

    pygame.draw.rect(surf, border, (0, 0, w, h), width=2 if is_active else 1, border_radius=10)

    return surf


# =============================================================================
# MODAL ARTWORKS & EMBLEMS
# =============================================================================
def draw_property_card_artwork(surf: pygame.Surface, rect: pygame.Rect, group_key: str, tile_name: str) -> None:
    """Draw a framed, rich 2.5D architectural artwork inside the property purchase card."""
    # Frame background (soft sky / parchment)
    pygame.draw.rect(surf, (24, 42, 56), rect, border_radius=10)
    pygame.draw.rect(surf, (70, 110, 140), rect, width=1, border_radius=10)

    cx, cy = rect.centerx, rect.centery
    base_y = rect.bottom - 12
    col_gold = (232, 184, 80)
    col_bld = (180, 205, 220)
    col_roof = (195, 75, 55)

    # Ground strip
    pygame.draw.line(surf, (45, 75, 60), (rect.x + 8, base_y), (rect.right - 8, base_y), 3)

    if group_key == "brown":  # Bogor: Palace & trees
        # Palace building
        pygame.draw.rect(surf, (230, 235, 245), (cx - 45, base_y - 32, 90, 32), border_radius=2)
        pygame.draw.polygon(surf, col_roof, [(cx - 50, base_y - 32), (cx + 50, base_y - 32), (cx, base_y - 52)])
        _draw_palm_tree(surf, cx - 65, base_y, 45)
        _draw_palm_tree(surf, cx + 65, base_y, 45)

    elif group_key == "light_blue":  # Depok: Suburban houses
        for ox in (-40, 40):
            pygame.draw.rect(surf, (220, 225, 235), (cx + ox - 24, base_y - 30, 48, 30), border_radius=2)
            pygame.draw.polygon(surf, (70, 140, 180), [(cx + ox - 28, base_y - 30), (cx + ox + 28, base_y - 30), (cx + ox, base_y - 48)])
        pygame.draw.circle(surf, (55, 145, 70), (cx, base_y - 12), 16)

    elif group_key == "pink":  # Bandung: Gedung Sate & mountains
        # Mountain backdrop
        pygame.draw.polygon(surf, (35, 65, 50), [(rect.x + 10, base_y), (cx - 40, base_y - 45), (cx + 60, base_y)])
        pygame.draw.polygon(surf, (45, 80, 60), [(cx - 20, base_y), (cx + 50, base_y - 52), (rect.right - 10, base_y)])
        # Gedung Sate
        pygame.draw.rect(surf, (240, 240, 245), (cx - 40, base_y - 30, 80, 30), border_radius=2)
        pygame.draw.line(surf, col_gold, (cx, base_y - 30), (cx, base_y - 56), 3)
        pygame.draw.circle(surf, col_gold, (cx, base_y - 56), 5)

    elif group_key == "orange":  # Semarang: Lawang Sewu arches
        pygame.draw.rect(surf, (230, 220, 200), (cx - 55, base_y - 38, 110, 38), border_radius=3)
        for i in range(5):
            ax = cx - 44 + i * 22
            pygame.draw.arc(surf, (80, 60, 40), pygame.Rect(ax - 7, base_y - 28, 14, 28), 0, math.pi, 2)
        pygame.draw.polygon(surf, col_roof, [(cx - 60, base_y - 38), (cx + 60, base_y - 38), (cx, base_y - 54)])

    elif group_key == "red":  # Surabaya: Port & Bridge
        # Towers
        pygame.draw.rect(surf, (150, 180, 210), (cx - 50, base_y - 48, 16, 48))
        pygame.draw.rect(surf, (150, 180, 210), (cx + 34, base_y - 48, 16, 48))
        # Cable stay lines
        pygame.draw.line(surf, col_gold, (cx - 42, base_y - 44), (cx, base_y - 10), 2)
        pygame.draw.line(surf, col_gold, (cx + 42, base_y - 44), (cx, base_y - 10), 2)
        pygame.draw.line(surf, (200, 220, 240), (rect.x + 10, base_y - 10), (rect.right - 10, base_y - 10), 3)

    elif group_key == "yellow":  # Bali: Candi Bentar split gate
        gw, gh = 28, 48
        # Left wing
        pts_l = [(cx - 36, base_y), (cx - 6, base_y), (cx - 6, base_y - gh), (cx - 26, base_y - gh + 14), (cx - 36, base_y - gh + 8)]
        pygame.draw.polygon(surf, (190, 140, 85), pts_l)
        # Right wing
        pts_r = [(cx + 6, base_y), (cx + 36, base_y), (cx + 36, base_y - gh + 8), (cx + 26, base_y - gh + 14), (cx + 6, base_y - gh)]
        pygame.draw.polygon(surf, (190, 140, 85), pts_r)
        _draw_palm_tree(surf, cx - 65, base_y, 40)
        _draw_palm_tree(surf, cx + 65, base_y, 40)

    elif group_key == "green":  # Kalimantan: Rainforest & Longhouse
        pygame.draw.polygon(surf, (25, 80, 45), [(rect.x + 5, base_y), (cx - 30, base_y - 46), (cx + 25, base_y)])
        pygame.draw.polygon(surf, (35, 100, 55), [(cx, base_y), (cx + 50, base_y - 48), (rect.right - 5, base_y)])
        # Longhouse
        pygame.draw.rect(surf, (140, 95, 50), (cx - 40, base_y - 24, 80, 20), border_radius=2)
        pygame.draw.arc(surf, (180, 130, 70), pygame.Rect(cx - 44, base_y - 36, 88, 24), 0, math.pi, 3)

    elif group_key == "dark_blue":  # Jakarta: Monas Landmark
        # Skyline behind
        _draw_city_silhouette(surf, rect.width - 20, rect.height, random.Random(12), base_y, (35, 55, 75), scale=0.5)
        # Monas
        _draw_monas_bg(surf, cx, base_y, 52)

    else:
        # Default transport / station / utility
        pygame.draw.rect(surf, (160, 190, 220), (cx - 45, base_y - 32, 90, 32), border_radius=4)
        for i in range(4):
            pygame.draw.rect(surf, (255, 240, 180), (cx - 38 + i * 20, base_y - 24, 14, 14), border_radius=2)


def draw_event_card_icon(surf: pygame.Surface, cx: int, cy: int, is_chance: bool) -> None:
    """Draw a large, beautiful emblem in the center of Chance / Community Chest cards."""
    size = 42
    if is_chance:
        # Golden Indonesian sunburst / compass
        col_main = (255, 215, 80)
        col_dark = (190, 140, 30)
        pygame.draw.circle(surf, col_dark, (cx, cy), size + 2)
        pygame.draw.circle(surf, col_main, (cx, cy), size)
        pygame.draw.circle(surf, (40, 30, 15), (cx, cy), size - 6)
        # 8-point gold compass star
        for a in range(0, 360, 45):
            rad = math.radians(a)
            tip_x = cx + int(math.cos(rad) * (size - 10))
            tip_y = cy + int(math.sin(rad) * (size - 10))
            pygame.draw.line(surf, col_main, (cx, cy), (tip_x, tip_y), 3)
        pygame.draw.circle(surf, col_main, (cx, cy), 6)
    else:
        # Community Chest: overflowing treasure chest
        col_box = (150, 100, 45)
        col_gold = (255, 215, 80)
        # Chest body
        pygame.draw.rect(surf, col_box, (cx - size, cy - 8, size * 2, size), border_radius=4)
        pygame.draw.rect(surf, (190, 130, 60), (cx - size, cy - 8, size * 2, size), width=2, border_radius=4)
        # Curved lid
        pygame.draw.arc(surf, (200, 150, 70), pygame.Rect(cx - size, cy - 28, size * 2, 40), 0, math.pi, 4)
        # Gold coins spilling out
        for ox, oy in [(-12, -14), (0, -18), (14, -12), (-6, -10), (8, -8)]:
            pygame.draw.circle(surf, col_gold, (cx + ox, cy + oy), 7)
            pygame.draw.circle(surf, (190, 140, 30), (cx + ox, cy + oy), 7, width=1)


def draw_jail_bars_art(surf: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw iron prison bars with a golden padlock for the Jail modal."""
    pygame.draw.rect(surf, (14, 22, 30), rect, border_radius=8)
    pygame.draw.rect(surf, (55, 75, 95), rect, width=1, border_radius=8)

    bar_col = (110, 125, 145)
    high_col = (165, 185, 205)

    # Vertical iron bars
    num_bars = 7
    step = rect.width // (num_bars + 1)
    for i in range(1, num_bars + 1):
        bx = rect.x + i * step
        pygame.draw.line(surf, bar_col, (bx, rect.y + 6), (bx, rect.bottom - 6), 4)
        pygame.draw.line(surf, high_col, (bx - 1, rect.y + 6), (bx - 1, rect.bottom - 6), 1)

    # Horizontal crossbars
    for hy in (rect.y + rect.height // 4, rect.bottom - rect.height // 4):
        pygame.draw.line(surf, bar_col, (rect.x + 8, hy), (rect.right - 8, hy), 3)

    # Padlock in center
    cx, cy = rect.centerx, rect.centery
    # Shackle arc
    pygame.draw.arc(surf, (160, 175, 190), pygame.Rect(cx - 10, cy - 18, 20, 20), 0, math.pi, 3)
    # Lock body
    pygame.draw.rect(surf, (225, 175, 60), (cx - 14, cy - 6, 28, 22), border_radius=4)
    # Keyhole
    pygame.draw.circle(surf, (30, 30, 40), (cx, cy + 2), 3)
    pygame.draw.line(surf, (30, 30, 40), (cx, cy + 2), (cx, cy + 7), 2)


def draw_trophy_art(surf: pygame.Surface, cx: int, cy: int, size: int) -> None:
    """Draw a glorious golden championship trophy cup with handles and stars."""
    col_gold = (255, 215, 80)
    col_dark = (195, 140, 30)
    col_high = (255, 245, 170)

    # Base pedestal
    pw = size * 5 // 4
    pygame.draw.rect(surf, (40, 50, 60), (cx - pw // 2, cy + size // 2, pw, size // 4), border_radius=3)
    pygame.draw.rect(surf, col_dark, (cx - pw // 2, cy + size // 2, pw, size // 4), width=1, border_radius=3)

    # Stem
    pygame.draw.rect(surf, col_gold, (cx - size // 6, cy + size // 4, size // 3, size // 4))

    # Cup bowl
    cup_pts = [
        (cx - size // 2, cy - size // 3),
        (cx + size // 2, cy - size // 3),
        (cx + size // 3, cy + size // 4),
        (cx - size // 3, cy + size // 4)
    ]
    pygame.draw.polygon(surf, col_gold, cup_pts)
    pygame.draw.polygon(surf, col_dark, cup_pts, width=2)
    # Specular shine
    pygame.draw.line(surf, col_high, (cx - size // 3, cy - size // 4), (cx - size // 4, cy + size // 6), 2)

    # Handles
    pygame.draw.arc(surf, col_gold, pygame.Rect(cx - size * 3 // 4, cy - size // 4, size // 2, size // 2), math.pi / 2, 3 * math.pi / 2, 3)
    pygame.draw.arc(surf, col_gold, pygame.Rect(cx + size // 4, cy - size // 4, size // 2, size // 2), -math.pi / 2, math.pi / 2, 3)

    # Star emblem on cup
    pygame.draw.circle(surf, col_high, (cx, cy - size // 10), size // 8)


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================
def clear_cache() -> None:
    """Clear all cached surfaces (call on resolution change)."""
    global _surf_cache
    _surf_cache.clear()
