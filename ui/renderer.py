"""
Premium 2.5D board renderer for Nusantara Property Tycoon.
Renders an Indonesian-themed board with depth, layering, environmental art,
3D buildings, dynamic camera zoom/pan integration, and pixel-perfect hit testing.
"""
import math
import pygame
from typing import Dict, List, Tuple, Optional
from game.state import GameState, TileType, PropertyColorGroup
from game.board import Board
from game.player import Player
from game.property import Tile
from game.dice import Dice
from game.economy import format_rupiah
from game.engine import GameEngine
from ui.components import get_font, LogBox
from ui.tokens import TokenRenderer
from ui.camera import Camera, CameraState
from ui.visual_assets import (
    C_BG, C_BOARD_BG, C_BOARD_BORDER, C_BOARD_INNER,
    C_TILE_LIGHT, C_TILE_SHADOW, C_TILE_BORDER,
    C_CORNER_BG, C_GOLD, C_GOLD_LIGHT, C_TEAL, C_RED,
    C_TEXT_DARK, C_TEXT_MED, C_TEXT_LIGHT,
    C_SUCCESS, C_DANGER, C_SURFACE, C_SURFACE_MED, C_SURFACE_LIGHT,
    GROUP_COLORS_RICH, GROUP_NAMES,
    make_game_background, make_board_frame,
    draw_house_sprite, draw_hotel_sprite, draw_region_deco,
    draw_rounded_rect_with_shadow, draw_bevel_rect, lerp_color,
    clear_cache
)

# Backward-compatible color exports
COLOR_BG             = C_BG
COLOR_SURFACE        = C_SURFACE
COLOR_SURFACE_LIGHT  = C_SURFACE_LIGHT
COLOR_ACCENT_GOLD    = C_GOLD
COLOR_ACCENT_TEAL    = C_TEAL
COLOR_TEXT_PRIMARY   = C_TEXT_LIGHT
COLOR_TEXT_SECONDARY = (175, 195, 185)
COLOR_DANGER         = C_DANGER
COLOR_SUCCESS        = C_SUCCESS

GROUP_COLORS = {
    PropertyColorGroup.BROWN:      GROUP_COLORS_RICH["brown"],
    PropertyColorGroup.LIGHT_BLUE: GROUP_COLORS_RICH["light_blue"],
    PropertyColorGroup.PINK:       GROUP_COLORS_RICH["pink"],
    PropertyColorGroup.ORANGE:     GROUP_COLORS_RICH["orange"],
    PropertyColorGroup.RED:        GROUP_COLORS_RICH["red"],
    PropertyColorGroup.YELLOW:     GROUP_COLORS_RICH["yellow"],
    PropertyColorGroup.GREEN:      GROUP_COLORS_RICH["green"],
    PropertyColorGroup.DARK_BLUE:  GROUP_COLORS_RICH["dark_blue"],
}

_GROUP_KEY = {
    PropertyColorGroup.BROWN:      "brown",
    PropertyColorGroup.LIGHT_BLUE: "light_blue",
    PropertyColorGroup.PINK:       "pink",
    PropertyColorGroup.ORANGE:     "orange",
    PropertyColorGroup.RED:        "red",
    PropertyColorGroup.YELLOW:     "yellow",
    PropertyColorGroup.GREEN:      "green",
    PropertyColorGroup.DARK_BLUE:  "dark_blue",
}

_TILE_SIDE = {}
for _p in range(1, 10):   _TILE_SIDE[_p]  = "bottom"
for _p in range(11, 20):  _TILE_SIDE[_p]  = "left"
for _p in range(21, 30):  _TILE_SIDE[_p]  = "top"
for _p in range(31, 40):  _TILE_SIDE[_p]  = "right"


