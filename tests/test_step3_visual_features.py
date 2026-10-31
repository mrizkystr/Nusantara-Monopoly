"""
Tests for STEP 3 Visual Overhaul Features:
- 2.5D Dynamic Camera (Zoom, Pan, Screen-to-World mapping)
- Modern Mobile HUD (Top Bar, Action Dock, Opponent cards)
- Visual Assets (Backgrounds, Frames, House & Hotel sprites, Property Artwork)
- Animated Token Renderer (All 6 Indonesian tokens with animation)
- Cinematic Dice & Token Hop Animations
"""
import unittest
import pygame
from ui.camera import Camera, CameraState
from ui.hud import ModernHUD
from ui.tokens import TokenRenderer, TOKEN_TYPES
from ui.renderer import BoardRenderer
from ui.animation import DiceAnimation, MovementAnimation, ToastManager
from ui.visual_assets import (
    make_menu_background, make_game_background, make_board_frame,
    draw_house_sprite, draw_hotel_sprite, draw_property_card_artwork,
    draw_event_card_icon, draw_jail_bars_art, draw_trophy_art
)
from game.engine import GameEngine


class TestStep3VisualFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    def test_camera_zoom_and_pan(self):
        cam = Camera(1440, 900)
        self.assertEqual(cam.state, CameraState.BOARD_OVERVIEW)
        self.assertEqual(cam.zoom, 1.0)

        # Focus tile
        cam.focus_tile((600, 450), zoom=1.4, state=CameraState.PROPERTY_FOCUS)
        self.assertEqual(cam.state, CameraState.PROPERTY_FOCUS)
        self.assertEqual(cam.target_zoom, 1.4)
        self.assertEqual(cam.target_x, 600.0)
        self.assertEqual(cam.target_y, 450.0)

        # Update step advances towards target
        cam.update(0.1)
        self.assertGreater(cam.zoom, 1.0)

        # Reset to overview
        cam.reset_overview()
        self.assertEqual(cam.state, CameraState.BOARD_OVERVIEW)
        self.assertEqual(cam.target_zoom, 1.0)

    def test_camera_coordinate_mapping(self):
        cam = Camera(1000, 800)
        cam.set_viewport(1000, 800, default_center=(500, 400))
        # At 1.0 zoom centered at (500, 400), screen (500, 400) maps to world (500, 400)
        wx, wy = cam.screen_to_world((500, 400))
        self.assertEqual((wx, wy), (500, 400))

        sx, sy = cam.world_to_screen((500, 400))
        self.assertEqual((sx, sy), (500, 400))

    def test_all_six_tokens_render(self):
        surf = pygame.Surface((100, 100))
        for token_id, token_label, token_desc in TOKEN_TYPES:
            # Test static rendering
            TokenRenderer.draw_token(surf, token_id, (50, 50), radius=16, color=(230, 75, 60), is_active=False)
            # Test active animated rendering
            TokenRenderer.draw_token(surf, token_id, (50, 50), radius=16, color=(50, 150, 220), is_active=True, anim_time=1.2)
        # All 6 tokens rendered without error
        self.assertEqual(len(TOKEN_TYPES), 6)

    def test_visual_assets_generators(self):
        menu_bg = make_menu_background(800, 600)
        self.assertEqual(menu_bg.get_size(), (800, 600))

        game_bg = make_game_background(800, 600)
        self.assertEqual(game_bg.get_size(), (800, 600))

        frame = make_board_frame(500)
        self.assertEqual(frame.get_size(), (500, 500))

        # Test sprites
        surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        draw_house_sprite(surf, 50, 50, size=8, color=(60, 180, 100))
        draw_hotel_sprite(surf, 100, 50, size=12)
        draw_property_card_artwork(surf, pygame.Rect(10, 10, 180, 80), "pink", "Bandung")
        draw_event_card_icon(surf, 100, 100, is_chance=True)
        draw_event_card_icon(surf, 100, 100, is_chance=False)
        draw_jail_bars_art(surf, pygame.Rect(10, 10, 180, 80))
        draw_trophy_art(surf, 100, 100, size=30)

    def test_modern_hud_layout_and_cash_animation(self):
        engine = GameEngine()
        engine.initialize_game([
            {"name": "P1", "color": (230, 75, 60), "token_type": "monas"},
            {"name": "P2", "color": (50, 150, 220), "token_type": "becak"}
        ])
        hud = ModernHUD(
            on_roll_dice=lambda: None,
            on_end_turn=lambda: None,
            on_manage_assets=lambda: None,
            on_trade=lambda: None,
            on_save=lambda: None,
            on_settings=lambda: None,
            on_toggle_camera=lambda: None,
            on_main_menu=lambda: None
        )
        hud.update_layout(1440, 900, engine)
        self.assertGreater(len(hud.all_buttons), 0)

        # Cash interpolation
        hud.displayed_cash[0] = 10000000.0
        engine.players[0].cash = 15000000
        hud.update(0.1, engine)
        self.assertGreater(hud.displayed_cash[0], 10000000.0)

    def test_cinematic_dice_and_movement_animation(self):
        dice_anim = DiceAnimation(duration=0.5)
        dice_anim.start(3, 4, speed="Normal")
        self.assertTrue(dice_anim.is_active)
        dice_anim.update(0.1)
        self.assertNotEqual(dice_anim.bounce_y, 0.0)

        move_anim = MovementAnimation(step_duration=0.1)
        move_anim.start(path=[1, 2, 3], start_tile=0, target_tile=3, speed="Normal")
        self.assertTrue(move_anim.is_active)
        move_anim.update(0.05)
        self.assertLess(move_anim.hop_offset_y, 0.0)  # hopped upward

    def test_board_renderer_responsive_and_hit_test(self):
        renderer = BoardRenderer()
        renderer.update_layout(1280, 800)
        self.assertEqual(len(renderer.tile_rects), 40)
        self.assertGreater(renderer.board_rect.width, 400)

        # Tile 0 hit test
        t0_center = renderer.tile_rects[0].center
        self.assertEqual(renderer.get_tile_at_pos(t0_center), 0)


if __name__ == "__main__":
    unittest.main()
