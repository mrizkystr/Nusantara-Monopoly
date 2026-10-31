"""
Modern Mobile-Style HUD for Nusantara Property Tycoon.
Features:
- Top Bar: Turn count, Active Player Card, Compact Opponent Avatars, Settings & Camera toggle.
- Bottom Action Dock: Large Glowing Dice Button, Contextual Actions, Action Status Banner.
- Floating Mini Activity Ticker (collapsible).
"""
import math
import pygame
from typing import List, Dict, Optional, Tuple, Callable
from game.state import GameState
from game.engine import GameEngine
from game.player import Player
from game.economy import format_rupiah
from ui.components import Button, get_font
from ui.tokens import TokenRenderer
from ui.visual_assets import (
    C_GOLD, C_GOLD_LIGHT, C_TEAL, C_TEXT_LIGHT, C_TEXT_MED,
    C_SUCCESS, C_DANGER, C_SURFACE, C_SURFACE_LIGHT,
    draw_rounded_rect_with_shadow, draw_bevel_rect
)


class ModernHUD:
    """Modern casual-mobile game HUD replacing the traditional desktop sidebar."""

    def __init__(
        self,
        on_roll_dice: Callable[[], None],
        on_end_turn: Callable[[], None],
        on_manage_assets: Callable[[], None],
        on_trade: Callable[[], None],
        on_save: Callable[[], None],
        on_settings: Callable[[], None],
        on_toggle_camera: Callable[[], None],
        on_main_menu: Callable[[], None],
    ):
        self.on_roll_dice = on_roll_dice
        self.on_end_turn = on_end_turn
        self.on_manage_assets = on_manage_assets
        self.on_trade = on_trade
        self.on_save = on_save
        self.on_settings = on_settings
        self.on_toggle_camera = on_toggle_camera
        self.on_main_menu = on_main_menu

        # Buttons collections
        self.top_buttons: List[Button] = []
        self.dock_buttons: List[Button] = []
        self.all_buttons: List[Button] = []

        # Layout rects
        self.top_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.bottom_dock_rect = pygame.Rect(0, 0, 0, 0)
        self.ticker_rect = pygame.Rect(0, 0, 0, 0)

        # Smooth animated cash values for players: {player_id: displayed_cash_float}
        self.displayed_cash: Dict[int, float] = {}

        # Log expansion state
        self.is_log_expanded: bool = False
        self.anim_time: float = 0.0

    def update(self, dt: float, engine: GameEngine) -> None:
        self.anim_time += dt

        # Smoothly interpolate displayed cash towards authoritative cash
        for p in engine.players:
            if p.id not in self.displayed_cash:
                self.displayed_cash[p.id] = float(p.cash)
            else:
                target = float(p.cash)
                diff = target - self.displayed_cash[p.id]
                if abs(diff) < 500:
                    self.displayed_cash[p.id] = target
                else:
                    self.displayed_cash[p.id] += diff * min(1.0, dt * 7.0)

    def update_layout(self, screen_w: int, screen_h: int, engine: GameEngine, is_overview: bool = True) -> None:
        """Construct top bar and bottom dock buttons based on screen size and game state."""
        self.top_buttons.clear()
        self.dock_buttons.clear()
        self.all_buttons.clear()

        margin = 12
        top_h = 68
        self.top_bar_rect = pygame.Rect(margin, margin, screen_w - margin * 2, top_h)

        # Bottom Dock: centered at bottom of screen
        dock_w = min(880, screen_w - margin * 2)
        dock_h = 100
        dock_x = (screen_w - dock_w) // 2
        dock_y = screen_h - dock_h - margin
        self.bottom_dock_rect = pygame.Rect(dock_x, dock_y, dock_w, dock_h)

        # Floating Activity Ticker: bottom-left
        ticker_w = min(360, (screen_w - dock_w) // 2 - margin * 2)
        if ticker_w < 220:
            ticker_w = 260
        ticker_h = 95
        self.ticker_rect = pygame.Rect(margin, screen_h - ticker_h - margin, ticker_w, ticker_h)

        # --- Top Bar Right Buttons ---
        cam_icon = "SEMUA" if not is_overview else "FOKUS"
        b_cam = Button(
            pygame.Rect(self.top_bar_rect.right - 210, self.top_bar_rect.y + 14, 98, 40),
            cam_icon,
            self.on_toggle_camera,
            bg_color=(45, 75, 95),
            hover_color=(60, 95, 120),
            font_size=13,
            border_radius=8
        )
        b_set = Button(
            pygame.Rect(self.top_bar_rect.right - 105, self.top_bar_rect.y + 14, 95, 40),
            "ATUR",
            self.on_settings,
            bg_color=(45, 75, 95),
            hover_color=(60, 95, 120),
            font_size=13,
            border_radius=8
        )
        self.top_buttons.extend([b_cam, b_set])

        # --- Bottom Dock Buttons ---
        st = engine.state
        can_roll = (st == GameState.WAITING_FOR_ROLL)
        can_end = (st == GameState.TURN_END)
        can_manage = (st in (GameState.WAITING_FOR_ROLL, GameState.TURN_END, GameState.DEBT_RESOLUTION))
        can_trade = (st in (GameState.WAITING_FOR_ROLL, GameState.TURN_END) and len(engine.active_players) > 1)

        # Primary Dice Button in Center
        dice_btn_w = 230
        dice_btn_h = 48
        dice_btn_x = dock_x + (dock_w - dice_btn_w) // 2
        dice_btn_y = dock_y + 42

        b_dice = Button(
            pygame.Rect(dice_btn_x, dice_btn_y, dice_btn_w, dice_btn_h),
            "LEMPAR DADU",
            self.on_roll_dice,
            bg_color=C_SUCCESS if can_roll else (60, 80, 75),
            hover_color=(85, 215, 140) if can_roll else (60, 80, 75),
            text_color=(255, 255, 255),
            font_size=17,
            border_radius=10,
            is_enabled=can_roll
        )

        # Left Contextual Buttons: Kelola Aset & Negosiasi
        b_manage = Button(
            pygame.Rect(dock_x + 16, dice_btn_y + 6, 125, 38),
            "KELOLA ASET",
            self.on_manage_assets,
            bg_color=(220, 130, 40) if can_manage else (60, 60, 70),
            hover_color=(240, 150, 60) if can_manage else (60, 60, 70),
            font_size=12,
            border_radius=8,
            is_enabled=can_manage
        )
        b_trade = Button(
            pygame.Rect(dock_x + 148, dice_btn_y + 6, 115, 38),
            "BISNIS",
            self.on_trade,
            bg_color=(140, 75, 175) if can_trade else (60, 60, 70),
            hover_color=(165, 95, 205) if can_trade else (60, 60, 70),
            font_size=12,
            border_radius=8,
            is_enabled=can_trade
        )

        # Right Contextual Buttons: Selesai Giliran & Simpan
        b_end = Button(
            pygame.Rect(dock_x + dock_w - 280, dice_btn_y + 6, 145, 38),
            "SELESAI GILIRAN",
            self.on_end_turn,
            bg_color=(45, 135, 215) if can_end else (60, 60, 70),
            hover_color=(60, 160, 245) if can_end else (60, 60, 70),
            font_size=12,
            border_radius=8,
            is_enabled=can_end
        )
        b_save = Button(
            pygame.Rect(dock_x + dock_w - 125, dice_btn_y + 6, 110, 38),
            "SIMPAN",
            self.on_save,
            bg_color=(50, 70, 85),
            hover_color=(65, 90, 110),
            font_size=12,
            border_radius=8
        )

        self.dock_buttons.extend([b_manage, b_trade, b_dice, b_end, b_save])
        self.all_buttons = self.top_buttons + self.dock_buttons

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle clicks on HUD buttons and log toggle."""
        # Toggle log expansion when clicking ticker
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ticker_rect.collidepoint(event.pos):
                self.is_log_expanded = not self.is_log_expanded
                return True

        for b in self.all_buttons:
            if b.handle_event(event):
                return True
        return False

    def draw(self, surface: pygame.Surface, engine: GameEngine) -> None:
        """Draw Top Bar, Bottom Action Dock, and Floating Ticker."""
        self._draw_top_bar(surface, engine)
        self._draw_bottom_dock(surface, engine)
        self._draw_activity_ticker(surface, engine)

    def _draw_top_bar(self, surface: pygame.Surface, engine: GameEngine) -> None:
        tb = self.top_bar_rect
        # Glassmorphic rounded top banner
        top_surf = pygame.Surface((tb.width, tb.height), pygame.SRCALPHA)
        pygame.draw.rect(top_surf, (15, 28, 38, 220), (0, 0, tb.width, tb.height), border_radius=14)
        pygame.draw.rect(top_surf, (60, 95, 120, 160), (0, 0, tb.width, tb.height), width=1, border_radius=14)
        surface.blit(top_surf, tb.topleft)

        # 1. Left side: Turn Pill
        f_turn = get_font(13, bold=True)
        turn_txt = f"PUTARAN {engine.turn_count}"
        turn_s = f_turn.render(turn_txt, True, C_GOLD)
        pill_rect = pygame.Rect(tb.x + 14, tb.y + 14, turn_s.get_width() + 20, 40)
        pygame.draw.rect(surface, (25, 45, 58), pill_rect, border_radius=8)
        pygame.draw.rect(surface, (180, 140, 50), pill_rect, width=1, border_radius=8)
        surface.blit(turn_s, turn_s.get_rect(center=pill_rect.center))

        # 2. Active Player Hero Card
        cp = engine.current_player
        hero_x = pill_rect.right + 16
        if cp:
            hero_w = 260
            hero_rect = pygame.Rect(hero_x, tb.y + 8, hero_w, tb.height - 16)
            pygame.draw.rect(surface, (22, 42, 54), hero_rect, border_radius=10)
            # Glowing active border
            pulse_gold = (232, 184, 80)
            pygame.draw.rect(surface, pulse_gold, hero_rect, width=2, border_radius=10)

            # Player Token
            tok_type = getattr(cp, "token_type", "monas")
            tok_center = (hero_rect.x + 28, hero_rect.centery)
            TokenRenderer.draw_token(surface, tok_type, tok_center, radius=18, color=cp.color, is_active=True, anim_time=self.anim_time)

            # Name and status
            f_pname = get_font(14, bold=True)
            f_pcash = get_font(15, bold=True)
            name_s = f_pname.render(cp.name, True, C_TEXT_LIGHT)
            surface.blit(name_s, (hero_rect.x + 54, hero_rect.y + 6))

            disp_cash = int(self.displayed_cash.get(cp.id, cp.cash))
            cash_s = f_pcash.render(format_rupiah(disp_cash), True, C_SUCCESS)
            surface.blit(cash_s, (hero_rect.x + 54, hero_rect.y + 26))

        # 3. Compact Opponent Avatars
        opponents = [p for p in engine.players if cp is None or p.id != cp.id]
        opp_x = hero_x + 280
        for opp in opponents:
            pill_w = 160
            opp_rect = pygame.Rect(opp_x, tb.y + 12, pill_w, 44)
            bg_col = (20, 35, 45) if not opp.is_bankrupt else (18, 22, 28)
            pygame.draw.rect(surface, bg_col, opp_rect, border_radius=8)
            pygame.draw.rect(surface, (45, 65, 80), opp_rect, width=1, border_radius=8)

            # Mini token
            tok_type = getattr(opp, "token_type", "monas")
            TokenRenderer.draw_token(surface, tok_type, (opp_rect.x + 18, opp_rect.centery), radius=12, color=opp.color, is_active=False)

            # Opponent name and cash
            f_oname = get_font(11, bold=True)
            f_ocash = get_font(11)
            status_tag = " (PAILIT)" if opp.is_bankrupt else (f" (JAIL)" if opp.in_jail else "")
            oname_s = f_oname.render(f"{opp.name[:10]}{status_tag}", True, (210, 215, 225) if not opp.is_bankrupt else (110, 115, 125))
            surface.blit(oname_s, (opp_rect.x + 36, opp_rect.y + 5))

            disp_cash = int(self.displayed_cash.get(opp.id, opp.cash))
            ocash_s = f_ocash.render(f"{format_rupiah(disp_cash)} • Aset:{len(opp.properties)}", True, (160, 185, 175) if not opp.is_bankrupt else (90, 95, 105))
            surface.blit(ocash_s, (opp_rect.x + 36, opp_rect.y + 22))

            opp_x += pill_w + 10

        # Draw Top Bar buttons
        for b in self.top_buttons:
            b.draw(surface)

    def _draw_bottom_dock(self, surface: pygame.Surface, engine: GameEngine) -> None:
        bd = self.bottom_dock_rect

        # Dock panel background with glassmorphic bevel
        dock_surf = pygame.Surface((bd.width, bd.height), pygame.SRCALPHA)
        pygame.draw.rect(dock_surf, (14, 26, 36, 230), (0, 0, bd.width, bd.height), border_radius=16)
        pygame.draw.rect(dock_surf, (55, 90, 115, 180), (0, 0, bd.width, bd.height), width=1, border_radius=16)
        surface.blit(dock_surf, bd.topleft)

        # Action Status Banner across top of dock
        status_txt = self._get_status_message(engine)
        f_stat = get_font(13, bold=True)
        stat_s = f_stat.render(status_txt, True, C_GOLD_LIGHT)
        surface.blit(stat_s, stat_s.get_rect(center=(bd.centerx, bd.y + 18)))

        # Draw dock buttons
        for b in self.dock_buttons:
            b.draw(surface)

    def _get_status_message(self, engine: GameEngine) -> str:
        st = engine.state
        cp = engine.current_player
        cp_name = cp.name if cp else "Pemain"

        if st == GameState.WAITING_FOR_ROLL:
            return f"Giliran {cp_name} — Tekan LEMPAR DADU atau SPASI untuk Melangkah"
        elif st == GameState.MOVING:
            return f"{cp_name} sedang melangkah melintasi Nusantara..."
        elif st == GameState.PROPERTY_DECISION:
            return f"{cp_name} mendarat di properti baru — Beli atau Lelang?"
        elif st == GameState.AUCTION:
            return "Lelang Terbuka Sedang Berlangsung!"
        elif st == GameState.CARD_RESOLUTION:
            return f"{cp_name} membuka kartu peristiwa Nusantara!"
        elif st == GameState.JAIL_DECISION:
            return f"{cp_name} berada di Penjara — Tentukan cara keluar!"
        elif st == GameState.DEBT_RESOLUTION:
            return f"PERINGATAN: {cp_name} harus melunasi utang atau menyatakan pailit!"
        elif st == GameState.TURN_END:
            if engine.rolled_double:
                return f"Dadu Kembar! {cp_name} berhak melempar dadu sekali lagi!"
            return f"Giliran selesai — Tekan SELESAI GILIRAN untuk mengoper dadu"
        elif st == GameState.GAME_OVER:
            winner_name = engine.winner.name if engine.winner else "Juara"
            return f"Selamat kepada {winner_name}! Menjadi Konglomerat Terhebat Nusantara!"
        return f"Nusantara Property Tycoon — Giliran {cp_name}"

    def _draw_activity_ticker(self, surface: pygame.Surface, engine: GameEngine) -> None:
        """Floating mini activity feed in bottom-left."""
        tr = self.ticker_rect

        # Ticker background
        ticker_surf = pygame.Surface((tr.width, tr.height), pygame.SRCALPHA)
        pygame.draw.rect(ticker_surf, (15, 28, 38, 200), (0, 0, tr.width, tr.height), border_radius=12)
        pygame.draw.rect(ticker_surf, (50, 80, 100, 140), (0, 0, tr.width, tr.height), width=1, border_radius=12)
        surface.blit(ticker_surf, tr.topleft)

        # Header tag
        f_lbl = get_font(10, bold=True)
        lbl_s = f_lbl.render("AKTIVITAS TERBARU (KLIK DETAIL)", True, C_TEAL)
        surface.blit(lbl_s, (tr.x + 10, tr.y + 6))

        # Recent 3 log messages
        f_log = get_font(11)
        recent = engine.event_log[-3:]
        y = tr.y + 24
        for msg in recent:
            col = (230, 235, 245)
            if "menerima" in msg.lower() or "bebas" in msg.lower():
                col = C_SUCCESS
            elif "bangkrut" in msg.lower() or "penjara" in msg.lower() or "utang" in msg.lower() or "denda" in msg.lower():
                col = C_DANGER
            elif "membeli" in msg.lower() or "lelang" in msg.lower() or "membangun" in msg.lower():
                col = C_GOLD

            # Truncate
            short = msg
            while len(short) > 6 and f_log.size(short + "...")[0] > tr.width - 20:
                short = short[:-2]
            if len(short) < len(msg):
                short += "..."

            surface.blit(f_log.render(short, True, col), (tr.x + 10, y))
            y += 22

        # Expanded Full Log Modal
        if self.is_log_expanded:
            self._draw_expanded_log_modal(surface, engine)

    def _draw_expanded_log_modal(self, surface: pygame.Surface, engine: GameEngine) -> None:
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        surface.blit(dim, (0, 0))

        mw, mh = min(540, w - 40), min(420, h - 60)
        m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
        pygame.draw.rect(surface, (18, 32, 44), m, border_radius=14)
        pygame.draw.rect(surface, (60, 95, 125), m, width=2, border_radius=14)

        f_hdr = get_font(18, bold=True)
        surface.blit(f_hdr.render("CATATAN LENGKAP AKTIVITAS", True, C_GOLD), (m.x + 20, m.y + 16))

        # Recent 12 logs
        f_item = get_font(13)
        recent = engine.event_log[-12:]
        ly = m.y + 54
        for msg in recent:
            col = (235, 240, 248)
            if "menerima" in msg.lower() or "bebas" in msg.lower():
                col = C_SUCCESS
            elif "bangkrut" in msg.lower() or "penjara" in msg.lower() or "utang" in msg.lower():
                col = C_DANGER
            elif "membeli" in msg.lower() or "lelang" in msg.lower() or "membangun" in msg.lower():
                col = C_GOLD

            surface.blit(f_item.render(f"• {msg}", True, col), (m.x + 20, ly))
            ly += 26

        f_tip = get_font(12)
        surface.blit(f_tip.render("Klik di mana saja untuk menutup", True, (150, 175, 190)), (m.centerx - 90, m.bottom - 28))
