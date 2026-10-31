"""
Premium Indonesian Cultural Vector Tokens with idle animations.
All tokens are drawn procedurally with 2.5D shading and expressive silhouettes.
"""
import math
import pygame
from typing import Tuple

TOKEN_TYPES = [
    ("monas",   "Monas",       "Monumen Nasional Jakarta"),
    ("becak",   "Becak",       "Kendaraan Roda Tiga Tradisional"),
    ("angkot",  "Angkot",      "Angkutan Kota Khas Nusantara"),
    ("pinisi",  "Kapal Pinisi","Kapal Layar Tradisional Bugis-Makassar"),
    ("wayang",  "Wayang",      "Seni Teater Boneka Bayangan"),
    ("komodo",  "Komodo",      "Fauna Purba Kepulauan Komodo"),
]


class TokenRenderer:
    """Draws stylized, animated Indonesian cultural tokens."""

    @classmethod
    def draw_token(
        cls,
        surface: pygame.Surface,
        token_type: str,
        center: Tuple[int, int],
        radius: int,
        color: Tuple[int, int, int],
        is_active: bool = False,
        anim_time: float = 0.0
    ) -> None:
        cx, cy = int(center[0]), int(center[1])
        r = radius

        # Active player gentle float/bob
        if is_active:
            cy += int(math.sin(anim_time * 3.8) * 2.5)

        # Drop shadow (oval under token)
        shadow_surf = pygame.Surface((r * 3, r), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 55), (0, 0, r * 3, r))
        surface.blit(shadow_surf, (cx - r * 3 // 2, cy + r - 2))

        # Active player pulsing glow ring
        if is_active:
            pulse = 0.6 + 0.4 * math.sin(anim_time * 5.0)
            glow_r = r + int(4 * pulse)
            glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
            alpha = int(180 * pulse)
            pygame.draw.circle(glow_surf, (232, 184, 80, alpha), (glow_r + 2, glow_r + 2), glow_r, width=3)
            surface.blit(glow_surf, (cx - glow_r - 2, cy - glow_r - 2))

        # Outer ring (white / light)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r + 1)

        # Token disc — radial gradient look via concentric circles
        for i in range(r, 0, -1):
            t = i / r
            shade = (
                int(color[0] * (0.7 + 0.3 * t)),
                int(color[1] * (0.7 + 0.3 * t)),
                int(color[2] * (0.7 + 0.3 * t)),
            )
            pygame.draw.circle(surface, shade, (cx, cy), i)

        # Top specular highlight
        hl_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(hl_surf, (255, 255, 255, 55), (r - r // 4, r - r // 3), r // 2)
        surface.blit(hl_surf, (cx - r, cy - r))

        # Border
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r, width=2)

        # Silhouette icon
        inner_r = int(r * 0.62)
        fn_map = {
            "monas":  cls._draw_monas,
            "becak":  cls._draw_becak,
            "angkot": cls._draw_angkot,
            "pinisi": cls._draw_pinisi,
            "wayang": cls._draw_wayang,
            "komodo": cls._draw_komodo,
        }
        draw_fn = fn_map.get(token_type, cls._draw_monas)
        draw_fn(surface, cx, cy, inner_r)

    # -------------------------------------------------------------------------
    # MONAS — Monumen Nasional
    # -------------------------------------------------------------------------
    @classmethod
    def _draw_monas(cls, surface, cx, cy, r):
        w = (255, 255, 255)
        gold = (241, 196, 15)
        # Platform steps
        pygame.draw.rect(surface, w, (cx - r * 6 // 10, cy + r * 3 // 8, r * 6 // 5, r // 5))
        pygame.draw.rect(surface, w, (cx - r * 4 // 10, cy + r * 2 // 8, r * 4 // 5, r // 8))
        # Obelisk
        pts = [
            (cx - r // 5, cy + r * 2 // 8),
            (cx + r // 5, cy + r * 2 // 8),
            (cx + r // 8, cy - r * 3 // 8),
            (cx - r // 8, cy - r * 3 // 8)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Gold flame
        flame = [
            (cx, cy - r),
            (cx + r // 5, cy - r * 3 // 8),
            (cx - r // 5, cy - r * 3 // 8)
        ]
        pygame.draw.polygon(surface, gold, flame)

    # -------------------------------------------------------------------------
    # BECAK — Traditional pedicab
    # -------------------------------------------------------------------------
    @classmethod
    def _draw_becak(cls, surface, cx, cy, r):
        w = (255, 255, 255)
        # Two wheels
        pygame.draw.circle(surface, w, (cx - r // 2, cy + r // 3), r // 4, width=2)
        pygame.draw.circle(surface, w, (cx + r // 2, cy + r // 3), r // 4, width=2)
        # Passenger hood arc
        hood_rect = pygame.Rect(cx - r * 3 // 4, cy - r // 2, r * 3 // 2, r)
        pygame.draw.arc(surface, w, hood_rect, 0, math.pi, 3)
        # Frame / handlebar
        pygame.draw.line(surface, w, (cx - r // 4, cy + r // 3), (cx + r // 3, cy - r // 5), 2)
        pygame.draw.line(surface, w, (cx + r // 3, cy - r // 5), (cx + r // 2, cy + r // 4), 2)

    # -------------------------------------------------------------------------
    # ANGKOT — Minivan public transport
    # -------------------------------------------------------------------------
    @classmethod
    def _draw_angkot(cls, surface, cx, cy, r):
        w = (255, 255, 255)
        dark = (30, 35, 45)
        # Body
        pts = [
            (cx - r, cy + r // 4),
            (cx + r, cy + r // 4),
            (cx + r, cy - r // 5),
            (cx + r // 2, cy - r // 2),
            (cx - r, cy - r // 2)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Windshield (dark)
        wp = [
            (cx - r * 3 // 4, cy - r * 2 // 5),
            (cx - r // 4, cy - r * 2 // 5),
            (cx - r // 4, cy - r // 8),
            (cx - r * 3 // 4, cy - r // 8)
        ]
        pygame.draw.polygon(surface, dark, wp)
        # Windows
        for i in range(2):
            wx = cx + r // 8 + i * (r // 2)
            pygame.draw.rect(surface, dark, (wx, cy - r * 2 // 5, r // 4, r // 4))
        # Wheels
        pygame.draw.circle(surface, dark, (cx - r // 2, cy + r // 4), r // 4)
        pygame.draw.circle(surface, dark, (cx + r // 2, cy + r // 4), r // 4)

    # -------------------------------------------------------------------------
    # PINISI — Bugis-Makassar traditional ship
    # -------------------------------------------------------------------------
    @classmethod
    def _draw_pinisi(cls, surface, cx, cy, r):
        w = (255, 255, 255)
        cream = (240, 245, 255)
        # Hull
        hull = [
            (cx - r, cy + r // 5),
            (cx + r, cy + r // 8),
            (cx + r * 3 // 4, cy + r // 2),
            (cx - r * 3 // 4, cy + r // 2)
        ]
        pygame.draw.polygon(surface, w, hull)
        # Front mast (taller)
        mast1_x = cx - r // 4
        pygame.draw.line(surface, w, (mast1_x, cy + r // 5), (mast1_x, cy - r * 4 // 5), 2)
        # Back mast (shorter)
        mast2_x = cx + r // 3
        pygame.draw.line(surface, w, (mast2_x, cy + r // 5), (mast2_x, cy - r // 2), 2)
        # Main sail (triangle)
        sail1 = [(mast1_x, cy - r * 3 // 4), (mast1_x - r * 3 // 4, cy + r // 8), (mast1_x, cy + r // 8)]
        pygame.draw.polygon(surface, cream, sail1)
        # Back sail
        sail2 = [(mast2_x, cy - r // 3), (mast2_x + r // 3, cy + r // 8), (mast2_x, cy + r // 8)]
        pygame.draw.polygon(surface, cream, sail2)

    # -------------------------------------------------------------------------
    # WAYANG — Shadow puppet
    # -------------------------------------------------------------------------
    @classmethod
    def _draw_wayang(cls, surface, cx, cy, r):
        w = (255, 255, 255)
        # Gunungan outline (elongated pointed silhouette)
        pts = [
            (cx, cy - r),
            (cx + r * 2 // 3, cy - r // 3),
            (cx + r // 2, cy + r // 4),
            (cx + r // 4, cy + r * 3 // 4),
            (cx, cy + r),
            (cx - r // 4, cy + r * 3 // 4),
            (cx - r // 2, cy + r // 4),
            (cx - r * 2 // 3, cy - r // 3)
        ]
        pygame.draw.polygon(surface, w, pts)
        # Inner split (puppet body detail)
        pygame.draw.line(surface, (30, 35, 45), (cx, cy - r // 2), (cx, cy + r // 3), 2)
        # Head circle
        pygame.draw.circle(surface, (30, 35, 45), (cx, cy - r // 2), r // 5)
        pygame.draw.circle(surface, w, (cx, cy - r // 2), r // 5, width=1)

    # -------------------------------------------------------------------------
    # KOMODO — Komodo dragon
    # -------------------------------------------------------------------------
    @classmethod
    def _draw_komodo(cls, surface, cx, cy, r):
        w = (255, 255, 255)
        # Body (elongated ellipse)
        body_rect = pygame.Rect(cx - r * 3 // 4, cy - r // 5, r * 3 // 2, r * 2 // 5)
        pygame.draw.ellipse(surface, w, body_rect)
        # Head
        pygame.draw.ellipse(surface, w, pygame.Rect(cx + r // 3, cy - r // 3, r * 3 // 4, r // 3))
        # Tail (tapered line going left)
        pygame.draw.line(surface, w, (cx - r * 3 // 4, cy), (cx - r, cy + r // 3), 3)
        pygame.draw.line(surface, w, (cx - r, cy + r // 3), (cx - r * 5 // 4, cy + r // 2), 2)
        # Legs (4 short lines)
        for lx, ly_off in [(cx - r // 2, 1), (cx - r // 6, 1), (cx + r // 6, -1), (cx + r // 2, -1)]:
            pygame.draw.line(surface, w, (lx, cy + r // 8), (lx + 2, cy + r // 2 * ly_off + r // 3), 2)
        # Eye
        pygame.draw.circle(surface, (30, 35, 45), (cx + r * 5 // 8, cy - r // 5), 3)
        # Tongue
        pygame.draw.line(surface, (210, 50, 60), (cx + r, cy - r // 8), (cx + r + r // 4, cy - r // 12), 2)
