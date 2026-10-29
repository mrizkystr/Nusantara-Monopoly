"""Indonesian Cultural Vector Tokens rendered procedurally."""
import math
import pygame
from typing import Tuple, List, Dict

TOKEN_TYPES = [
    ("monas", "Monas", "Ikon Monumen Nasional Jakarta"),
    ("becak", "Becak", "Kendaraan Roda Tiga Tradisional"),
    ("angkot", "Angkot", "Angkutan Kota Khas Nusantara"),
    ("pinisi", "Kapal Pinisi", "Kapal Layar Tradisional Bugis-Makassar"),
    ("wayang", "Wayang", "Seni Teater Boneka Bayangan"),
    ("komodo", "Komodo", "Fauna Purba Endemik Kepulauan Komodo")
]


class TokenRenderer:
    """Draws stylized Indonesian cultural tokens using vector geometry."""

    @classmethod
    def draw_token(
        cls,
        surface: pygame.Surface,
        token_type: str,
        center: Tuple[int, int],
        radius: int,
        color: Tuple[int, int, int],
        is_active: bool = False
    ) -> None:
        cx, cy = int(center[0]), int(center[1])
        r = radius

        # Subtle shadow
        pygame.draw.circle(surface, (0, 0, 0, 80), (cx + 2, cy + 2), r)

        # Active player pulsing glow ring
        if is_active:
            pygame.draw.circle(surface, (232, 184, 109), (cx, cy), r + 4, width=2)

        # Base token disc
        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, (248, 245, 238), (cx, cy), r, width=2)

        # Draw specific token silhouette in clean crisp white inside the token disc
        inner_r = int(r * 0.65)
        if token_type == "monas":
            cls._draw_monas(surface, cx, cy, inner_r)
        elif token_type == "becak":
            cls._draw_becak(surface, cx, cy, inner_r)
        elif token_type == "angkot":
            cls._draw_angkot(surface, cx, cy, inner_r)
        elif token_type == "pinisi":
            cls._draw_pinisi(surface, cx, cy, inner_r)
        elif token_type == "wayang":
            cls._draw_wayang(surface, cx, cy, inner_r)
        elif token_type == "komodo":
            cls._draw_komodo(surface, cx, cy, inner_r)
        else:
            cls._draw_monas(surface, cx, cy, inner_r)

    @classmethod
    def _draw_monas(cls, surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
        # Base platform
        w = (255, 255, 255)
        gold = (241, 196, 15)
        # Platform square
        pygame.draw.rect(surface, w, (cx - r // 2, cy + r // 3, r, r // 4))
        # Obelisk pillar
        pts = [
            (cx - r // 6, cy + r // 3),
            (cx + r // 6, cy + r // 3),
            (cx + r // 8, cy - r // 3),
            (cx - r // 8, cy - r // 3)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Golden flame at top
        flame_pts = [
            (cx, cy - r),
            (cx + r // 6, cy - r // 3),
            (cx - r // 6, cy - r // 3)
        ]
        pygame.draw.polygon(surface, gold, flame_pts)

    @classmethod
    def _draw_becak(cls, surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
        w = (255, 255, 255)
        # 2 Wheels at bottom
        pygame.draw.circle(surface, w, (cx - r // 2, cy + r // 3), r // 4, width=1)
        pygame.draw.circle(surface, w, (cx + r // 2, cy + r // 3), r // 4, width=1)
        # Canopy curved passenger hood
        pygame.draw.arc(surface, w, (cx - r // 2, cy - r // 2, r, r), 0.5, 2.8, 2)
        # Driver frame line
        pygame.draw.line(surface, w, (cx - r // 4, cy + r // 4), (cx + r // 3, cy - r // 4), 2)

    @classmethod
    def _draw_angkot(cls, surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
        w = (255, 255, 255)
        # Minivan boxy body
        pts = [
            (cx - r, cy + r // 3),
            (cx + r, cy + r // 3),
            (cx + r, cy),
            (cx + r // 2, cy - r // 2),
            (cx - r, cy - r // 2)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Wheels
        pygame.draw.circle(surface, (30, 40, 50), (cx - r // 2, cy + r // 3), r // 4)
        pygame.draw.circle(surface, (30, 40, 50), (cx + r // 2, cy + r // 3), r // 4)

    @classmethod
    def _draw_pinisi(cls, surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
        w = (255, 255, 255)
        # Boat hull curve
        hull_pts = [
            (cx - r, cy + r // 4),
            (cx + r, cy + r // 5),
            (cx + r // 2, cy + r // 2),
            (cx - r // 2, cy + r // 2)
        ]
        pygame.draw.polygon(surface, w, hull_pts)
        # 2 Masts
        pygame.draw.line(surface, w, (cx - r // 4, cy + r // 4), (cx - r // 4, cy - r * 4 // 5), 2)
        pygame.draw.line(surface, w, (cx + r // 3, cy + r // 4), (cx + r // 3, cy - r // 2), 2)
        # Triangular sails
        sail1 = [(cx - r // 4, cy - r * 3 // 4), (cx - r * 3 // 4, cy), (cx - r // 4, cy)]
        pygame.draw.polygon(surface, (240, 245, 255), sail1)

    @classmethod
    def _draw_wayang(cls, surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
        w = (255, 255, 255)
        # Gunungan / Wayang head pointed silhouette
        pts = [
            (cx, cy - r),
            (cx + r * 2 // 3, cy - r // 4),
            (cx + r // 3, cy + r // 2),
            (cx, cy + r * 3 // 4),
            (cx - r // 3, cy + r // 2),
            (cx - r * 2 // 3, cy - r // 4)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Inner slit eye/nose
        pygame.draw.line(surface, (40, 50, 60), (cx, cy - r // 2), (cx, cy + r // 4), 2)

    @classmethod
    def _draw_komodo(cls, surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
        w = (255, 255, 255)
        # Curved lizard body and long tail
        pts = [
            (cx - r, cy - r // 4),
            (cx - r // 2, cy - r // 3),
            (cx, cy),
            (cx + r // 2, cy + r // 4),
            (cx + r, cy + r // 2),
            (cx + r // 3, cy + r // 3),
            (cx, cy + r // 6),
            (cx - r // 2, cy)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Legs
        pygame.draw.line(surface, w, (cx - r // 4, cy), (cx - r // 2, cy + r // 2), 2)
        pygame.draw.line(surface, w, (cx + r // 4, cy + r // 6), (cx + r // 2, cy + r * 2 // 3), 2)
