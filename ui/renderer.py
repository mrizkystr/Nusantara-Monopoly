"""Polished, modern board, tile, token, and sidebar renderer."""
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

# Cohesive Palette (Section 2)
COLOR_BG = (20, 32, 43)              # #14202B
COLOR_SURFACE = (32, 50, 65)         # #203241
COLOR_SURFACE_LIGHT = (43, 64, 80)   # #2B4050
COLOR_ACCENT_GOLD = (232, 184, 109)  # #E8B86D
COLOR_ACCENT_TEAL = (95, 179, 162)   # #5FB3A2
COLOR_TEXT_PRIMARY = (248, 245, 238) # #F8F5EE
COLOR_TEXT_SECONDARY = (184, 198, 204) # #B8C6CC
COLOR_DANGER = (217, 108, 108)       # #D96C6C
COLOR_SUCCESS = (101, 189, 139)      # #65BD8B

COLOR_TILE_BG = (245, 247, 250)
COLOR_TILE_BORDER = (55, 75, 95)

GROUP_COLORS = {
    PropertyColorGroup.BROWN: (140, 70, 30),
    PropertyColorGroup.LIGHT_BLUE: (115, 190, 235),
    PropertyColorGroup.PINK: (230, 95, 160),
    PropertyColorGroup.ORANGE: (245, 135, 30),
    PropertyColorGroup.RED: (225, 45, 45),
    PropertyColorGroup.YELLOW: (245, 210, 25),
    PropertyColorGroup.GREEN: (35, 155, 60),
    PropertyColorGroup.DARK_BLUE: (25, 65, 165)
}


