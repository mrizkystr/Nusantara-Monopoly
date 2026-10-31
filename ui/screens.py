"""
Complete UI Screens and Dialog Modals for Nusantara Property Tycoon.
Features:
- Premium Indonesian Casual Game Visuals
- 2.5D Mobile-Style HUD integration
- Dynamic Camera zoom/pan during gameplay
- Animated Property Certificates, Cultural Event Cards, Auctions, and Victory Celebration
"""
import math
import random
import pygame
from typing import List, Dict, Optional, Tuple, Callable

from game.state import GameState, TileType, PropertyColorGroup
from game.engine import GameEngine
from game.player import Player
from game.property import Tile
from game.economy import format_rupiah, Economy
from game.settings import Settings
from game.save_manager import SaveManager
from game.trading import TradeOffer
from ui.components import Button, Panel, get_font
from ui.renderer import (
    BoardRenderer, GROUP_COLORS, _GROUP_KEY,
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_LIGHT,
    COLOR_ACCENT_GOLD, COLOR_ACCENT_TEAL,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_DANGER, COLOR_SUCCESS
)
from ui.tokens import TokenRenderer, TOKEN_TYPES
from ui.audio import AudioManager
from ui.animation import DiceAnimation, MovementAnimation, ToastManager, ScreenFadeTransition
from ui.camera import Camera, CameraState
from ui.hud import ModernHUD
from ui.visual_assets import (
    make_menu_background, make_card_surf, draw_rounded_rect_with_shadow,
    draw_bevel_rect, GROUP_NAMES, C_GOLD, C_GOLD_LIGHT, C_TEAL,
    C_TEXT_LIGHT, C_TEXT_MED, C_TEXT_DARK, C_SUCCESS, C_DANGER,
    draw_property_card_artwork, draw_event_card_icon, draw_jail_bars_art, draw_trophy_art
)

TOKEN_PALETTE = [
    ("Merah",  (231, 76, 60)),
    ("Biru",   (52, 152, 219)),
    ("Hijau",  (46, 204, 113)),
    ("Kuning", (241, 196, 15)),
    ("Ungu",   (155, 89, 182)),
    ("Oranye", (230, 126, 34))
]