class BoardRenderer:
    """Premium 2.5D board renderer with camera integration."""

    def __init__(self):
        self.tile_rects: Dict[int, pygame.Rect] = {}
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)  # Backward compat
        self.log_box = LogBox(pygame.Rect(0, 0, 0, 0))

        self._cached_board_surf: Optional[pygame.Surface] = None
        self._cached_bg_surf: Optional[pygame.Surface] = None
        self._board_buffer_surf: Optional[pygame.Surface] = None
        self._last_board_size: int = 0
        self._last_screen_size: Tuple = (0, 0)

        self.hovered_tile: Optional[int] = None
        self._anim_time: float = 0.0

        # Current crop region for camera mouse hit-testing: (crop_x, crop_y, crop_w, crop_h)
        self._last_crop_rect: Optional[Tuple[float, float, float, float]] = None

    def update(self, dt: float) -> None:
        self._anim_time += dt

    def update_layout(self, screen_w: int, screen_h: int) -> None:
        """Calculate board dimensions centered between the mobile-style top and bottom HUD."""
        margin = 10
        top_h = 72
        dock_h = 108

        # Available space between top bar and bottom action dock
        avail_h = screen_h - top_h - dock_h - (margin * 2)
        avail_w = screen_w - (margin * 2)
        board_size = max(420, min(avail_w, avail_h))

        board_x = (screen_w - board_size) // 2
        board_y = top_h + margin + (avail_h - board_size) // 2

        self.board_rect = pygame.Rect(board_x, board_y, board_size, board_size)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)

        if board_size != self._last_board_size:
            self._cached_board_surf = None
            self._board_buffer_surf = pygame.Surface((board_size, board_size))
            self._last_board_size = board_size
            clear_cache()

        if (screen_w, screen_h) != self._last_screen_size:
            self._cached_bg_surf = None
            self._last_screen_size = (screen_w, screen_h)

        # Calculate perimeter tile rects in world/board coordinates
        bx, by, bsize = self.board_rect.x, self.board_rect.y, self.board_rect.width
        border_thick = max(10, int(bsize * 0.024))
        inner_size   = bsize - 2 * border_thick
        inner_x      = bx + border_thick
        inner_y      = by + border_thick

        corner_size = int(inner_size * 0.138)
        edge_w = (inner_size - 2 * corner_size) / 9.0

        self.tile_rects.clear()

        # Pos 0: Bottom-Right corner (MULAI)
        self.tile_rects[0] = pygame.Rect(
            inner_x + inner_size - corner_size,
            inner_y + inner_size - corner_size,
            corner_size, corner_size
        )

        # Pos 1..9: Bottom edge (Right to Left)
        for i in range(1, 10):
            x = inner_x + inner_size - corner_size - int(i * edge_w)
            w = int((inner_x + inner_size - corner_size - int((i - 1) * edge_w)) - x)
            self.tile_rects[i] = pygame.Rect(x, inner_y + inner_size - corner_size, w, corner_size)

        # Pos 10: Bottom-Left corner (PENJARA)
        self.tile_rects[10] = pygame.Rect(inner_x, inner_y + inner_size - corner_size, corner_size, corner_size)

        # Pos 11..19: Left edge (Bottom to Top)
        for i in range(1, 10):
            pos = 10 + i
            y = inner_y + inner_size - corner_size - int(i * edge_w)
            h = int((inner_y + inner_size - corner_size - int((i - 1) * edge_w)) - y)
            self.tile_rects[pos] = pygame.Rect(inner_x, y, corner_size, h)

        # Pos 20: Top-Left corner (PARKIR GRATIS)
        self.tile_rects[20] = pygame.Rect(inner_x, inner_y, corner_size, corner_size)

        # Pos 21..29: Top edge (Left to Right)
        for i in range(1, 10):
            pos = 20 + i
            x = inner_x + corner_size + int((i - 1) * edge_w)
            w = int((inner_x + corner_size + int(i * edge_w)) - x)
            self.tile_rects[pos] = pygame.Rect(x, inner_y, w, corner_size)

        # Pos 30: Top-Right corner (MASUK PENJARA)
        self.tile_rects[30] = pygame.Rect(
            inner_x + inner_size - corner_size, inner_y, corner_size, corner_size
        )

        # Pos 31..39: Right edge (Top to Bottom)
        for i in range(1, 10):
            pos = 30 + i
            y = inner_y + corner_size + int((i - 1) * edge_w)
            h = int((inner_y + corner_size + int(i * edge_w)) - y)
            self.tile_rects[pos] = pygame.Rect(inner_x + inner_size - corner_size, y, corner_size, h)

    def get_tile_at_pos(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """
        Return the board position (0-39) clicked, taking camera zoom into account.
        Compatible with raw screen coordinates and unit tests.
        """
        mx, my = mouse_pos
        bx, by = self.board_rect.x, self.board_rect.y
        bsize = self.board_rect.width

        # Check if click is inside the board view
        if not self.board_rect.collidepoint(mouse_pos):
            return None

        # If camera zoomed in, map screen coords through last crop transform
        if self._last_crop_rect is not None:
            crop_x, crop_y, crop_w, crop_h = self._last_crop_rect
            norm_x = (mx - bx) / float(bsize)
            norm_y = (my - by) / float(bsize)
            mapped_x = bx + crop_x + norm_x * crop_w
            mapped_y = by + crop_y + norm_y * crop_h
            test_pos = (int(mapped_x), int(mapped_y))
        else:
            test_pos = mouse_pos

        for pos, rect in self.tile_rects.items():
            if rect.collidepoint(test_pos):
                return pos
        return None

    def draw(
        self,
        surface: pygame.Surface,
        engine: GameEngine,
        animated_positions: Optional[Dict[int, int]] = None,
        dice_anim=None,
        active_dest_tile: Optional[int] = None,
        camera: Optional[Camera] = None
    ) -> None:
        """Full render pass with 2.5D camera zoom and smoothscaling."""
        w, h = surface.get_size()
        bsize = self.board_rect.width
        bx, by = self.board_rect.x, self.board_rect.y

        # Draw full board table background
        if self._cached_bg_surf is None or self._cached_bg_surf.get_size() != (w, h):
            self._cached_bg_surf = make_game_background(w, h)
        surface.blit(self._cached_bg_surf, (0, 0))

        # Ensure board buffer surface exists
        if self._board_buffer_surf is None or self._board_buffer_surf.get_size() != (bsize, bsize):
            self._board_buffer_surf = pygame.Surface((bsize, bsize))

        # 1. Render static board tiles into cache
        if self._cached_board_surf is None:
            self._render_static_board(engine.board)

        # Blit cached static board onto board buffer (relative coords 0,0)
        self._board_buffer_surf.blit(self._cached_board_surf, (0, 0))

        # 2. Draw active destination tile highlight pulse
        if active_dest_tile is not None and active_dest_tile in self.tile_rects:
            d_rect = self.tile_rects[active_dest_tile]
            rel_rect = pygame.Rect(d_rect.x - bx, d_rect.y - by, d_rect.width, d_rect.height)
            pulse_alpha = int(90 + 60 * math.sin(self._anim_time * 5.5))
            pulse_surf = pygame.Surface((rel_rect.width, rel_rect.height), pygame.SRCALPHA)
            pulse_surf.fill((255, 220, 80, pulse_alpha))
            self._board_buffer_surf.blit(pulse_surf, rel_rect.topleft)
            pygame.draw.rect(self._board_buffer_surf, C_GOLD_LIGHT, rel_rect, width=3, border_radius=3)

        # 3. Draw hover outline
        if self.hovered_tile is not None and self.hovered_tile in self.tile_rects:
            h_rect = self.tile_rects[self.hovered_tile]
            rel_h = pygame.Rect(h_rect.x - bx, h_rect.y - by, h_rect.width, h_rect.height)
            hover_surf = pygame.Surface((rel_h.width, rel_h.height), pygame.SRCALPHA)
            hover_surf.fill((255, 255, 255, 40))
            self._board_buffer_surf.blit(hover_surf, rel_h.topleft)
            pygame.draw.rect(self._board_buffer_surf, (255, 255, 255, 140), rel_h, width=2, border_radius=2)

        # 4. Draw dynamic tile overlays (ownership, mortgages, 3D houses & hotel models)
        for pos in range(40):
            rect = self.tile_rects.get(pos)
            if rect:
                rel_rect = pygame.Rect(rect.x - bx, rect.y - by, rect.width, rect.height)
                tile = engine.board.get_tile(pos)
                if tile:
                    self._draw_dynamic_tile_overlay(self._board_buffer_surf, rel_rect, tile, pos, engine)

        # 5. Draw player tokens
        self._draw_tokens(self._board_buffer_surf, engine, animated_positions=animated_positions, bx=bx, by=by)

        # 6. Draw board center art + 2.5D dice
        self._draw_board_center(self._board_buffer_surf, engine, dice_anim=dice_anim, bx=bx, by=by)

        # 7. Apply Camera Zoom / Pan Transform
        if camera is not None and camera.zoom > 1.02:
            # Crop around camera focus
            zoom = camera.zoom
            crop_w = bsize / zoom
            crop_h = bsize / zoom
            rel_focus_x = camera.world_x - bx
            rel_focus_y = camera.world_y - by

            crop_x = max(0.0, min(bsize - crop_w, rel_focus_x - crop_w / 2.0))
            crop_y = max(0.0, min(bsize - crop_h, rel_focus_y - crop_h / 2.0))

            self._last_crop_rect = (crop_x, crop_y, crop_w, crop_h)

            crop_sub = self._board_buffer_surf.subsurface(pygame.Rect(int(crop_x), int(crop_y), int(crop_w), int(crop_h)))
            scaled_surf = pygame.transform.smoothscale(crop_sub, (bsize, bsize))
            surface.blit(scaled_surf, self.board_rect.topleft)
        else:
            self._last_crop_rect = None
            surface.blit(self._board_buffer_surf, self.board_rect.topleft)

        # Draw decorative gold border around the whole board frame
        pygame.draw.rect(surface, (160, 120, 55), self.board_rect, width=2, border_radius=12)

    def _render_static_board(self, board: Board) -> None:
        """Cache static 40-tile board graphics to achieve solid 60 FPS."""
        bsize = self.board_rect.width
        self._cached_board_surf = pygame.Surface((bsize, bsize), pygame.SRCALPHA)

        # Draw wooden board frame
        frame = make_board_frame(bsize)
        self._cached_board_surf.blit(frame, (0, 0))

        bx, by = self.board_rect.x, self.board_rect.y
        for pos in range(40):
            global_rect = self.tile_rects[pos]
            tile_rect = pygame.Rect(
                global_rect.x - bx, global_rect.y - by,
                global_rect.width, global_rect.height
            )
            tile = board.get_tile(pos)
            if tile:
                self._draw_static_tile(self._cached_board_surf, tile_rect, tile, pos)

    def _draw_static_tile(self, surf: pygame.Surface, rect: pygame.Rect, tile: Tile, pos: int) -> None:
        """Render individual static tile with 2.5D beveling."""
        is_corner = pos in (0, 10, 20, 30)
        if is_corner:
            self._draw_corner_tile(surf, rect, tile, pos)
            return

        draw_bevel_rect(surf, rect, C_TILE_LIGHT, bevel=2, radius=2)
        pygame.draw.rect(surf, C_TILE_BORDER, rect, width=1, border_radius=2)
        side = _TILE_SIDE.get(pos, "bottom")

        # Color group stripe
        stripe_thick = int(min(rect.width, rect.height) * 0.30)
        if tile.color_group:
            grp_color = GROUP_COLORS.get(tile.color_group, (100, 100, 100))
            grp_key   = _GROUP_KEY.get(tile.color_group, "")

            if side == "bottom":
                stripe_rect = pygame.Rect(rect.x, rect.y, rect.width, stripe_thick)
            elif side == "top":
                stripe_rect = pygame.Rect(rect.x, rect.bottom - stripe_thick, rect.width, stripe_thick)
            elif side == "left":
                stripe_rect = pygame.Rect(rect.right - stripe_thick, rect.y, stripe_thick, rect.height)
            else:
                stripe_rect = pygame.Rect(rect.x, rect.y, stripe_thick, rect.height)

            draw_bevel_rect(surf, stripe_rect, grp_color, bevel=2, radius=2)
            light = lerp_color(grp_color, (255, 255, 255), 0.25)
            pygame.draw.rect(surf, light, stripe_rect, width=1, border_radius=2)
            draw_region_deco(surf, stripe_rect, grp_key, side)

        # Special tiles
        if tile.type in (TileType.CHANCE, TileType.COMMUNITY_CHEST, TileType.TAX, TileType.TRANSPORT, TileType.UTILITY):
            self._draw_special_tile_content(surf, rect, tile, side)
            return

        # Property text
        self._draw_property_text(surf, rect, tile, pos, side)

    def _draw_special_tile_content(self, surf, rect, tile, side):
        sym_map = {
            TileType.CHANCE:         ("?",   C_GOLD,          "KESEMP."),
            TileType.COMMUNITY_CHEST:("$",   C_TEAL,          "DANA UMUM"),
            TileType.TAX:            ("%",   (170, 100, 200), tile.name[:7]),
            TileType.TRANSPORT:      ("KA",  (70, 100, 130),  "STASIUN"),
            TileType.UTILITY:        ("PLN", (46, 185, 145),  "UTILITAS"),
        }
        sym, col, short_name = sym_map.get(tile.type, ("?", C_GOLD, ""))
        cx, cy = rect.centerx, rect.centery

        f_sym   = get_font(max(8, min(13, rect.height // 3)), bold=True)
        f_label = get_font(max(6, min(10, rect.height // 5)), bold=True)

        sym_surf = f_sym.render(sym, True, col)
        lbl_surf = f_label.render(short_name, True, C_TEXT_DARK)

        if side in ("bottom", "top"):
            surf.blit(sym_surf, sym_surf.get_rect(center=(cx, cy - 4)))
            surf.blit(lbl_surf, lbl_surf.get_rect(center=(cx, cy + lbl_surf.get_height() // 2 + 2)))
        else:
            surf.blit(sym_surf, sym_surf.get_rect(center=(cx, cy - 5)))
            surf.blit(lbl_surf, lbl_surf.get_rect(center=(cx, cy + 7)))

    def _draw_property_text(self, surf, rect, tile, pos, side):
        stripe_thick = int(min(rect.width, rect.height) * 0.30)

        # Precise non-stripe center calculation
        if side == "bottom":
            text_cx = rect.centerx
            text_cy = rect.y + stripe_thick + (rect.height - stripe_thick) // 2
        elif side == "top":
            text_cx = rect.centerx
            text_cy = rect.y + (rect.height - stripe_thick) // 2
        elif side == "left":
            text_cx = rect.x + (rect.width - stripe_thick) // 2
            text_cy = rect.centery
        else:  # right
            text_cx = rect.x + stripe_thick + (rect.width - stripe_thick) // 2
            text_cy = rect.centery

        if side in ("left", "right"):
            name_short = tile.name[:8] if len(tile.name) > 8 else tile.name
            f_name = get_font(max(7, min(10, rect.height // 5)), bold=True)
            f_price = get_font(max(6, min(9, rect.height // 6)))

            name_surf_h = f_name.render(name_short, True, C_TEXT_DARK)
            price_str = f"Rp{tile.purchase_price // 1000}rb" if tile.purchase_price > 0 else ""
            price_surf_h = f_price.render(price_str, True, C_TEXT_MED)

            rot = 90 if side == "left" else -90
            name_surf = pygame.transform.rotate(name_surf_h, rot)
            price_surf = pygame.transform.rotate(price_surf_h, rot)

            surf.blit(name_surf, name_surf.get_rect(center=(text_cx, text_cy - price_surf.get_height() // 2 - 1)))
            if price_str:
                surf.blit(price_surf, price_surf.get_rect(center=(text_cx, text_cy + name_surf.get_height() // 2 + 1)))
        else:
            name_short = tile.name[:9] if len(tile.name) > 9 else tile.name
            f_name  = get_font(max(7, min(11, int(rect.width * 0.14))), bold=True)
            f_price = get_font(max(6, min(9,  int(rect.width * 0.11))))

            name_surf  = f_name.render(name_short, True, C_TEXT_DARK)
            surf.blit(name_surf, name_surf.get_rect(center=(text_cx, text_cy - 2)))

            if tile.purchase_price > 0:
                price_str  = f"Rp{tile.purchase_price // 1000}rb"
                price_surf = f_price.render(price_str, True, C_TEXT_MED)
                surf.blit(price_surf, price_surf.get_rect(center=(text_cx, text_cy + name_surf.get_height() + 1)))

    def _draw_corner_tile(self, surf: pygame.Surface, rect: pygame.Rect, tile: Tile, pos: int) -> None:
        draw_bevel_rect(surf, rect, C_CORNER_BG, bevel=4, radius=4)
        pygame.draw.rect(surf, C_BOARD_BORDER, rect, width=2, border_radius=4)

        cx, cy = rect.centerx, rect.centery
        f_top = get_font(max(9, rect.width // 9), bold=True)
        f_sub = get_font(max(7, rect.width // 11))

        if pos == 0:
            col, top, sub = C_SUCCESS, "MULAI", "Gaji Rp2Jt"
            pygame.draw.circle(surf, col, (cx, cy), rect.width // 5, width=3)
        elif pos == 10:
            col, top, sub = (100, 115, 130), "PENJARA", "Kunjungan"
            for bar_i in range(3):
                bx2 = cx - rect.width // 4 + bar_i * rect.width // 6
                pygame.draw.line(surf, (80, 90, 110), (bx2, cy - rect.height // 4), (bx2, cy + rect.height // 4), 3)
        elif pos == 20:
            col, top, sub = C_GOLD, "PARKIR", "GRATIS"
            car_rect = pygame.Rect(cx - rect.width // 4, cy - 4, rect.width // 2, rect.height // 6)
            pygame.draw.rect(surf, (180, 200, 220), car_rect, border_radius=3)
        else:  # 30
            col, top, sub = C_DANGER, "MASUK", "PENJARA!"
            pygame.draw.line(surf, col, (cx + rect.width // 4, cy - rect.height // 4), (cx - rect.width // 5, cy + rect.height // 5), 3)

        top_s = f_top.render(top, True, col)
        sub_s = f_sub.render(sub, True, C_TEXT_MED)
        surf.blit(top_s, top_s.get_rect(center=(cx, cy - top_s.get_height() // 2 - 2)))
        surf.blit(sub_s, sub_s.get_rect(center=(cx, cy + sub_s.get_height() // 2 + 2)))

    def _draw_dynamic_tile_overlay(self, surface: pygame.Surface, rect: pygame.Rect, tile: Tile, pos: int, engine: GameEngine) -> None:
        stripe_thick = int(min(rect.width, rect.height) * 0.30)
        side = _TILE_SIDE.get(pos, "bottom")

        # Ownership tag
        if tile.owner_id is not None:
            owner = engine.get_player(tile.owner_id)
            if owner:
                badge_pos = (rect.right - 8, rect.bottom - 8) if side in ("bottom", "right") else (rect.right - 8, rect.y + 8)
                pygame.draw.circle(surface, owner.color, badge_pos, 5)
                pygame.draw.circle(surface, (255, 255, 255), badge_pos, 5, width=1)

        # Mortgage tag
        if tile.is_mortgaged:
            m_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            m_surf.fill((200, 50, 50, 85))
            surface.blit(m_surf, rect.topleft)
            f_m = get_font(max(7, min(10, rect.width // 7)), bold=True)
            m_txt = f_m.render("GADAI", True, (255, 220, 220))
            pygame.draw.rect(surface, (160, 30, 30), m_txt.get_rect(center=rect.center).inflate(6, 3), border_radius=3)
            surface.blit(m_txt, m_txt.get_rect(center=rect.center))
            return

        # 3D Buildings
        if not tile.is_mortgaged and tile.color_group:
            if side == "bottom":
                bld_rect = pygame.Rect(rect.x, rect.y, rect.width, stripe_thick)
            elif side == "top":
                bld_rect = pygame.Rect(rect.x, rect.bottom - stripe_thick, rect.width, stripe_thick)
            elif side == "left":
                bld_rect = pygame.Rect(rect.right - stripe_thick, rect.y, stripe_thick, rect.height)
            else:
                bld_rect = pygame.Rect(rect.x, rect.y, stripe_thick, rect.height)

            if tile.hotels > 0:
                s = min(bld_rect.width, bld_rect.height) // 2 - 1
                draw_hotel_sprite(surface, bld_rect.centerx, bld_rect.centery, max(4, s))
            elif tile.houses > 0:
                count = tile.houses
                house_s = max(3, min(bld_rect.width, bld_rect.height) // 3)
                if side in ("bottom", "top"):
                    total_w = count * (house_s * 2 + 2) - 2
                    start_x = bld_rect.centerx - total_w // 2
                    for hi in range(count):
                        hx = start_x + hi * (house_s * 2 + 2) + house_s
                        draw_house_sprite(surface, hx, bld_rect.centery, house_s, (60, 180, 100))
                else:
                    total_h = count * (house_s * 2 + 2) - 2
                    start_y = bld_rect.centery - total_h // 2
                    for hi in range(count):
                        hy = start_y + hi * (house_s * 2 + 2) + house_s
                        draw_house_sprite(surface, bld_rect.centerx, hy, house_s, (60, 180, 100))

    def _draw_tokens(self, surface: pygame.Surface, engine: GameEngine, animated_positions=None, bx: int = 0, by: int = 0) -> None:
        tiles_players: Dict[int, List] = {}
        for p in engine.active_players:
            pos = animated_positions[p.id] if (animated_positions and p.id in animated_positions) else p.position
            tiles_players.setdefault(pos, []).append(p)

        for pos, players in tiles_players.items():
            rect = self.tile_rects.get(pos)
            if not rect:
                continue

            count = len(players)
            # Relative to board buffer
            cx, cy = rect.centerx - bx, rect.centery - by

            offsets = [(0, 0)]
            if count == 2:   offsets = [(-9, 0), (9, 0)]
            elif count == 3: offsets = [(-9, -7), (9, -7), (0, 9)]
            elif count == 4: offsets = [(-9, -9), (9, -9), (-9, 9), (9, 9)]

            for idx, p in enumerate(players):
                ox, oy = offsets[idx]
                tx, ty = cx + ox, cy + oy
                is_active = (engine.current_player and p.id == engine.current_player.id)
                token_type = getattr(p, "token_type", "monas")
                token_r = max(8, min(14, int(min(rect.width, rect.height) * 0.28)))
                TokenRenderer.draw_token(
                    surface, token_type, (tx, ty),
                    radius=token_r, color=p.color, is_active=is_active,
                    anim_time=self._anim_time
                )

    def _draw_board_center(self, surface: pygame.Surface, engine: GameEngine, dice_anim=None, bx: int = 0, by: int = 0) -> None:
        bsize = self.board_rect.width
        border_thick = max(10, int(bsize * 0.024))
        inner_size = bsize - 2 * border_thick

        corner_size = int(inner_size * 0.138)
        edge_w = (inner_size - 2 * corner_size) / 9.0
        center_size = inner_size - 2 * corner_size - 2 * int(edge_w)

        cx = border_thick + corner_size + int(edge_w) + center_size // 2
        cy = border_thick + corner_size + int(edge_w) + center_size // 2
        half = center_size // 2

        # Center parchment background
        center_rect = pygame.Rect(cx - half, cy - half, center_size, center_size)
        center_surf = pygame.Surface((center_size, center_size), pygame.SRCALPHA)
        for yi in range(center_size):
            t = yi / center_size
            col = lerp_color((245, 230, 185), (235, 215, 165), t)
            pygame.draw.line(center_surf, col, (0, yi), (center_size, yi))

        inner_bdr = pygame.Rect(4, 4, center_size - 8, center_size - 8)
        pygame.draw.rect(center_surf, (160, 120, 55, 180), inner_bdr, width=2, border_radius=6)
        self._draw_archipelago(center_surf, center_size // 2, center_size // 2, center_size)
        surface.blit(center_surf, center_rect.topleft)

        # Title
        f_sub  = get_font(max(10, center_size // 18), bold=True)
        f_main = get_font(max(14, center_size // 11), bold=True)
        sub_s  = f_sub.render("NUSANTARA", True, (140, 90, 30))
        main_s = f_main.render("PROPERTY TYCOON", True, (80, 50, 15))
        surface.blit(sub_s,  sub_s.get_rect(center=(cx, cy - half // 2 + 5)))
        surface.blit(main_s, main_s.get_rect(center=(cx, cy - half // 2 + sub_s.get_height() + 8)))

        # Dice view
        dice_y = cy + half // 6
        self._draw_premium_dice(surface, cx - 28, dice_y, dice_anim, engine)

        # Double indicator
        if engine.dice.is_double and engine.has_rolled and not (dice_anim and dice_anim.is_active):
            f_dbl = get_font(max(9, center_size // 22), bold=True)
            d_s = f_dbl.render("✦ Dadu Kembar! Giliran Tambahan ✦", True, C_GOLD)
            surface.blit(d_s, d_s.get_rect(center=(cx, dice_y + 45)))

    def _draw_archipelago(self, surf: pygame.Surface, cx: int, cy: int, size: int) -> None:
        gold_land = (210, 175, 105, 160)
        gold_border = (165, 130, 65, 200)
        s = size // 2

        # Draw islands with land fill and delicate coastline border
        islands = [
            pygame.Rect(cx - s * 4 // 5, cy - s * 3 // 5, s * 3 // 4, s // 3),   # Sumatra
            pygame.Rect(cx - s // 4, cy - s // 6, s * 3 // 5, s // 5),           # Java
            pygame.Rect(cx + s // 12, cy - s * 2 // 3, s * 2 // 5, s // 2),      # Kalimantan
            pygame.Rect(cx + s * 2 // 5, cy - s // 2, s // 4, s * 3 // 8),       # Sulawesi
            pygame.Rect(cx + s * 3 // 5, cy - s // 4, s * 2 // 7, s // 3),       # Papua
            pygame.Rect(cx + s // 8, cy + s // 10, s // 7, s // 8),              # Bali/Lombok
        ]

        for r in islands:
            pygame.draw.ellipse(surf, gold_land, r)
            pygame.draw.ellipse(surf, gold_border, r, width=1)

        # Maluku archipelago dots
        for xi in range(4):
            m_pos = (cx + s * 2 // 5 + xi * 10, cy + s // 10 + (xi % 2) * 6)
            pygame.draw.circle(surf, gold_land, m_pos, 4)
            pygame.draw.circle(surf, gold_border, m_pos, 4, width=1)

    def _draw_premium_dice(self, surface: pygame.Surface, left_x: int, cy: int, dice_anim, engine: GameEngine) -> None:
        d1 = dice_anim.face1 if (dice_anim and dice_anim.is_active) else engine.dice.dice1
        d2 = dice_anim.face2 if (dice_anim and dice_anim.is_active) else engine.dice.dice2
        is_rolling = dice_anim and dice_anim.is_active

        shake_x, shake_y = 0, 0
        bounce_y = 0
        if is_rolling:
            shake_x = int(math.sin(self._anim_time * 24) * 3)
            bounce_y = int(getattr(dice_anim, "bounce_y", 0.0))

        # Dice width 46
        self._draw_single_die(surface, left_x - 12 + shake_x, cy + bounce_y, d1, is_rolling)
        self._draw_single_die(surface, left_x + 40 + shake_x, cy + bounce_y, d2, is_rolling)

    def _draw_single_die(self, surface: pygame.Surface, x: int, cy: int, value: int, rolling: bool) -> None:
        size = 46
        rect = pygame.Rect(x, cy - size // 2, size, size)

        # Drop shadow (scales with bounce)
        shadow_surf = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 75), (0, 0, size + 8, size + 8), border_radius=10)
        surface.blit(shadow_surf, (rect.x - 3, rect.y + 4))

        die_col = (255, 248, 230) if rolling else (255, 255, 255)
        pygame.draw.rect(surface, die_col, rect, border_radius=9)
        # 2.5D Top bevel highlight
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, 6), border_radius=6)
        # Bottom shadow bevel
        pygame.draw.rect(surface, (190, 195, 208), pygame.Rect(rect.x + 2, rect.bottom - 6, rect.width - 4, 4))
        # Outer border
        pygame.draw.rect(surface, (140, 155, 175), rect, width=1, border_radius=9)

        # Pips coordinates (centered on 46x46 face)
        pip_coords = {
            1: [(23, 23)],
            2: [(13, 13), (33, 33)],
            3: [(13, 13), (23, 23), (33, 33)],
            4: [(13, 13), (33, 13), (13, 33), (33, 33)],
            5: [(13, 13), (33, 13), (23, 23), (13, 33), (33, 33)],
            6: [(13, 13), (33, 13), (13, 23), (33, 23), (13, 33), (33, 33)],
        }
        pip_col = (28, 30, 42) if not rolling else (190, 45, 45)
        for px, py in pip_coords.get(value, []):
            pygame.draw.circle(surface, pip_col, (rect.x + px, rect.y + py), 5)
            # Specular pip highlight
            pygame.draw.circle(surface, (95, 100, 115) if not rolling else (230, 110, 110), (rect.x + px - 1, rect.y + py - 1), 2)