class BoardRenderer:
    def __init__(self):
        self.tile_rects: Dict[int, pygame.Rect] = {}
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self.log_box = LogBox(pygame.Rect(0, 0, 0, 0))
        self._cached_board_surf: Optional[pygame.Surface] = None
        self._last_board_size: int = 0
        self.hovered_tile: Optional[int] = None

    def update_layout(self, screen_w: int, screen_h: int) -> None:
        """Calculate responsive positions for board and sidebar."""
        margin = 16
        sidebar_w = max(340, min(420, int(screen_w * 0.28)))
        board_max_w = screen_w - sidebar_w - (margin * 3)
        board_max_h = screen_h - (margin * 2)
        board_size = min(board_max_w, board_max_h)

        self.board_rect = pygame.Rect(margin, margin, board_size, board_size)
        self.sidebar_rect = pygame.Rect(
            self.board_rect.right + margin,
            margin,
            screen_w - self.board_rect.right - (margin * 2),
            board_size
        )

        # Update log box in sidebar bottom
        log_h = max(130, int(self.sidebar_rect.height * 0.26))
        self.log_box.rect = pygame.Rect(
            self.sidebar_rect.x + 12,
            self.sidebar_rect.bottom - log_h - 12,
            self.sidebar_rect.width - 24,
            log_h
        )

        # Invalidate cached surface if size changed
        if board_size != self._last_board_size:
            self._cached_board_surf = None
            self._last_board_size = board_size

        # Calculate perimeter tile rects
        bx, by, bsize = self.board_rect.x, self.board_rect.y, self.board_rect.width
        corner_size = int(bsize * 0.135)
        edge_w = (bsize - 2 * corner_size) / 9.0

        self.tile_rects.clear()

        # Pos 0: Bottom-Right corner (MULAI)
        self.tile_rects[0] = pygame.Rect(bx + bsize - corner_size, by + bsize - corner_size, corner_size, corner_size)

        # Pos 1..9: Bottom edge (Right to Left)
        for i in range(1, 10):
            x = bx + bsize - corner_size - int(i * edge_w)
            w = int((bx + bsize - corner_size - int((i - 1) * edge_w)) - x)
            self.tile_rects[i] = pygame.Rect(x, by + bsize - corner_size, w, corner_size)

        # Pos 10: Bottom-Left corner (PENJARA)
        self.tile_rects[10] = pygame.Rect(bx, by + bsize - corner_size, corner_size, corner_size)

        # Pos 11..19: Left edge (Bottom to Top)
        for i in range(1, 10):
            pos = 10 + i
            y = by + bsize - corner_size - int(i * edge_w)
            h = int((by + bsize - corner_size - int((i - 1) * edge_w)) - y)
            self.tile_rects[pos] = pygame.Rect(bx, y, corner_size, h)

        # Pos 20: Top-Left corner (PARKIR GRATIS)
        self.tile_rects[20] = pygame.Rect(bx, by, corner_size, corner_size)

        # Pos 21..29: Top edge (Left to Right)
        for i in range(1, 10):
            pos = 20 + i
            x = bx + corner_size + int((i - 1) * edge_w)
            w = int((bx + corner_size + int(i * edge_w)) - x)
            self.tile_rects[pos] = pygame.Rect(x, by, w, corner_size)

        # Pos 30: Top-Right corner (MASUK PENJARA)
        self.tile_rects[30] = pygame.Rect(bx + bsize - corner_size, by, corner_size, corner_size)

        # Pos 31..39: Right edge (Top to Bottom)
        for i in range(1, 10):
            pos = 30 + i
            y = by + corner_size + int((i - 1) * edge_w)
            h = int((by + corner_size + int(i * edge_w)) - y)
            self.tile_rects[pos] = pygame.Rect(bx + bsize - corner_size, y, corner_size, h)

    def get_tile_at_pos(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Return the board position (0-39) clicked by the mouse, if any."""
        for pos, rect in self.tile_rects.items():
            if rect.collidepoint(mouse_pos):
                return pos
        return None

    def draw(
        self,
        surface: pygame.Surface,
        engine: GameEngine,
        animated_positions: Optional[Dict[int, int]] = None,
        dice_anim=None,
        active_dest_tile: Optional[int] = None
    ) -> None:
        """Render board, static cached tiles, dynamic overlays, tokens, center, and sidebar."""
        surface.fill(COLOR_BG)

        # Render or blit cached static board
        if self._cached_board_surf is None:
            self._render_static_board(engine.board)

        surface.blit(self._cached_board_surf, self.board_rect.topleft)

        # Draw dynamic destination highlight pulse (if player is moving)
        if active_dest_tile is not None and active_dest_tile in self.tile_rects:
            d_rect = self.tile_rects[active_dest_tile]
            pulse_surf = pygame.Surface((d_rect.width, d_rect.height), pygame.SRCALPHA)
            pulse_surf.fill((232, 184, 109, 80))
            surface.blit(pulse_surf, d_rect.topleft)
            pygame.draw.rect(surface, COLOR_ACCENT_GOLD, d_rect, width=3)

        # Draw tile hover outline
        if self.hovered_tile is not None and self.hovered_tile in self.tile_rects:
            h_rect = self.tile_rects[self.hovered_tile]
            pygame.draw.rect(surface, (255, 255, 255, 120), h_rect, width=2)

        # Draw dynamic tile states (ownership tags, mortgage, houses/hotels)
        for pos in range(40):
            rect = self.tile_rects[pos]
            tile = engine.board.get_tile(pos)
            if tile:
                self._draw_dynamic_tile_overlay(surface, rect, tile, pos, engine)

        # Draw player tokens
        self._draw_tokens(surface, engine, animated_positions=animated_positions)

        # Draw board center
        self._draw_board_center(surface, engine, dice_anim=dice_anim)

        # Draw sidebar
        self._draw_sidebar(surface, engine)

    def _render_static_board(self, board: Board) -> None:
        """Cache static 40-tile board graphics to improve frame rate to solid 60 FPS."""
        bsize = self.board_rect.width
        self._cached_board_surf = pygame.Surface((bsize, bsize), pygame.SRCALPHA)

        # Board background surface
        local_rect = pygame.Rect(0, 0, bsize, bsize)
        pygame.draw.rect(self._cached_board_surf, COLOR_SURFACE, local_rect, border_radius=12)
        pygame.draw.rect(self._cached_board_surf, (50, 70, 95), local_rect, width=2, border_radius=12)

        # Draw all static tiles relative to (0, 0)
        bx, by = self.board_rect.x, self.board_rect.y
        for pos in range(40):
            global_rect = self.tile_rects[pos]
            tile_rect = pygame.Rect(global_rect.x - bx, global_rect.y - by, global_rect.width, global_rect.height)
            tile = board.get_tile(pos)
            if tile:
                self._draw_static_tile(self._cached_board_surf, tile_rect, tile, pos)

    def _draw_static_tile(self, surf: pygame.Surface, rect: pygame.Rect, tile: Tile, pos: int) -> None:
        """Render unchanging tile background, labels, and color stripes."""
        pygame.draw.rect(surf, COLOR_TILE_BG, rect)
        pygame.draw.rect(surf, COLOR_TILE_BORDER, rect, width=1)

        # Corner tiles
        if tile.type == TileType.GO:
            self._draw_corner(surf, rect, "MULAI", "Gaji Rp2Jt", COLOR_SUCCESS)
            return
        elif tile.type == TileType.JAIL:
            self._draw_corner(surf, rect, "PENJARA", "Kunjungan", (120, 135, 150))
            return
        elif tile.type == TileType.FREE_PARKING:
            self._draw_corner(surf, rect, "PARKIR", "GRATIS", COLOR_ACCENT_GOLD)
            return
        elif tile.type == TileType.GO_TO_JAIL:
            self._draw_corner(surf, rect, "MASUK", "PENJARA", COLOR_DANGER)
            return

        # Edge stripes
        stripe_h = 16
        stripe_rect = None
        if 1 <= pos <= 9:
            stripe_rect = pygame.Rect(rect.x, rect.y, rect.width, stripe_h)
        elif 11 <= pos <= 19:
            stripe_rect = pygame.Rect(rect.right - stripe_h, rect.y, stripe_h, rect.height)
        elif 21 <= pos <= 29:
            stripe_rect = pygame.Rect(rect.x, rect.bottom - stripe_h, rect.width, stripe_h)
        elif 31 <= pos <= 39:
            stripe_rect = pygame.Rect(rect.x, rect.y, stripe_h, rect.height)

        if tile.color_group and stripe_rect:
            col = GROUP_COLORS.get(tile.color_group, (100, 100, 100))
            pygame.draw.rect(surf, col, stripe_rect)
            pygame.draw.rect(surf, (30, 40, 50), stripe_rect, width=1)

        # Special tiles icons & titles
        if tile.type in (TileType.CHANCE, TileType.COMMUNITY_CHEST, TileType.TAX, TileType.TRANSPORT, TileType.UTILITY):
            sym, col = "?", COLOR_ACCENT_GOLD
            if tile.type == TileType.COMMUNITY_CHEST:
                sym, col = "$", COLOR_ACCENT_TEAL
            elif tile.type == TileType.TAX:
                sym, col = "%", (170, 110, 200)
            elif tile.type == TileType.TRANSPORT:
                sym, col = "TRAIN", (70, 90, 115)
            elif tile.type == TileType.UTILITY:
                sym, col = "POWER", (46, 175, 145)

            f_sym = get_font(12, bold=True)
            f_title = get_font(9, bold=True)

            surf.blit(f_sym.render(sym, True, col), f_sym.render(sym, True, col).get_rect(center=(rect.centerx, rect.centery - 8)))
            surf.blit(f_title.render(tile.name[:10], True, (35, 45, 55)), f_title.render(tile.name[:10], True, (35, 45, 55)).get_rect(center=(rect.centerx, rect.centery + 8)))

            if tile.purchase_price > 0:
                f_p = get_font(8)
                p_s = f_p.render(f"Rp{tile.purchase_price // 1000}rb", True, (90, 105, 120))
                surf.blit(p_s, p_s.get_rect(center=(rect.centerx, rect.bottom - 10)))
            return

        # Property City Title
        f_name = get_font(11, bold=True)
        t_s = f_name.render(tile.name, True, (25, 35, 45))
        cy = rect.centery + 6 if (1 <= pos <= 9) else (rect.centery - 6 if 21 <= pos <= 29 else rect.centery)
        surf.blit(t_s, t_s.get_rect(center=(rect.centerx, cy)))

        # Property Price Tag
        if tile.purchase_price > 0:
            f_p = get_font(9)
            p_s = f_p.render(f"Rp{tile.purchase_price // 1000}rb", True, (90, 105, 120))
            py = rect.bottom - 12 if (1 <= pos <= 9 or 11 <= pos <= 19 or 31 <= pos <= 39) else rect.top + 4
            surf.blit(p_s, p_s.get_rect(center=(rect.centerx, py)))

    def _draw_dynamic_tile_overlay(self, surface: pygame.Surface, rect: pygame.Rect, tile: Tile, pos: int, engine: GameEngine) -> None:
        """Render ownership tags, mortgages, and houses/hotels on top of cached tiles."""
        # Ownership badge
        if tile.owner_id is not None:
            owner = engine.get_player(tile.owner_id)
            if owner:
                tag_pos = (rect.x + 8, rect.y + 8)
                pygame.draw.circle(surface, owner.color, tag_pos, 5)
                pygame.draw.circle(surface, (255, 255, 255), tag_pos, 5, width=1)

        # Mortgage tag
        if tile.is_mortgaged:
            m_surf = pygame.Surface((rect.width - 4, rect.height - 4), pygame.SRCALPHA)
            m_surf.fill((217, 108, 108, 110))
            surface.blit(m_surf, (rect.x + 2, rect.y + 2))
            f_m = get_font(10, bold=True)
            txt_m = f_m.render("TERGADAI", True, (255, 255, 255))
            pygame.draw.rect(surface, (180, 40, 40), txt_m.get_rect(center=rect.center).inflate(6, 2), border_radius=2)
            surface.blit(txt_m, txt_m.get_rect(center=rect.center))

        # Houses & Hotel
        stripe_rect = None
        stripe_h = 16
        if 1 <= pos <= 9:
            stripe_rect = pygame.Rect(rect.x, rect.y, rect.width, stripe_h)
        elif 11 <= pos <= 19:
            stripe_rect = pygame.Rect(rect.right - stripe_h, rect.y, stripe_h, rect.height)
        elif 21 <= pos <= 29:
            stripe_rect = pygame.Rect(rect.x, rect.bottom - stripe_h, rect.width, stripe_h)
        elif 31 <= pos <= 39:
            stripe_rect = pygame.Rect(rect.x, rect.y, stripe_h, rect.height)

        if stripe_rect and not tile.is_mortgaged:
            if tile.hotels > 0:
                h_rect = pygame.Rect(0, 0, 18, 10)
                h_rect.center = stripe_rect.center
                pygame.draw.rect(surface, (220, 40, 40), h_rect, border_radius=2)
                pygame.draw.rect(surface, (255, 215, 0), h_rect, width=1, border_radius=2)
            elif tile.houses > 0:
                total_w = tile.houses * 10
                start_x = stripe_rect.centerx - (total_w // 2)
                for h in range(tile.houses):
                    hx = start_x + (h * 10)
                    hy = stripe_rect.centery - 4
                    pygame.draw.rect(surface, (46, 204, 113), (hx, hy, 8, 8), border_radius=1)
                    pygame.draw.rect(surface, (255, 255, 255), (hx, hy, 8, 8), width=1, border_radius=1)

    def _draw_corner(self, surf: pygame.Surface, rect: pygame.Rect, top_txt: str, sub_txt: str, color: Tuple[int, int, int]) -> None:
        inner = rect.inflate(-6, -6)
        pygame.draw.rect(surf, (240, 245, 250), inner, border_radius=8)
        pygame.draw.rect(surf, color, inner, width=2, border_radius=8)

        f_top = get_font(13, bold=True)
        f_sub = get_font(10)
        t_s = f_top.render(top_txt, True, color)
        s_s = f_sub.render(sub_txt, True, (60, 75, 90))

        surf.blit(t_s, t_s.get_rect(center=(rect.centerx, rect.centery - 8)))
        surf.blit(s_s, s_s.get_rect(center=(rect.centerx, rect.centery + 10)))

    def _draw_tokens(self, surface: pygame.Surface, engine: GameEngine, animated_positions: Optional[Dict[int, int]] = None) -> None:
        """Render distinct vector tokens with offset when sharing a tile."""
        tiles_players: Dict[int, List[Player]] = {}
        for p in engine.active_players:
            # Use animated tile position if actively stepping
            pos = animated_positions[p.id] if (animated_positions and p.id in animated_positions) else p.position
            tiles_players.setdefault(pos, []).append(p)

        for pos, players in tiles_players.items():
            rect = self.tile_rects.get(pos)
            if not rect:
                continue

            count = len(players)
            cx, cy = rect.centerx, rect.centery
            offsets = [(0, 0)]
            if count == 2:
                offsets = [(-10, 0), (10, 0)]
            elif count == 3:
                offsets = [(-10, -8), (10, -8), (0, 10)]
            elif count == 4:
                offsets = [(-10, -10), (10, -10), (-10, 10), (10, 10)]

            for idx, p in enumerate(players):
                ox, oy = offsets[idx]
                tx, ty = cx + ox, cy + oy
                is_active = (engine.current_player and p.id == engine.current_player.id)
                token_type = getattr(p, "token_type", "monas")
                TokenRenderer.draw_token(surface, token_type, (tx, ty), radius=10, color=p.color, is_active=is_active)

    def _draw_board_center(self, surface: pygame.Surface, engine: GameEngine, dice_anim=None) -> None:
        """Draw logo, current player banner, and dice in center of board."""
        bx, by, bsize = self.board_rect.x, self.board_rect.y, self.board_rect.width
        center_x, center_y = bx + (bsize // 2), by + (bsize // 2)

        # Title
        f_sub = get_font(14, bold=True)
        f_main = get_font(26, bold=True)
        sub_s = f_sub.render("NUSANTARA", True, COLOR_ACCENT_GOLD)
        main_s = f_main.render("PROPERTY TYCOON", True, COLOR_TEXT_PRIMARY)
        surface.blit(sub_s, sub_s.get_rect(center=(center_x, center_y - 85)))
        surface.blit(main_s, main_s.get_rect(center=(center_x, center_y - 60)))

        # Current player badge
        cp = engine.current_player
        if cp:
            f_turn = get_font(16, bold=True)
            turn_txt = f"Giliran: {cp.name}"
            t_s = f_turn.render(turn_txt, True, cp.color)
            surface.blit(t_s, t_s.get_rect(center=(center_x, center_y - 20)))

        # Dice view (animated or static)
        d1 = dice_anim.face1 if (dice_anim and dice_anim.is_active) else engine.dice.dice1
        d2 = dice_anim.face2 if (dice_anim and dice_anim.is_active) else engine.dice.dice2

        self._draw_die(surface, center_x - 38, center_y + 10, d1)
        self._draw_die(surface, center_x + 6, center_y + 10, d2)

        # Double roll indicator
        if engine.dice.is_double and engine.has_rolled and not (dice_anim and dice_anim.is_active):
            f_dbl = get_font(13, bold=True)
            d_s = f_dbl.render("Dadu Kembar! Giliran Tambahan", True, COLOR_ACCENT_GOLD)
            surface.blit(d_s, d_s.get_rect(center=(center_x, center_y + 60)))

    def _draw_die(self, surface: pygame.Surface, x: int, y: int, value: int) -> None:
        """Render a shaded 32x32 die with rounded bevels."""
        rect = pygame.Rect(x, y, 32, 32)
        # Drop shadow
        pygame.draw.rect(surface, (10, 15, 20), rect.move(2, 2), border_radius=6)
        # Die body
        pygame.draw.rect(surface, (250, 252, 255), rect, border_radius=6)
        pygame.draw.rect(surface, (180, 195, 210), rect, width=2, border_radius=6)

        pip_coords = {
            1: [(16, 16)],
            2: [(9, 9), (23, 23)],
            3: [(9, 9), (16, 16), (23, 23)],
            4: [(9, 9), (23, 9), (9, 23), (23, 23)],
            5: [(9, 9), (23, 9), (16, 16), (9, 23), (23, 23)],
            6: [(9, 9), (23, 9), (9, 16), (23, 16), (9, 23), (23, 23)]
        }
        for px, py in pip_coords.get(value, []):
            pygame.draw.circle(surface, (30, 40, 50), (x + px, y + py), 3)

    def _draw_sidebar(self, surface: pygame.Surface, engine: GameEngine) -> None:
        """Render player list and event log in the sidebar with the new modern theme."""
        pygame.draw.rect(surface, COLOR_SURFACE, self.sidebar_rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_SURFACE_LIGHT, self.sidebar_rect, width=1, border_radius=10)

        f_h = get_font(15, bold=True)
        h_s = f_h.render("STATUS KONGLOMERAT", True, COLOR_ACCENT_GOLD)
        surface.blit(h_s, (self.sidebar_rect.x + 16, self.sidebar_rect.y + 14))

        card_y = self.sidebar_rect.y + 40
        card_h = 70
        for p in engine.players:
            is_active = (engine.current_player and p.id == engine.current_player.id)
            c_rect = pygame.Rect(self.sidebar_rect.x + 12, card_y, self.sidebar_rect.width - 24, card_h)

            bg_col = COLOR_SURFACE_LIGHT if is_active else (25, 40, 52)
            pygame.draw.rect(surface, bg_col, c_rect, border_radius=8)
            if is_active:
                pygame.draw.rect(surface, COLOR_ACCENT_GOLD, c_rect, width=2, border_radius=8)

            # Player Token Preview
            token_type = getattr(p, "token_type", "monas")
            TokenRenderer.draw_token(surface, token_type, (c_rect.x + 22, c_rect.y + 24), radius=12, color=p.color, is_active=is_active)

            # Name and Status
            f_name = get_font(14, bold=True)
            status_tag = ""
            if p.is_bankrupt:
                status_tag = " (PAILIT)"
            elif p.in_jail:
                status_tag = f" (PENJARA {p.jail_turns}/3)"

            n_s = f_name.render(f"{p.name}{status_tag}", True, COLOR_TEXT_PRIMARY if not p.is_bankrupt else (120, 130, 140))
            surface.blit(n_s, (c_rect.x + 44, c_rect.y + 12))

            # Cash and Net Worth
            f_info = get_font(12)
            c_txt = f"Kas: {format_rupiah(p.cash)}"
            pr_txt = f"Aset: {len(p.properties)} Petak"
            c_s = f_info.render(c_txt, True, COLOR_SUCCESS if p.cash > 0 else COLOR_DANGER)
            pr_s = f_info.render(pr_txt, True, COLOR_TEXT_SECONDARY)
            surface.blit(c_s, (c_rect.x + 44, c_rect.y + 36))
            surface.blit(pr_s, (c_rect.x + 190, c_rect.y + 36))

            card_y += card_h + 8

        # Draw Event Log
        f_log_lbl = get_font(13, bold=True)
        lbl_s = f_log_lbl.render("CATATAN AKTIVITAS", True, COLOR_ACCENT_TEAL)
        surface.blit(lbl_s, (self.sidebar_rect.x + 14, self.log_box.rect.y - 22))
        self.log_box.draw(surface, engine.event_log)