# =========================================================================
# MAIN MENU SCREEN — Premium Indonesian Cityscape
# =========================================================================
class MainMenuScreen:
    def __init__(self, on_new_game: Callable, on_load_game: Callable, on_rules: Callable, on_settings: Callable, on_quit: Callable):
        self.on_new_game = on_new_game
        self.on_load_game = on_load_game
        self.on_rules = on_rules
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.buttons: List[Button] = []
        self.anim_time: float = 0.0

    def update(self, dt: float) -> None:
        self.anim_time += dt

    def update_layout(self, w: int, h: int) -> None:
        btn_w, btn_h = min(360, int(w * 0.28)), 52
        start_y = int(h * 0.44)
        spacing = 14
        cx = w // 2 - (btn_w // 2)

        has_save = SaveManager.has_save_file()

        def wrap(fn):
            def inner():
                AudioManager.get_instance().play_sfx("click")
                fn()
            return inner

        self.buttons = [
            Button(pygame.Rect(cx, start_y, btn_w, btn_h), "MAIN BARU", wrap(self.on_new_game), bg_color=(46, 160, 95), hover_color=(60, 190, 115), font_size=18, border_radius=12),
            Button(pygame.Rect(cx, start_y + (btn_h + spacing), btn_w, btn_h), "LANJUTKAN PERMAINAN", wrap(self.on_load_game), bg_color=(45, 125, 195), hover_color=(55, 150, 230), font_size=16, is_enabled=has_save, border_radius=12),
            Button(pygame.Rect(cx, start_y + (btn_h + spacing) * 2, btn_w, btn_h), "CARA BERMAIN", wrap(self.on_rules), bg_color=(50, 75, 95), hover_color=(65, 95, 120), text_color=COLOR_TEXT_PRIMARY, font_size=16, border_radius=12),
            Button(pygame.Rect(cx, start_y + (btn_h + spacing) * 3, btn_w, btn_h), "PENGATURAN", wrap(self.on_settings), bg_color=(50, 75, 95), hover_color=(65, 95, 120), text_color=COLOR_TEXT_PRIMARY, font_size=16, border_radius=12),
            Button(pygame.Rect(cx, start_y + (btn_h + spacing) * 4, btn_w, btn_h), "KELUAR", wrap(self.on_quit), bg_color=(195, 55, 50), hover_color=(220, 70, 65), font_size=16, border_radius=12)
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        # Rich Indonesian tropical night cityscape background
        bg = make_menu_background(w, h)
        surface.blit(bg, (0, 0))

        cx = w // 2

        # Floating gold sparkles in night sky
        for i in range(12):
            spark_x = int((w * (0.15 + (i * 0.07))) + math.sin(self.anim_time * 2.0 + i) * 25) % w
            spark_y = int((h * 0.12) + math.cos(self.anim_time * 1.5 + i * 1.3) * 35)
            alpha = int(140 + 115 * math.sin(self.anim_time * 3.0 + i))
            psurf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(psurf, (255, 225, 100, alpha), (3, 3), 3)
            surface.blit(psurf, (spark_x, spark_y))

        # Title Emblem Container
        f_sub = get_font(20, bold=True)
        f_title = get_font(46, bold=True)
        f_tagline = get_font(16)

        sub_s = f_sub.render("✦  N U S A N T A R A  ✦", True, C_GOLD_LIGHT)
        title_s = f_title.render("PROPERTY TYCOON", True, (255, 252, 245))
        tag_s = f_tagline.render("Jelajahi Kota, Bangun Properti, Kuasai Kepulauan Indonesia", True, (210, 225, 230))

        # Title double shadow for 3D casual game look
        title_shad1 = f_title.render("PROPERTY TYCOON", True, (15, 25, 35))
        title_shad2 = f_title.render("PROPERTY TYCOON", True, (160, 110, 30))

        t_y = int(h * 0.22)
        surface.blit(sub_s, sub_s.get_rect(center=(cx, t_y - 42)))
        surface.blit(title_shad1, title_shad1.get_rect(center=(cx + 3, t_y + 3)))
        surface.blit(title_shad2, title_shad2.get_rect(center=(cx + 1, t_y + 1)))
        surface.blit(title_s, title_s.get_rect(center=(cx, t_y)))
        surface.blit(tag_s, tag_s.get_rect(center=(cx, t_y + 44)))

        # Decorative gold ribbon under tagline
        ribbon_w = min(480, int(w * 0.45))
        rx = cx - ribbon_w // 2
        ry = t_y + 64
        pygame.draw.line(surface, C_GOLD, (rx, ry), (rx + ribbon_w, ry), 2)
        pygame.draw.circle(surface, C_GOLD_LIGHT, (cx, ry), 5)

        for b in self.buttons:
            b.draw(surface)


# =========================================================================
# PLAYER SETUP SCREEN
# =========================================================================
class SetupScreen:
    def __init__(self, on_start: Callable[[List[Dict]], None], on_back: Callable[[], None]):
        self.on_start = on_start
        self.on_back = on_back
        self.num_players: int = 4
        self.player_names: List[str] = ["Konglomerat 1", "Konglomerat 2", "Konglomerat 3", "Konglomerat 4"]
        self.player_colors: List[int] = [0, 1, 2, 3]
        self.player_tokens: List[int] = [0, 1, 2, 3]
        self.active_input_idx: Optional[int] = None
        self.error_message: str = ""
        self.buttons: List[Button] = []
        self.anim_time: float = 0.0

    def update(self, dt: float) -> None:
        self.anim_time += dt

    def update_layout(self, w: int, h: int) -> None:
        self.buttons = []
        cx = w // 2

        def wrap(fn):
            def inner():
                AudioManager.get_instance().play_sfx("click")
                fn()
            return inner

        # Player count buttons (2, 3, 4)
        btn_w, btn_h = 95, 42
        start_x = cx - 160
        y_count = int(h * 0.19)
        for count in [2, 3, 4]:
            is_cur = (self.num_players == count)
            b = Button(
                pygame.Rect(start_x, y_count, btn_w, btn_h),
                f"{count} Pemain",
                wrap(lambda c=count: self._set_player_count(c)),
                bg_color=(46, 160, 95) if is_cur else (50, 75, 95),
                hover_color=(60, 190, 115) if is_cur else (65, 95, 120),
                font_size=15,
                border_radius=8
            )
            self.buttons.append(b)
            start_x += btn_w + 14

        # Player setup cards
        card_w = min(680, w - 40)
        card_start_y = int(h * 0.28)
        card_h = 68
        for i in range(self.num_players):
            cy = card_start_y + (i * (card_h + 14))
            c_right = cx + (card_w // 2)

            t_name = TOKEN_TYPES[self.player_tokens[i]][1]
            b_tok = Button(
                pygame.Rect(c_right - 275, cy + 16, 135, 38),
                f"Pion: {t_name}",
                wrap(lambda idx=i: self._cycle_token(idx)),
                bg_color=(50, 75, 95),
                hover_color=(65, 95, 120),
                font_size=13,
                border_radius=8
            )
            self.buttons.append(b_tok)

            col_name, rgb = TOKEN_PALETTE[self.player_colors[i]]
            b_col = Button(
                pygame.Rect(c_right - 130, cy + 16, 115, 38),
                col_name,
                wrap(lambda idx=i: self._cycle_color(idx)),
                bg_color=rgb,
                font_size=13,
                border_radius=8
            )
            self.buttons.append(b_col)

        # Bottom buttons
        self.buttons.append(
            Button(pygame.Rect(cx - 220, int(h * 0.85), 210, 50), "MULAI BERTANDING", wrap(self._submit), bg_color=(46, 160, 95), hover_color=(60, 190, 115), font_size=17, border_radius=12)
        )
        self.buttons.append(
            Button(pygame.Rect(cx + 10, int(h * 0.85), 210, 50), "KEMBALI KE MENU", wrap(self.on_back), bg_color=(50, 75, 95), hover_color=(65, 95, 120), font_size=17, border_radius=12)
        )

    def _set_player_count(self, count: int) -> None:
        self.num_players = count
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _cycle_token(self, idx: int) -> None:
        self.player_tokens[idx] = (self.player_tokens[idx] + 1) % len(TOKEN_TYPES)
        self.error_message = ""
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _cycle_color(self, idx: int) -> None:
        self.player_colors[idx] = (self.player_colors[idx] + 1) % len(TOKEN_PALETTE)
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _submit(self) -> None:
        for i in range(self.num_players):
            if not self.player_names[i].strip():
                self.error_message = f"Nama Pemain {i+1} tidak boleh kosong!"
                return

        tokens_chosen = [self.player_tokens[i] for i in range(self.num_players)]
        if len(tokens_chosen) != len(set(tokens_chosen)):
            self.error_message = "Setiap pemain harus memilih pion yang berbeda!"
            return

        configs = []
        for i in range(self.num_players):
            configs.append({
                "name": self.player_names[i].strip(),
                "color": TOKEN_PALETTE[self.player_colors[i]][1],
                "token_type": TOKEN_TYPES[self.player_tokens[i]][0]
            })
        self.on_start(configs)

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            w, h = pygame.display.get_surface().get_size()
            cx = w // 2
            card_w = min(680, w - 40)
            card_start_y = int(h * 0.28)
            card_h = 68
            self.active_input_idx = None
            for i in range(self.num_players):
                cy = card_start_y + (i * (card_h + 14))
                input_rect = pygame.Rect(cx - (card_w // 2) + 70, cy + 16, 210, 38)
                if input_rect.collidepoint(event.pos):
                    self.active_input_idx = i
                    break

        elif event.type == pygame.KEYDOWN and self.active_input_idx is not None:
            idx = self.active_input_idx
            if event.key == pygame.K_BACKSPACE:
                self.player_names[idx] = self.player_names[idx][:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.active_input_idx = None
            elif len(self.player_names[idx]) < 18 and event.unicode.isprintable():
                self.player_names[idx] += event.unicode
                self.error_message = ""

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        bg = make_menu_background(w, h)
        surface.blit(bg, (0, 0))

        cx = w // 2

        f_title = get_font(30, bold=True)
        t_s = f_title.render("PENGATURAN KONGLOMERAT", True, (255, 250, 240))
        surface.blit(t_s, t_s.get_rect(center=(cx, int(h * 0.09))))

        f_lbl = get_font(15, bold=True)
        lbl_s = f_lbl.render("Pilih Jumlah Pemain:", True, C_GOLD)
        surface.blit(lbl_s, lbl_s.get_rect(center=(cx, int(h * 0.15))))

        # Player setup cards
        card_w = min(680, w - 40)
        card_start_y = int(h * 0.28)
        card_h = 68
        for i in range(self.num_players):
            cy = card_start_y + (i * (card_h + 14))
            c_rect = pygame.Rect(cx - (card_w // 2), cy, card_w, card_h)

            # Card panel
            pygame.draw.rect(surface, (20, 35, 48), c_rect, border_radius=10)
            pygame.draw.rect(surface, (55, 85, 110), c_rect, width=1, border_radius=10)

            # Token preview
            tok_type = TOKEN_TYPES[self.player_tokens[i]][0]
            rgb = TOKEN_PALETTE[self.player_colors[i]][1]
            TokenRenderer.draw_token(surface, tok_type, (c_rect.x + 36, c_rect.y + card_h // 2), radius=18, color=rgb, is_active=True, anim_time=self.anim_time)

            # Name input field
            input_rect = pygame.Rect(c_rect.x + 70, cy + 16, 210, 38)
            is_focus = (self.active_input_idx == i)
            pygame.draw.rect(surface, (14, 24, 34) if is_focus else (30, 48, 64), input_rect, border_radius=8)
            pygame.draw.rect(surface, C_GOLD if is_focus else (60, 85, 110), input_rect, width=2 if is_focus else 1, border_radius=8)

            f_name = get_font(14, bold=True)
            txt = self.player_names[i] + ("|" if is_focus else "")
            n_s = f_name.render(txt, True, C_TEXT_LIGHT)
            surface.blit(n_s, (input_rect.x + 10, input_rect.y + 9))

        if self.error_message:
            f_err = get_font(14, bold=True)
            err_s = f_err.render(self.error_message, True, COLOR_DANGER)
            surface.blit(err_s, err_s.get_rect(center=(cx, int(h * 0.80))))

        for b in self.buttons:
            b.draw(surface)


# =========================================================================
# RULES & SETTINGS SCREENS
# =========================================================================
class RulesScreen:
    def __init__(self, on_back: Callable[[], None]):
        self.on_back = on_back
        self.page = 0
        self.buttons: List[Button] = []
        self.topics = [
            ("1. TUJUAN PERMAINAN", "Kuasai properti terbaik di kepulauan Nusantara, dirikan rumah dan hotel, kelola keuangan Anda dengan bijak, dan jadilah konglomerat terakhir yang bertahan saat pemain lain mengalami kebangkrutan."),
            ("2. CARA MELEMPAR DADU", "Setiap putaran, pemain melempar dua buah dadu (2d6). Bidak bergerak maju searah jarum jam. Jika mendapatkan dadu kembar (angka sama), pemain mendapat giliran lempar tambahan! Namun waspada: melempar dadu kembar 3 kali berturut-turut akan langsung mengirim Anda ke Penjara!"),
            ("3. MEMBELI & LELANG PROPERTI", "Ketika mendarat di petak kota yang belum dimiliki, Anda dapat membelinya sesuai harga tercantum. Jika Anda memilih melepas pembelian, petak tersebut langsung dilelang secara terbuka untuk seluruh konglomerat yang aktif."),
            ("4. MEMBAYAR SEWA", "Jika Anda mendarat di petak milik lawan, Anda wajib membayar uang sewa. Memiliki seluruh petak dalam satu kelompok warna (Monopoli) akan melipatgandakan sewa dasar petak yang belum dibangun."),
            ("5. MEMBANGUN RUMAH", "Setelah menguasai seluruh kelompok warna tanpa ada yang digadaikan, Anda berhak membangun rumah (maksimal 4 per petak). Pembangunan wajib merata di seluruh kota dalam kelompok warna tersebut."),
            ("6. MEMBANGUN HOTEL", "Setelah sebuah kelompok warna terisi masing-masing 4 rumah, Anda dapat meningkatkan bangunan menjadi Hotel (1 per kota) dengan menukar 4 rumah tersebut kembali ke Bank dan membayar biaya hotel."),
            ("7. KESEMPATAN & DANA UMUM", "Mendarat di petak Kesempatan atau Dana Umum akan membuka kartu kejadian khas Indonesia: tender proyek daerah, dividen BUMN, denda ETLE, renovasi bangunan, gotong royong warga, hingga Kartu Bebas Penjara."),
            ("8. MEKANIK PENJARA", "Masuk Penjara terjadi jika: mendarat di petak MASUK PENJARA, mengambil kartu penjara, atau 3 kali dadu kembar. Keluar dengan: bayar denda Rp500.000, gunakan Kartu Bebas, atau lempar dadu kembar dalam 3 kesempatan."),
            ("9. GADAI & TEBUS PROPERTI", "Jika membutuhkan uang tunai darurat, properti tanpa bangunan dapat digadaikan ke Bank seharga 50% nilai beli. Properti tergadai tidak menghasilkan uang sewa. Tebus kembali dengan membayar nilai gadai ditambah bunga 10%."),
            ("10. KEWAJIBAN UTANG & KEPAILITAN", "Jika tidak sanggup membayar sewa atau denda, pemain masuk ke mode Pelunasan Utang. Anda dapat menjual bangunan atau menggadaikan aset. Jika tetap tidak mencukupi, Anda dinyatakan pailit/bangkrut dan seluruh aset diserahkan ke kreditur."),
            ("11. KEMENANGAN AKHIR", "Pemain terakhir yang tidak bangkrut dinobatkan sebagai Konglomerat Terhebat Nusantara! Layar juara akan menyajikan rincian statistik kas akhir, total properti, dan nilai kekayaan bersih Anda.")
        ]

    def update_layout(self, w: int, h: int) -> None:
        self.buttons = []
        cx = w // 2
        by = int(h * 0.84)

        def wrap(fn):
            def inner():
                AudioManager.get_instance().play_sfx("click")
                fn()
            return inner

        self.buttons.append(Button(pygame.Rect(cx - 240, by, 140, 44), "< SEBELUMNYA", wrap(self._prev_page), bg_color=(50, 75, 95), font_size=13, is_enabled=(self.page > 0), border_radius=8))
        self.buttons.append(Button(pygame.Rect(cx - 70, by, 140, 44), "MENU UTAMA", wrap(self.on_back), bg_color=(50, 75, 95), font_size=14, border_radius=8))
        self.buttons.append(Button(pygame.Rect(cx + 100, by, 140, 44), "SELANJUTNYA >", wrap(self._next_page), bg_color=(46, 160, 95), font_size=13, is_enabled=(self.page < len(self.topics) - 1), border_radius=8))

    def _prev_page(self) -> None:
        self.page = max(0, self.page - 1)
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _next_page(self) -> None:
        self.page = min(len(self.topics) - 1, self.page + 1)
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        bg = make_menu_background(w, h)
        surface.blit(bg, (0, 0))

        cx = w // 2
        f_title = get_font(28, bold=True)
        surface.blit(f_title.render("PANDUAN & CARA BERMAIN", True, C_TEXT_LIGHT), f_title.render("PANDUAN & CARA BERMAIN", True, C_TEXT_LIGHT).get_rect(center=(cx, int(h * 0.12))))

        box = pygame.Rect(cx - 380, int(h * 0.22), 760, int(h * 0.56))
        pygame.draw.rect(surface, (20, 36, 48), box, border_radius=14)
        pygame.draw.rect(surface, (60, 95, 120), box, width=2, border_radius=14)

        title, desc = self.topics[self.page]
        f_topic = get_font(20, bold=True)
        surface.blit(f_topic.render(title, True, C_GOLD), (box.x + 32, box.y + 28))

        f_page = get_font(13)
        p_s = f_page.render(f"Halaman {self.page + 1} dari {len(self.topics)}", True, (160, 185, 200))
        surface.blit(p_s, (box.right - p_s.get_width() - 32, box.y + 32))

        f_desc = get_font(16)
        words = desc.split(" ")
        lines = []
        cur_line = ""
        for wd in words:
            if f_desc.size(cur_line + " " + wd)[0] < box.width - 64:
                cur_line += " " + wd if cur_line else wd
            else:
                lines.append(cur_line)
                cur_line = wd
        if cur_line:
            lines.append(cur_line)

        ly = box.y + 84
        for l in lines:
            surface.blit(f_desc.render(l, True, (240, 245, 250)), (box.x + 32, ly))
            ly += 30

        for b in self.buttons:
            b.draw(surface)


class SettingsScreen:
    def __init__(self, settings: Settings, on_back: Callable[[], None]):
        self.settings = settings
        self.on_back = on_back
        self.buttons: List[Button] = []

    def update_layout(self, w: int, h: int) -> None:
        self.buttons = []
        cx = w // 2
        sy = int(h * 0.24)
        bw, bh = 46, 36

        def wrap(fn):
            def inner():
                AudioManager.get_instance().play_sfx("click")
                fn()
            return inner

        # Master
        self.buttons.append(Button(pygame.Rect(cx + 80, sy, bw, bh), "-", wrap(lambda: self._adjust_vol("master", -0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6))
        self.buttons.append(Button(pygame.Rect(cx + 170, sy, bw, bh), "+", wrap(lambda: self._adjust_vol("master", 0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6))

        # Music
        self.buttons.append(Button(pygame.Rect(cx + 80, sy + 50, bw, bh), "-", wrap(lambda: self._adjust_vol("music", -0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6))
        self.buttons.append(Button(pygame.Rect(cx + 170, sy + 50, bw, bh), "+", wrap(lambda: self._adjust_vol("music", 0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6))

        # SFX
        self.buttons.append(Button(pygame.Rect(cx + 80, sy + 100, bw, bh), "-", wrap(lambda: self._adjust_vol("sfx", -0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6))
        self.buttons.append(Button(pygame.Rect(cx + 170, sy + 100, bw, bh), "+", wrap(lambda: self._adjust_vol("sfx", 0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6))

        # Mute toggle
        mute_txt = "BISUKAN SUARA: AKTIF" if self.settings.muted else "BISUKAN SUARA: MATI"
        self.buttons.append(Button(pygame.Rect(cx - 160, sy + 160, 320, 40), mute_txt, wrap(self._toggle_mute), bg_color=(195, 55, 50) if self.settings.muted else (50, 75, 95), font_size=14, border_radius=8))

        # Animation Speed
        spd_txt = f"KECEPATAN ANIMASI: {self.settings.animation_speed.upper()}"
        self.buttons.append(Button(pygame.Rect(cx - 160, sy + 212, 320, 40), spd_txt, wrap(self._cycle_speed), bg_color=(50, 75, 95), font_size=14, border_radius=8))

        # Skip Movement
        skip_txt = "LEWATI ANIMASI GERAK: YA" if self.settings.skip_movement else "LEWATI ANIMASI GERAK: TIDAK"
        self.buttons.append(Button(pygame.Rect(cx - 160, sy + 264, 320, 40), skip_txt, wrap(self._toggle_skip), bg_color=(50, 75, 95), font_size=14, border_radius=8))

        # Back
        self.buttons.append(Button(pygame.Rect(cx - 110, int(h * 0.85), 220, 48), "SIMPAN & KEMBALI", wrap(self._save_and_back), bg_color=(46, 160, 95), font_size=17, border_radius=10))

    def _adjust_vol(self, category: str, delta: float) -> None:
        if category == "master":
            self.settings.master_volume = max(0.0, min(1.0, round(self.settings.master_volume + delta, 2)))
        elif category == "music":
            self.settings.music_volume = max(0.0, min(1.0, round(self.settings.music_volume + delta, 2)))
        elif category == "sfx":
            self.settings.sfx_volume = max(0.0, min(1.0, round(self.settings.sfx_volume + delta, 2)))
        self.settings.apply_to_audio(AudioManager.get_instance())
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _toggle_mute(self) -> None:
        self.settings.muted = not self.settings.muted
        self.settings.apply_to_audio(AudioManager.get_instance())
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _cycle_speed(self) -> None:
        speeds = ["Normal", "Fast", "Instant"]
        cur_idx = speeds.index(self.settings.animation_speed) if self.settings.animation_speed in speeds else 0
        self.settings.animation_speed = speeds[(cur_idx + 1) % len(speeds)]
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _toggle_skip(self) -> None:
        self.settings.skip_movement = not self.settings.skip_movement
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def _save_and_back(self) -> None:
        self.settings.save()
        self.on_back()

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        bg = make_menu_background(w, h)
        surface.blit(bg, (0, 0))

        cx = w // 2
        f_title = get_font(28, bold=True)
        surface.blit(f_title.render("PENGATURAN PERMAINAN", True, C_TEXT_LIGHT), f_title.render("PENGATURAN PERMAINAN", True, C_TEXT_LIGHT).get_rect(center=(cx, int(h * 0.12))))

        f_lbl = get_font(15, bold=True)
        f_val = get_font(15)
        sy = int(h * 0.24)

        surface.blit(f_lbl.render("Volume Utama:", True, (170, 195, 205)), (cx - 160, sy + 6))
        surface.blit(f_val.render(f"{int(self.settings.master_volume * 100)}%", True, C_GOLD), (cx + 130, sy + 6))

        surface.blit(f_lbl.render("Volume Musik (BGM):", True, (170, 195, 205)), (cx - 160, sy + 56))
        surface.blit(f_val.render(f"{int(self.settings.music_volume * 100)}%", True, C_GOLD), (cx + 130, sy + 56))

        surface.blit(f_lbl.render("Volume Efek Suara (SFX):", True, (170, 195, 205)), (cx - 160, sy + 106))
        surface.blit(f_val.render(f"{int(self.settings.sfx_volume * 100)}%", True, C_GOLD), (cx + 130, sy + 106))

        for b in self.buttons:
            b.draw(surface)


# =========================================================================
# GAMEPLAY SCREEN — 2.5D Board, Dynamic Camera, Mobile HUD, Rich Modals
# =========================================================================
class GamePlayScreen:
    def __init__(self, engine: GameEngine, settings: Settings, on_main_menu: Callable[[], None]):
        self.engine = engine
        self.settings = settings
        self.on_main_menu = on_main_menu

        self.renderer = BoardRenderer()
        self.camera = Camera(1440, 900)

        # Animations
        self.dice_anim = DiceAnimation()
        self.move_anim = MovementAnimation()
        self.toast_mgr = ToastManager()

        # Mobile HUD
        self.hud = ModernHUD(
            on_roll_dice=self._on_roll_dice,
            on_end_turn=self._on_end_turn,
            on_manage_assets=self._open_manage,
            on_trade=self._open_trade,
            on_save=self._save_game,
            on_settings=self._open_settings_modal,
            on_toggle_camera=self._toggle_camera_mode,
            on_main_menu=self.on_main_menu
        )

        # Legacy compatibility attribute for tests checking self.sidebar_buttons
        self.sidebar_buttons: List[Button] = []

        # Modal / Dialog states
        self.inspect_tile_pos: Optional[int] = None
        self.show_manage_modal = False
        self.show_trade_modal = False
        self.show_settings_modal = False
        self.trade_partner_id: Optional[int] = None
        self.trade_offer_cash: int = 0
        self.trade_req_cash: int = 0
        self.trade_offer_props: List[int] = []
        self.trade_req_props: List[int] = []
        self.modal_buttons: List[Button] = []

        self._last_processed_tx_count = 0

    def update_layout(self, w: int, h: int) -> None:
        self.renderer.update_layout(w, h)
        board_center = (self.renderer.board_rect.centerx, self.renderer.board_rect.centery)
        self.camera.set_viewport(w, h, default_center=board_center)
        self.hud.update_layout(w, h, self.engine, is_overview=(self.camera.state == CameraState.BOARD_OVERVIEW))
        self.sidebar_buttons = list(self.hud.dock_buttons)

    def update(self, dt: float) -> None:
        self.renderer.update(dt)
        self.camera.update(dt)
        self.hud.update(dt, self.engine)
        self.dice_anim.update(dt)
        self.move_anim.update(dt)
        self.toast_mgr.update(dt)

        # Check for new confirmed financial transactions from engine
        if len(self.engine.transactions) > self._last_processed_tx_count:
            new_txs = self.engine.transactions[self._last_processed_tx_count:]
            for tx in new_txs:
                amt = tx["amount"]
                sign = "+" if amt > 0 else ""
                col = COLOR_SUCCESS if amt > 0 else COLOR_DANGER
                bx = self.renderer.board_rect.centerx
                by = self.renderer.board_rect.centery
                self.toast_mgr.add(f"{sign}{format_rupiah(amt)} ({tx['description']})", color=col)
                self.toast_mgr.add_transaction(f"{sign}{format_rupiah(amt)}", bx, by, col, amt)
            self._last_processed_tx_count = len(self.engine.transactions)

    def _toggle_camera_mode(self) -> None:
        if self.camera.state == CameraState.BOARD_OVERVIEW:
            cp = self.engine.current_player
            if cp and cp.position in self.renderer.tile_rects:
                target_rect = self.renderer.tile_rects[cp.position]
                self.camera.focus_tile(target_rect.center, zoom=1.32, state=CameraState.PLAYER_FOCUS)
        else:
            self.camera.reset_overview()
        self._refresh()

    def _open_settings_modal(self) -> None:
        self.show_settings_modal = True

    def _on_roll_dice(self) -> None:
        if self.engine.state != GameState.WAITING_FOR_ROLL:
            return

        ok, _ = self.engine.roll_dice(defer_movement=True)
        if ok and self.engine.pending_movement:
            d1, d2 = self.engine.dice.dice1, self.engine.dice.dice2

            def on_dice_done():
                pm = self.engine.pending_movement
                if pm:
                    def on_step_moved(tile_idx):
                        if tile_idx in self.renderer.tile_rects:
                            t_rect = self.renderer.tile_rects[tile_idx]
                            self.camera.follow_movement(t_rect.center)

                    self.move_anim.start(
                        path=pm["path"],
                        start_tile=pm["start_pos"],
                        target_tile=pm["target_pos"],
                        speed=self.settings.animation_speed,
                        on_step=on_step_moved,
                        on_complete=self._on_movement_complete
                    )
                self._refresh()

            self.dice_anim.start(d1, d2, speed=self.settings.animation_speed, on_complete=on_dice_done)
        self._refresh()

    def _on_movement_complete(self) -> None:
        self.engine.complete_deferred_movement()
        cp = self.engine.current_player
        if cp and cp.position in self.renderer.tile_rects:
            t_rect = self.renderer.tile_rects[cp.position]
            self.camera.focus_tile(t_rect.center, zoom=1.28, state=CameraState.PROPERTY_FOCUS, auto_return_sec=3.0)
        self._refresh()

    def _on_end_turn(self) -> None:
        self.engine.end_turn()
        self.camera.reset_overview()
        self._refresh()

    def _open_manage(self) -> None:
        self.show_manage_modal = True
        self.inspect_tile_pos = None

    def _open_trade(self) -> None:
        active_opponents = [p.id for p in self.engine.active_players if p.id != self.engine.current_player.id]
        if active_opponents:
            self.trade_partner_id = active_opponents[0]
            self.trade_offer_cash = 0
            self.trade_req_cash = 0
            self.trade_offer_props.clear()
            self.trade_req_props.clear()
            self.show_trade_modal = True
            self.inspect_tile_pos = None

    def _save_game(self) -> None:
        data = self.engine.to_dict()
        ok, msg = SaveManager.save_game(data)
        self.engine.log(msg)
        self.toast_mgr.add("Permainan Berhasil Disimpan!", color=COLOR_SUCCESS)

    def _refresh(self) -> None:
        w, h = pygame.display.get_surface().get_size()
        self.update_layout(w, h)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.move_anim.is_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.move_anim.skip()
                return

        # Tile Inspection click on board
        if event.type == pygame.MOUSEMOTION:
            self.renderer.hovered_tile = self.renderer.get_tile_at_pos(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self._has_active_blocking_modal():
                clicked_pos = self.renderer.get_tile_at_pos(event.pos)
                if clicked_pos is not None:
                    tile = self.engine.board.get_tile(clicked_pos)
                    if tile and tile.is_ownable:
                        self.inspect_tile_pos = clicked_pos
                        AudioManager.get_instance().play_sfx("click")
                        return

        # Key shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.engine.state == GameState.WAITING_FOR_ROLL and not self.dice_anim.is_active:
                self._on_roll_dice()
                return
            elif event.key == pygame.K_ESCAPE:
                if self.inspect_tile_pos is not None:
                    self.inspect_tile_pos = None
                    return
                elif self.show_manage_modal:
                    self.show_manage_modal = False
                    return
                elif self.show_trade_modal:
                    self.show_trade_modal = False
                    return
                elif self.show_settings_modal:
                    self.show_settings_modal = False
                    return
                elif self.camera.state != CameraState.BOARD_OVERVIEW:
                    self.camera.reset_overview()
                    return

        # Modals
        if self.inspect_tile_pos is not None:
            self._handle_inspect_modal_event(event)
            return
        elif self.engine.state == GameState.PROPERTY_DECISION:
            self._handle_property_decision_event(event)
            return
        elif self.engine.state == GameState.AUCTION:
            self._handle_auction_event(event)
            return
        elif self.engine.state == GameState.CARD_RESOLUTION:
            self._handle_card_event(event)
            return
        elif self.engine.state == GameState.JAIL_DECISION:
            self._handle_jail_event(event)
            return
        elif self.engine.state == GameState.DEBT_RESOLUTION:
            self._handle_debt_event(event)
            return
        elif self.engine.state == GameState.GAME_OVER:
            self._handle_game_over_event(event)
            return

        if self.show_manage_modal:
            self._handle_manage_modal_event(event)
            return
        if self.show_trade_modal:
            self._handle_trade_modal_event(event)
            return
        if self.show_settings_modal:
            self._handle_settings_modal_event(event)
            return

        # HUD event handling
        self.hud.handle_event(event)

    def _has_active_blocking_modal(self) -> bool:
        return (
            self.engine.state in (GameState.PROPERTY_DECISION, GameState.AUCTION, GameState.CARD_RESOLUTION, GameState.JAIL_DECISION, GameState.DEBT_RESOLUTION, GameState.GAME_OVER)
            or self.show_manage_modal or self.show_trade_modal or self.inspect_tile_pos is not None or self.show_settings_modal
        )

    def draw(self, surface: pygame.Surface) -> None:
        anim_pos = None
        if self.move_anim.is_active:
            cp = self.engine.current_player
            if cp:
                anim_pos = {cp.id: self.move_anim.current_tile}

        # 1. Render Board with Camera Transformation
        self.renderer.draw(
            surface,
            self.engine,
            animated_positions=anim_pos,
            dice_anim=self.dice_anim,
            active_dest_tile=self.move_anim.target_tile if self.move_anim.is_active else None,
            camera=self.camera
        )

        # 2. Render Modern HUD (Top Bar, Action Dock, Mini Activity Ticker)
        self.hud.draw(surface, self.engine)

        # 3. Draw Floating Toasts and Transaction Coins
        bx, by = self.renderer.board_rect.centerx, self.renderer.board_rect.centery + 70
        self.toast_mgr.draw(surface, bx, by, get_font(14, bold=True))

        # 4. Modals
        if self.inspect_tile_pos is not None:
            self._draw_inspect_modal(surface)
        elif self.engine.state == GameState.PROPERTY_DECISION:
            self._draw_property_decision_modal(surface)
        elif self.engine.state == GameState.AUCTION:
            self._draw_auction_modal(surface)
        elif self.engine.state == GameState.CARD_RESOLUTION:
            self._draw_card_modal(surface)
        elif self.engine.state == GameState.JAIL_DECISION:
            self._draw_jail_modal(surface)
        elif self.engine.state == GameState.DEBT_RESOLUTION:
            self._draw_debt_modal(surface)
        elif self.engine.state == GameState.GAME_OVER:
            self._draw_game_over_modal(surface)
        elif self.show_manage_modal:
            self._draw_manage_modal(surface)
        elif self.show_trade_modal:
            self._draw_trade_modal(surface)
        elif self.show_settings_modal:
            self._draw_settings_modal(surface)

    def _draw_modal_backdrop(self, surface: pygame.Surface) -> pygame.Rect:
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        surface.blit(dim, (0, 0))

        mw, mh = min(580, w - 40), min(460, h - 40)
        modal_rect = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
        pygame.draw.rect(surface, (18, 32, 44), modal_rect, border_radius=14)
        pygame.draw.rect(surface, (65, 100, 130), modal_rect, width=2, border_radius=14)
        return modal_rect

    # 1. PROPERTY INSPECT CARD MODAL
    def _draw_inspect_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        tile = self.engine.board.get_tile(self.inspect_tile_pos)
        if not tile:
            return

        f_hdr = get_font(18, bold=True)
        surface.blit(f_hdr.render("SERTIFIKAT HAK MILIK PROPERTI", True, C_GOLD), (m.x + 28, m.y + 18))

        f_name = get_font(24, bold=True)
        surface.blit(f_name.render(tile.name, True, C_TEXT_LIGHT), (m.x + 28, m.y + 46))

        if tile.color_group:
            col = GROUP_COLORS.get(tile.color_group, (100, 100, 100))
            pygame.draw.rect(surface, col, (m.x + 28, m.y + 78, m.width - 56, 8), border_radius=3)

        owner = self.engine.get_player(tile.owner_id) if tile.owner_id is not None else None
        owner_name = owner.name if owner else "Bank Negara (Tersedia untuk Dibeli)"

        f_info = get_font(14)
        surface.blit(f_info.render(f"Pemilik: {owner_name}", True, C_TEAL), (m.x + 30, m.y + 98))
        surface.blit(f_info.render(f"Harga Beli: {format_rupiah(tile.purchase_price)}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 122))
        surface.blit(f_info.render(f"Nilai Hipotek / Gadai: {format_rupiah(tile.mortgage_value)}", True, (170, 190, 205)), (m.x + 30, m.y + 146))

        if tile.type == TileType.PROPERTY and len(tile.rent_table) == 7:
            f_tbl = get_font(12)
            surface.blit(f_tbl.render(f"• Sewa Dasar: {format_rupiah(tile.rent_table[0])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 178))
            surface.blit(f_tbl.render(f"• Monopoli Warna: {format_rupiah(tile.rent_table[1])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 198))
            surface.blit(f_tbl.render(f"• Dengan 1 Rumah: {format_rupiah(tile.rent_table[2])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 218))
            surface.blit(f_tbl.render(f"• Dengan 2 Rumah: {format_rupiah(tile.rent_table[3])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 238))
            surface.blit(f_tbl.render(f"• Dengan 3 Rumah: {format_rupiah(tile.rent_table[4])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 258))
            surface.blit(f_tbl.render(f"• Dengan 4 Rumah: {format_rupiah(tile.rent_table[5])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 278))
            surface.blit(f_tbl.render(f"• Dengan 1 HOTEL: {format_rupiah(tile.rent_table[6])}", True, C_GOLD), (m.x + 30, m.y + 298))
            surface.blit(f_tbl.render(f"Biaya Bangun Rumah/Hotel: {format_rupiah(tile.building_cost)}", True, C_TEAL), (m.x + 30, m.y + 328))

    def _build_inspect_buttons(self, m: pygame.Rect) -> None:
        b_close = Button(pygame.Rect(m.centerx - 85, m.bottom - 56, 170, 42), "TUTUP (ESC)", lambda: self._close_inspect(), bg_color=(50, 75, 95), border_radius=8)
        self.modal_buttons = [b_close]

    def _draw_inspect_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        tile = self.engine.board.get_tile(self.inspect_tile_pos)
        if not tile:
            return

        f_hdr = get_font(18, bold=True)
        surface.blit(f_hdr.render("SERTIFIKAT HAK MILIK PROPERTI", True, C_GOLD), (m.x + 28, m.y + 18))

        f_name = get_font(24, bold=True)
        surface.blit(f_name.render(tile.name, True, C_TEXT_LIGHT), (m.x + 28, m.y + 46))

        if tile.color_group:
            col = GROUP_COLORS.get(tile.color_group, (100, 100, 100))
            pygame.draw.rect(surface, col, (m.x + 28, m.y + 78, m.width - 56, 8), border_radius=3)

        owner = self.engine.get_player(tile.owner_id) if tile.owner_id is not None else None
        owner_name = owner.name if owner else "Bank Negara (Tersedia untuk Dibeli)"

        f_info = get_font(14)
        surface.blit(f_info.render(f"Pemilik: {owner_name}", True, C_TEAL), (m.x + 30, m.y + 98))
        surface.blit(f_info.render(f"Harga Beli: {format_rupiah(tile.purchase_price)}", True, C_GOLD), (m.x + 30, m.y + 122))
        surface.blit(f_info.render(f"Nilai Hipotek / Gadai: {format_rupiah(tile.mortgage_value)}", True, (170, 190, 205)), (m.x + 30, m.y + 146))

        if tile.type == TileType.PROPERTY and len(tile.rent_table) == 7:
            f_tbl = get_font(12)
            surface.blit(f_tbl.render(f"• Sewa Dasar: {format_rupiah(tile.rent_table[0])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 178))
            surface.blit(f_tbl.render(f"• Monopoli Warna: {format_rupiah(tile.rent_table[1])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 198))
            surface.blit(f_tbl.render(f"• Dengan 1 Rumah: {format_rupiah(tile.rent_table[2])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 218))
            surface.blit(f_tbl.render(f"• Dengan 2 Rumah: {format_rupiah(tile.rent_table[3])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 238))
            surface.blit(f_tbl.render(f"• Dengan 3 Rumah: {format_rupiah(tile.rent_table[4])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 258))
            surface.blit(f_tbl.render(f"• Dengan 4 Rumah: {format_rupiah(tile.rent_table[5])}", True, C_TEXT_LIGHT), (m.x + 30, m.y + 278))
            surface.blit(f_tbl.render(f"• Dengan 1 HOTEL: {format_rupiah(tile.rent_table[6])}", True, C_GOLD), (m.x + 30, m.y + 298))
            surface.blit(f_tbl.render(f"Biaya Bangun Rumah/Hotel: {format_rupiah(tile.building_cost)}", True, C_TEAL), (m.x + 30, m.y + 328))

        self._build_inspect_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _close_inspect(self) -> None:
        self.inspect_tile_pos = None

    def _handle_inspect_modal_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_inspect_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                break

    # 2. PROPERTY PURCHASE MODAL
    def _build_property_decision_buttons(self, m: pygame.Rect) -> None:
        cp = self.engine.current_player
        if not cp:
            self.modal_buttons = []
            return
        tile = self.engine.board.get_tile(cp.position)
        if not tile:
            self.modal_buttons = []
            return

        can_buy = cp.can_afford(tile.purchase_price)

        def on_buy():
            ok, _ = self.engine.buy_current_property()
            if ok:
                AudioManager.get_instance().play_sfx("buy")
                self.toast_mgr.add_construction((m.centerx, m.centery))

        def on_auction():
            self.engine.decline_and_auction_property()

        b1 = Button(pygame.Rect(m.x + 30, m.bottom - 72, (m.width - 80) // 2, 48), "BELI PROPERTI", on_buy, bg_color=(46, 160, 95), hover_color=(60, 190, 115), is_enabled=can_buy, border_radius=10)
        b2 = Button(pygame.Rect(m.x + 40 + (m.width - 80) // 2, m.bottom - 72, (m.width - 80) // 2, 48), "LELANG UMUM", on_auction, bg_color=(225, 130, 40), hover_color=(245, 150, 60), border_radius=10)
        self.modal_buttons = [b1, b2]

    def _draw_property_decision_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        cp = self.engine.current_player
        if not cp:
            return
        tile = self.engine.board.get_tile(cp.position)
        if not tile:
            return

        f_top = get_font(15, bold=True)
        surface.blit(f_top.render("PELUANG INVESTASI NUSANTARA", True, C_GOLD), (m.x + 28, m.y + 20))

        f_name = get_font(24, bold=True)
        surface.blit(f_name.render(tile.name, True, C_TEXT_LIGHT), (m.x + 28, m.y + 48))

        if tile.color_group:
            col = GROUP_COLORS.get(tile.color_group, (100, 100, 100))
            pygame.draw.rect(surface, col, (m.x + 28, m.y + 82, m.width - 56, 8), border_radius=3)

        f_info = get_font(16)
        surface.blit(f_info.render(f"Harga Beli: {format_rupiah(tile.purchase_price)}", True, C_GOLD), (m.x + 30, m.y + 115))
        surface.blit(f_info.render(f"Sewa Dasar: {format_rupiah(tile.rent_table[0]) if tile.rent_table else 'Variatif'}", True, (170, 195, 205)), (m.x + 30, m.y + 145))
        surface.blit(f_info.render(f"Uang Kas Anda: {format_rupiah(cp.cash)}", True, C_SUCCESS), (m.x + 30, m.y + 175))

        # 2.5D Property artwork box
        art_w = m.width - 60
        art_h = 110
        art_rect = pygame.Rect(m.x + 30, m.y + 208, art_w, art_h)
        grp_k = _GROUP_KEY.get(tile.color_group, "") if tile.color_group else ""
        draw_property_card_artwork(surface, art_rect, grp_k, tile.name)

        self._build_property_decision_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _handle_property_decision_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_property_decision_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                self._refresh()
                break

    # 3. AUCTION MODAL
    def _build_auction_buttons(self, m: pygame.Rect) -> None:
        auc = self.engine.auction
        if not auc:
            self.modal_buttons = []
            return
        cur_bidder_id = auc.get_current_bidder_id()
        cur_bidder = self.engine.get_player(cur_bidder_id) if cur_bidder_id is not None else None
        self.modal_buttons = []
        if cur_bidder:
            bx = m.x + 25
            by = m.y + 205
            bw = (m.width - 65) // 3
            inc_100k = auc.minimum_next_bid
            inc_500k = auc.highest_bid + 500000 if auc.highest_bid > 0 else 500000
            inc_1m = auc.highest_bid + 1000000 if auc.highest_bid > 0 else 1000000

            def bid(amt):
                ok, _ = self.engine.place_auction_bid(cur_bidder.id, amt)
                if ok:
                    AudioManager.get_instance().play_sfx("buy")

            def pass_b():
                self.engine.pass_auction_bid(cur_bidder.id)

            b1 = Button(pygame.Rect(bx, by, bw, 42), "+100rb", lambda: bid(inc_100k), bg_color=(52, 152, 219), is_enabled=cur_bidder.can_afford(inc_100k), border_radius=8)
            b2 = Button(pygame.Rect(bx + bw + 8, by, bw, 42), "+500rb", lambda: bid(inc_500k), bg_color=(46, 160, 95), is_enabled=cur_bidder.can_afford(inc_500k), border_radius=8)
            b3 = Button(pygame.Rect(bx + (bw + 8) * 2, by, bw, 42), "+1Jt", lambda: bid(inc_1m), bg_color=C_GOLD, text_color=(25, 25, 25), is_enabled=cur_bidder.can_afford(inc_1m), border_radius=8)
            b_pass = Button(pygame.Rect(bx, by + 56, m.width - 50, 44), "PAS / MUNDUR DARI LELANG", pass_b, bg_color=(195, 55, 50), border_radius=8)

            self.modal_buttons = [b1, b2, b3, b_pass]

    def _draw_auction_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        auc = self.engine.auction
        if not auc:
            return

        f_top = get_font(18, bold=True)
        surface.blit(f_top.render(f"LELANG TERBUKA: {auc.tile.name}", True, C_GOLD), (m.x + 28, m.y + 20))

        cur_bidder_id = auc.get_current_bidder_id()
        cur_bidder = self.engine.get_player(cur_bidder_id) if cur_bidder_id is not None else None
        highest_bidder = self.engine.get_player(auc.highest_bidder_id) if auc.highest_bidder_id is not None else None

        f_info = get_font(15)
        surface.blit(f_info.render(f"Tawaran Tertinggi: {format_rupiah(auc.highest_bid)}", True, C_SUCCESS), (m.x + 30, m.y + 65))
        surface.blit(f_info.render(f"Oleh: {highest_bidder.name if highest_bidder else 'Belum ada tawaran'}", True, (170, 195, 205)), (m.x + 30, m.y + 95))
        surface.blit(f_info.render(f"Giliran Menawar: {cur_bidder.name if cur_bidder else '-'}", True, cur_bidder.color if cur_bidder else C_TEXT_LIGHT), (m.x + 30, m.y + 125))
        surface.blit(f_info.render(f"Minimal Tawaran: {format_rupiah(auc.minimum_next_bid)}", True, C_GOLD), (m.x + 30, m.y + 155))

        self._build_auction_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _handle_auction_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_auction_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                self._refresh()
                break

    # 4. CARD MODAL
    def _build_card_buttons(self, m: pygame.Rect) -> None:
        card = self.engine.current_card
        if not card:
            self.modal_buttons = []
            return
        is_chance = (card.deck == "chance")
        deck_col = C_GOLD if is_chance else C_TEAL

        def on_continue():
            AudioManager.get_instance().play_sfx("card")
            self.engine.apply_current_card()

        b_ok = Button(pygame.Rect(m.centerx - 100, m.bottom - 68, 200, 46), "LANJUTKAN", on_continue, bg_color=deck_col, border_radius=10)
        self.modal_buttons = [b_ok]

    def _draw_card_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        card = self.engine.current_card
        if not card:
            return

        is_chance = (card.deck == "chance")
        deck_col = C_GOLD if is_chance else C_TEAL
        deck_name = "KARTU KESEMPATAN NUSANTARA" if is_chance else "KARTU DANA UMUM NUSANTARA"

        # Styled card surface with batik trim
        card_surf = make_card_surf(m.width, m.height, is_chance)
        surface.blit(card_surf, m.topleft)

        f_hdr = get_font(18, bold=True)
        surface.blit(f_hdr.render(deck_name, True, deck_col), (m.x + 30, m.y + 25))

        f_title = get_font(22, bold=True)
        surface.blit(f_title.render(card.title, True, C_TEXT_LIGHT), (m.x + 30, m.y + 60))

        f_desc = get_font(15)
        words = card.description.split(" ")
        lines = []
        cur_line = ""
        for w in words:
            if f_desc.size(cur_line + " " + w)[0] < m.width - 60:
                cur_line += " " + w if cur_line else w
            else:
                lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)

        dy = m.y + 105
        for l in lines:
            surface.blit(f_desc.render(l, True, (240, 245, 252)), (m.x + 30, dy))
            dy += 24

        # Thematic emblem in center
        draw_event_card_icon(surface, m.centerx, m.bottom - 135, is_chance)

        self._build_card_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _handle_card_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_card_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                self._refresh()
                break

    # 5. JAIL MODAL
    def _build_jail_buttons(self, m: pygame.Rect) -> None:
        p = self.engine.current_player
        if not p:
            self.modal_buttons = []
            return
        has_card = len(p.jail_cards) > 0
        can_afford_bail = p.can_afford(self.engine.board.jail_bail)

        def on_bail():
            ok, _ = self.engine.pay_jail_bail()
            if ok:
                AudioManager.get_instance().play_sfx("buy")

        def on_use_card():
            ok, _ = self.engine.use_jail_card()
            if ok:
                AudioManager.get_instance().play_sfx("card")

        def on_roll():
            self.engine.roll_jail_doubles()

        b1 = Button(pygame.Rect(m.x + 30, m.y + 180, m.width - 60, 42), f"Bayar Jaminan {format_rupiah(self.engine.board.jail_bail)}", on_bail, bg_color=(46, 160, 95), is_enabled=can_afford_bail, border_radius=8)
        b2 = Button(pygame.Rect(m.x + 30, m.y + 232, m.width - 60, 42), "Gunakan Kartu Bebas Penjara", on_use_card, bg_color=(52, 152, 219), is_enabled=has_card, border_radius=8)
        b3 = Button(pygame.Rect(m.x + 30, m.y + 284, m.width - 60, 42), "Lempar Dadu Kembar", on_roll, bg_color=C_GOLD, text_color=(25, 25, 25), border_radius=8)

        self.modal_buttons = [b1, b2, b3]

    def _draw_jail_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        p = self.engine.current_player

        f_hdr = get_font(20, bold=True)
        surface.blit(f_hdr.render("PENJARA KOTA NUSANTARA", True, COLOR_DANGER), (m.x + 30, m.y + 20))

        f_info = get_font(15)
        surface.blit(f_info.render(f"Masa tahanan: {p.jail_turns} dari maksimal 3 putaran.", True, (170, 195, 205)), (m.x + 30, m.y + 60))

        # Illustrated iron jail bars
        bars_rect = pygame.Rect(m.x + 30, m.y + 92, m.width - 60, 72)
        draw_jail_bars_art(surface, bars_rect)

        self._build_jail_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _handle_jail_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_jail_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                self._refresh()
                break

    # 6. DEBT RESOLUTION MODAL
    def _build_debt_buttons(self, m: pygame.Rect) -> None:
        p = self.engine.current_player
        if not p:
            self.modal_buttons = []
            return
        can_pay = p.can_afford(self.engine.debt_amount)

        def on_pay():
            ok, _ = self.engine.pay_debt()
            if ok:
                AudioManager.get_instance().play_sfx("buy")

        def on_bankrupt():
            AudioManager.get_instance().play_sfx("bankruptcy")
            self.engine.declare_bankruptcy()

        b1 = Button(pygame.Rect(m.x + 30, m.y + 200, m.width - 60, 42), "LUNASI UTANG SEKARANG", on_pay, bg_color=(46, 160, 95), is_enabled=can_pay, border_radius=8)
        b2 = Button(pygame.Rect(m.x + 30, m.y + 252, m.width - 60, 42), "KELOLA ASET (JUAL BANGUNAN / GADAI)", self._open_manage, bg_color=(225, 130, 40), border_radius=8)
        b3 = Button(pygame.Rect(m.x + 30, m.y + 304, m.width - 60, 42), "NYATAKAN BANGKRUT (MENYERAH)", on_bankrupt, bg_color=(195, 55, 50), border_radius=8)

        self.modal_buttons = [b1, b2, b3]

    def _draw_debt_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        p = self.engine.current_player

        f_hdr = get_font(20, bold=True)
        surface.blit(f_hdr.render("PENYELESAIAN KEWAJIBAN UTANG", True, COLOR_DANGER), (m.x + 30, m.y + 20))

        creditor = self.engine.get_player(self.engine.debt_creditor_id) if self.engine.debt_creditor_id is not None else None
        creditor_name = creditor.name if creditor else "Bank Negara"

        f_info = get_font(15)
        surface.blit(f_info.render(f"Alasan: {self.engine.debt_reason}", True, (170, 195, 205)), (m.x + 30, m.y + 60))
        surface.blit(f_info.render(f"Jumlah Utang: {format_rupiah(self.engine.debt_amount)}", True, COLOR_DANGER), (m.x + 30, m.y + 90))
        surface.blit(f_info.render(f"Kepada: {creditor_name}", True, C_GOLD), (m.x + 30, m.y + 120))
        surface.blit(f_info.render(f"Uang Kas Tersedia: {format_rupiah(p.cash)}", True, C_SUCCESS), (m.x + 30, m.y + 150))

        self._build_debt_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _handle_debt_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_debt_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                self._refresh()
                break

    # 7. GAME OVER MODAL
    def _build_game_over_buttons(self, m: pygame.Rect) -> None:
        b1 = Button(pygame.Rect(m.x + 30, m.bottom - 70, (m.width - 80) // 2, 46), "MAIN LAGI", self.on_main_menu, bg_color=(46, 160, 95), border_radius=10)
        b2 = Button(pygame.Rect(m.x + 40 + (m.width - 80) // 2, m.bottom - 70, (m.width - 80) // 2, 46), "MENU UTAMA", self.on_main_menu, bg_color=(50, 75, 95), border_radius=10)
        self.modal_buttons = [b1, b2]

    def _draw_game_over_modal(self, surface: pygame.Surface) -> None:
        m = self._draw_modal_backdrop(surface)
        winner = self.engine.winner

        f_hdr = get_font(26, bold=True)
        surface.blit(f_hdr.render("✦ PERMAINAN SELESAI! ✦", True, C_GOLD), f_hdr.render("✦ PERMAINAN SELESAI! ✦", True, C_GOLD).get_rect(center=(m.centerx, m.y + 28)))

        # Golden championship trophy cup
        draw_trophy_art(surface, m.centerx, m.y + 85, 46)

        f_win = get_font(22, bold=True)
        w_txt = f"Juara Tycoon: {winner.name if winner else 'Seri'}"
        surface.blit(f_win.render(w_txt, True, C_SUCCESS), f_win.render(w_txt, True, C_SUCCESS).get_rect(center=(m.centerx, m.y + 145)))

        if winner:
            f_info = get_font(15)
            surface.blit(f_info.render(f"Kas Akhir: {format_rupiah(winner.cash)}", True, C_TEXT_LIGHT), (m.x + 36, m.y + 180))
            surface.blit(f_info.render(f"Jumlah Properti: {len(winner.properties)} petak kota", True, C_TEXT_LIGHT), (m.x + 36, m.y + 208))
            surface.blit(f_info.render(f"Total Kekayaan Bersih: {format_rupiah(winner.get_net_worth(self.engine.board))}", True, C_GOLD), (m.x + 36, m.y + 236))
            surface.blit(f_info.render(f"Total Putaran: {self.engine.turn_count}", True, (170, 195, 205)), (m.x + 36, m.y + 264))

        self._build_game_over_buttons(m)
        for b in self.modal_buttons:
            b.draw(surface)

    def _handle_game_over_event(self, event: pygame.event.Event) -> None:
        if not self.modal_buttons:
            surf = pygame.display.get_surface()
            w = surf.get_width() if surf else 1440
            h = surf.get_height() if surf else 900
            mw, mh = min(580, w - 40), min(460, h - 40)
            m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
            self._build_game_over_buttons(m)
        for b in self.modal_buttons:
            if b.handle_event(event):
                break

    # 8. MANAGE ASSETS MODAL
    def _draw_manage_modal(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        surface.blit(dim, (0, 0))

        mw, mh = min(720, w - 40), min(560, h - 40)
        m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
        pygame.draw.rect(surface, (18, 32, 44), m, border_radius=14)
        pygame.draw.rect(surface, (60, 95, 120), m, width=2, border_radius=14)

        p = self.engine.current_player
        f_hdr = get_font(20, bold=True)
        surface.blit(f_hdr.render(f"PENGELOLAAN ASET — {p.name}", True, C_GOLD), (m.x + 25, m.y + 20))

        f_sub = get_font(13)
        surface.blit(f_sub.render(f"Kas: {format_rupiah(p.cash)} | Stok Bank: {self.engine.bank.houses} Rumah, {self.engine.bank.hotels} Hotel", True, (170, 195, 205)), (m.x + 25, m.y + 48))

        props = [self.engine.board.get_tile(pos) for pos in p.properties]
        self.modal_buttons = []

        if not props:
            f_empty = get_font(16)
            surface.blit(f_empty.render("Anda belum memiliki properti apa pun.", True, (170, 195, 205)), (m.x + 25, m.y + 100))
        else:
            y = m.y + 80
            for tile in props[:7]:
                c_rect = pygame.Rect(m.x + 20, y, m.width - 40, 52)
                pygame.draw.rect(surface, (25, 45, 60), c_rect, border_radius=8)

                if tile.color_group:
                    col = GROUP_COLORS.get(tile.color_group, (100, 100, 100))
                    pygame.draw.rect(surface, col, (c_rect.x, c_rect.y, 8, c_rect.height), border_radius=3)

                f_pname = get_font(14, bold=True)
                surface.blit(f_pname.render(tile.name, True, C_TEXT_LIGHT), (c_rect.x + 18, c_rect.y + 8))

                b_status = f"{tile.houses} Rumah" if tile.hotels == 0 else "1 Hotel"
                if tile.is_mortgaged:
                    b_status += " [TERGADAI]"
                f_pstat = get_font(12)
                surface.blit(f_pstat.render(b_status, True, C_GOLD), (c_rect.x + 18, c_rect.y + 28))

                btn_w = 95
                bx = c_rect.right - 10 - (btn_w * 3 + 12)

                def do_build(pos):
                    ok, _ = self.engine.build_house(pos)
                    if ok:
                        AudioManager.get_instance().play_sfx("build_house")

                def do_sell(pos):
                    ok, _ = self.engine.sell_building(pos)
                    if ok:
                        AudioManager.get_instance().play_sfx("buy")

                def do_mort(pos):
                    ok, _ = self.engine.mortgage_property(pos)
                    if ok:
                        AudioManager.get_instance().play_sfx("buy")

                def do_unmort(pos):
                    ok, _ = self.engine.unmortgage_property(pos)
                    if ok:
                        AudioManager.get_instance().play_sfx("buy")

                can_b, _ = Economy.can_build_on_property(tile, self.engine.board, self.engine.bank, p.cash)
                b_build = Button(pygame.Rect(bx, c_rect.y + 10, btn_w, 32), "Bangun", lambda pos=tile.position: do_build(pos), bg_color=(46, 160, 95), font_size=12, is_enabled=can_b, border_radius=6)
                self.modal_buttons.append(b_build)
                b_build.draw(surface)

                can_s, _ = Economy.can_sell_building_on_property(tile, self.engine.board)
                b_sell = Button(pygame.Rect(bx + btn_w + 6, c_rect.y + 10, btn_w, 32), "Jual Bangun", lambda pos=tile.position: do_sell(pos), bg_color=(225, 130, 40), font_size=12, is_enabled=can_s, border_radius=6)
                self.modal_buttons.append(b_sell)
                b_sell.draw(surface)

                if not tile.is_mortgaged:
                    can_m, _ = Economy.can_mortgage(tile, self.engine.board)
                    b_mort = Button(pygame.Rect(bx + (btn_w + 6) * 2, c_rect.y + 10, btn_w, 32), "Gadaikan", lambda pos=tile.position: do_mort(pos), bg_color=(195, 55, 50), font_size=12, is_enabled=can_m, border_radius=6)
                else:
                    can_un, _ = Economy.can_unmortgage(tile, p.cash)
                    b_mort = Button(pygame.Rect(bx + (btn_w + 6) * 2, c_rect.y + 10, btn_w, 32), "Tebus", lambda pos=tile.position: do_unmort(pos), bg_color=(52, 152, 219), font_size=12, is_enabled=can_un, border_radius=6)
                self.modal_buttons.append(b_mort)
                b_mort.draw(surface)

                y += 60

        b_close = Button(pygame.Rect(m.centerx - 80, m.bottom - 56, 160, 42), "TUTUP", self._close_manage, bg_color=(50, 75, 95), border_radius=8)
        self.modal_buttons.append(b_close)
        b_close.draw(surface)

    def _close_manage(self) -> None:
        self.show_manage_modal = False
        self._refresh()

    def _handle_manage_modal_event(self, event: pygame.event.Event) -> None:
        for b in self.modal_buttons:
            if b.handle_event(event):
                self._refresh()
                break

    # 9. TRADING MODAL
    def _draw_trade_modal(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        surface.blit(dim, (0, 0))

        mw, mh = min(720, w - 40), min(540, h - 40)
        m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
        pygame.draw.rect(surface, (18, 32, 44), m, border_radius=14)
        pygame.draw.rect(surface, (60, 95, 120), m, width=2, border_radius=14)

        p1 = self.engine.current_player
        p2 = self.engine.get_player(self.trade_partner_id) if self.trade_partner_id is not None else None

        f_hdr = get_font(20, bold=True)
        surface.blit(f_hdr.render("NEGOSIASI BISNIS ANTAR PEMAIN", True, C_GOLD), (m.x + 25, m.y + 20))

        f_lbl = get_font(14, bold=True)
        surface.blit(f_lbl.render("Pilih Mitra Dagang:", True, (170, 195, 205)), (m.x + 25, m.y + 55))

        self.modal_buttons = []
        opponents = [other for other in self.engine.active_players if other.id != p1.id]
        px = m.x + 160
        for opp in opponents:
            is_sel = (p2 and opp.id == p2.id)
            b_opp = Button(pygame.Rect(px, m.y + 50, 120, 32), opp.name, lambda oid=opp.id: self._select_partner(oid), bg_color=(46, 160, 95) if is_sel else (50, 75, 95), font_size=13, border_radius=6)
            self.modal_buttons.append(b_opp)
            b_opp.draw(surface)
            px += 130

        if p2:
            col_w = (m.width - 60) // 2
            pygame.draw.rect(surface, (25, 45, 60), (m.x + 20, m.y + 95, col_w, 350), border_radius=8)
            surface.blit(f_lbl.render(f"Tawaran ({p1.name}):", True, (46, 160, 95)), (m.x + 30, m.y + 105))

            f_c = get_font(13)
            surface.blit(f_c.render(f"Uang Kas: {format_rupiah(self.trade_offer_cash)}", True, C_GOLD), (m.x + 30, m.y + 135))
            b_add_c = Button(pygame.Rect(m.x + 30, m.y + 160, 60, 28), "+500k", lambda: self._add_offer_cash(500000), bg_color=(52, 152, 219), font_size=11, is_enabled=p1.can_afford(self.trade_offer_cash + 500000), border_radius=4)
            b_sub_c = Button(pygame.Rect(m.x + 95, m.y + 160, 60, 28), "-500k", lambda: self._add_offer_cash(-500000), bg_color=(195, 55, 50), font_size=11, is_enabled=self.trade_offer_cash >= 500000, border_radius=4)
            self.modal_buttons.extend([b_add_c, b_sub_c])
            b_add_c.draw(surface)
            b_sub_c.draw(surface)

            py = m.y + 200
            for pos in p1.properties[:4]:
                t = self.engine.board.get_tile(pos)
                is_offered = (pos in self.trade_offer_props)
                b_p = Button(pygame.Rect(m.x + 30, py, col_w - 20, 28), t.name, lambda p_pos=pos: self._toggle_offer_prop(p_pos), bg_color=(46, 160, 95) if is_offered else (45, 60, 75), font_size=12, border_radius=4)
                self.modal_buttons.append(b_p)
                b_p.draw(surface)
                py += 34

            col2_x = m.x + 30 + col_w
            pygame.draw.rect(surface, (25, 45, 60), (col2_x, m.y + 95, col_w, 350), border_radius=8)
            surface.blit(f_lbl.render(f"Permintaan ({p2.name}):", True, (52, 152, 219)), (col2_x + 10, m.y + 105))

            surface.blit(f_c.render(f"Uang Kas: {format_rupiah(self.trade_req_cash)}", True, C_GOLD), (col2_x + 10, m.y + 135))
            b_add_rc = Button(pygame.Rect(col2_x + 10, m.y + 160, 60, 28), "+500k", lambda: self._add_req_cash(500000), bg_color=(52, 152, 219), font_size=11, is_enabled=p2.can_afford(self.trade_req_cash + 500000), border_radius=4)
            b_sub_rc = Button(pygame.Rect(col2_x + 75, m.y + 160, 60, 28), "-500k", lambda: self._add_req_cash(-500000), bg_color=(195, 55, 50), font_size=11, is_enabled=self.trade_req_cash >= 500000, border_radius=4)
            self.modal_buttons.extend([b_add_rc, b_sub_rc])
            b_add_rc.draw(surface)
            b_sub_rc.draw(surface)

            py2 = m.y + 200
            for pos in p2.properties[:4]:
                t = self.engine.board.get_tile(pos)
                is_req = (pos in self.trade_req_props)
                b_p2 = Button(pygame.Rect(col2_x + 10, py2, col_w - 20, 28), t.name, lambda p_pos=pos: self._toggle_req_prop(p_pos), bg_color=(52, 152, 219) if is_req else (45, 60, 75), font_size=12, border_radius=4)
                self.modal_buttons.append(b_p2)
                b_p2.draw(surface)
                py2 += 34

        b_send = Button(pygame.Rect(m.centerx - 175, m.bottom - 60, 165, 44), "SEPAKATI TRANSAKSI", self._submit_trade, bg_color=(46, 160, 95), border_radius=8)
        b_cancel = Button(pygame.Rect(m.centerx + 10, m.bottom - 60, 165, 44), "BATAL", self._close_trade, bg_color=(50, 75, 95), border_radius=8)
        self.modal_buttons.extend([b_send, b_cancel])
        b_send.draw(surface)
        b_cancel.draw(surface)

    def _select_partner(self, oid: int) -> None:
        self.trade_partner_id = oid
        self.trade_req_cash = 0
        self.trade_req_props.clear()
        self._refresh()

    def _add_offer_cash(self, delta: int) -> None:
        self.trade_offer_cash = max(0, self.trade_offer_cash + delta)
        self._refresh()

    def _add_req_cash(self, delta: int) -> None:
        self.trade_req_cash = max(0, self.trade_req_cash + delta)
        self._refresh()

    def _toggle_offer_prop(self, pos: int) -> None:
        if pos in self.trade_offer_props:
            self.trade_offer_props.remove(pos)
        else:
            self.trade_offer_props.append(pos)
        self._refresh()

    def _toggle_req_prop(self, pos: int) -> None:
        if pos in self.trade_req_props:
            self.trade_req_props.remove(pos)
        else:
            self.trade_req_props.append(pos)
        self._refresh()

    def _submit_trade(self) -> None:
        if self.trade_partner_id is None:
            return
        offer = TradeOffer(
            sender_id=self.engine.current_player.id,
            receiver_id=self.trade_partner_id,
            offered_cash=self.trade_offer_cash,
            requested_cash=self.trade_req_cash,
            offered_properties=list(self.trade_offer_props),
            requested_properties=list(self.trade_req_props)
        )
        ok, msg = self.engine.execute_trade(offer)
        self.engine.log(msg)
        if ok:
            AudioManager.get_instance().play_sfx("buy")
        self.show_trade_modal = False
        self._refresh()

    def _close_trade(self) -> None:
        self.show_trade_modal = False
        self._refresh()

    def _handle_trade_modal_event(self, event: pygame.event.Event) -> None:
        for b in self.modal_buttons:
            if b.handle_event(event):
                break

    # 10. IN-GAME SETTINGS MODAL
    def _draw_settings_modal(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        surface.blit(dim, (0, 0))

        mw, mh = min(620, w - 40), min(480, h - 40)
        m = pygame.Rect((w - mw) // 2, (h - mh) // 2, mw, mh)
        pygame.draw.rect(surface, (18, 32, 44), m, border_radius=14)
        pygame.draw.rect(surface, (60, 95, 120), m, width=2, border_radius=14)

        f_hdr = get_font(22, bold=True)
        surface.blit(f_hdr.render("PENGATURAN PERMAINAN", True, C_GOLD), (m.x + 28, m.y + 20))

        f_lbl = get_font(15, bold=True)
        f_val = get_font(15)

        sy = m.y + 70
        surface.blit(f_lbl.render("Volume Utama:", True, (170, 195, 205)), (m.x + 30, sy + 6))
        surface.blit(f_val.render(f"{int(self.settings.master_volume * 100)}%", True, C_GOLD), (m.x + 220, sy + 6))

        surface.blit(f_lbl.render("Volume Musik (BGM):", True, (170, 195, 205)), (m.x + 30, sy + 56))
        surface.blit(f_val.render(f"{int(self.settings.music_volume * 100)}%", True, C_GOLD), (m.x + 220, sy + 56))

        surface.blit(f_lbl.render("Volume Efek (SFX):", True, (170, 195, 205)), (m.x + 30, sy + 106))
        surface.blit(f_val.render(f"{int(self.settings.sfx_volume * 100)}%", True, C_GOLD), (m.x + 220, sy + 106))

        surface.blit(f_lbl.render("Kecepatan Animasi:", True, (170, 195, 205)), (m.x + 30, sy + 156))
        surface.blit(f_val.render(f"{self.settings.animation_speed}", True, C_GOLD), (m.x + 220, sy + 156))

        surface.blit(f_lbl.render("Status Audio:", True, (170, 195, 205)), (m.x + 30, sy + 206))
        surface.blit(f_val.render("Bisu (Muted)" if self.settings.muted else "Aktif", True, COLOR_DANGER if self.settings.muted else C_SUCCESS), (m.x + 220, sy + 206))

        def wrap(fn):
            def inner():
                AudioManager.get_instance().play_sfx("click")
                fn()
            return inner

        self.modal_buttons = [
            # Master volume
            Button(pygame.Rect(m.right - 180, sy, 38, 30), "-", wrap(lambda: self._adjust_vol("master", -0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6),
            Button(pygame.Rect(m.right - 132, sy, 38, 30), "+", wrap(lambda: self._adjust_vol("master", 0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6),

            # Music volume
            Button(pygame.Rect(m.right - 180, sy + 50, 38, 30), "-", wrap(lambda: self._adjust_vol("music", -0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6),
            Button(pygame.Rect(m.right - 132, sy + 50, 38, 30), "+", wrap(lambda: self._adjust_vol("music", 0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6),

            # SFX volume
            Button(pygame.Rect(m.right - 180, sy + 100, 38, 30), "-", wrap(lambda: self._adjust_vol("sfx", -0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6),
            Button(pygame.Rect(m.right - 132, sy + 100, 38, 30), "+", wrap(lambda: self._adjust_vol("sfx", 0.1)), bg_color=(50, 75, 95), font_size=16, border_radius=6),

            # Speed
            Button(pygame.Rect(m.right - 180, sy + 150, 86, 30), "UBAH", wrap(self._cycle_speed), bg_color=(46, 160, 95), font_size=12, border_radius=6),

            # Mute
            Button(pygame.Rect(m.right - 180, sy + 200, 86, 30), "UNMUTE" if self.settings.muted else "MUTE", wrap(self._toggle_mute), bg_color=(195, 55, 50) if not self.settings.muted else (46, 160, 95), font_size=12, border_radius=6),

            # Close
            Button(pygame.Rect(m.centerx - 100, m.bottom - 56, 200, 42), "SIMPAN & KEMBALI", wrap(self._close_settings_modal), bg_color=(46, 160, 95), font_size=15, border_radius=8),
        ]
        for b in self.modal_buttons:
            b.draw(surface)

    def _adjust_vol(self, category: str, delta: float) -> None:
        if category == "master":
            self.settings.master_volume = max(0.0, min(1.0, round(self.settings.master_volume + delta, 2)))
        elif category == "music":
            self.settings.music_volume = max(0.0, min(1.0, round(self.settings.music_volume + delta, 2)))
        elif category == "sfx":
            self.settings.sfx_volume = max(0.0, min(1.0, round(self.settings.sfx_volume + delta, 2)))
        self.settings.apply_to_audio(AudioManager.get_instance())
        self._refresh()

    def _toggle_mute(self) -> None:
        self.settings.muted = not self.settings.muted
        self.settings.apply_to_audio(AudioManager.get_instance())
        self._refresh()

    def _cycle_speed(self) -> None:
        speeds = ["Normal", "Fast", "Instant"]
        cur_idx = speeds.index(self.settings.animation_speed) if self.settings.animation_speed in speeds else 0
        self.settings.animation_speed = speeds[(cur_idx + 1) % len(speeds)]
        self._refresh()

    def _close_settings_modal(self) -> None:
        self.settings.save()
        self.show_settings_modal = False
        self._refresh()

    def _handle_settings_modal_event(self, event: pygame.event.Event) -> None:
        for b in self.modal_buttons:
            if b.handle_event(event):
                break
