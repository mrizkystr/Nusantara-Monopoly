"""Unit and integration tests for STEP 2 features:
Visual design, Indonesian cultural tokens, audio system, animation engine, and settings.
"""
import os
import tempfile
import unittest
import pygame
from game.settings import Settings
from game.engine import GameEngine
from game.state import GameState
from ui.tokens import TokenRenderer, TOKEN_TYPES
from ui.audio import SoundGenerator, AudioManager
from ui.animation import DiceAnimation, MovementAnimation, ToastManager
from ui.renderer import BoardRenderer
from ui.screens import SettingsScreen, GamePlayScreen


class TestStep2Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        # Headless dummy video driver for tests
        cls.screen = pygame.display.set_mode((1440, 900))

    def test_settings_persistence(self):
        """Settings load, modify, and save properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_get_path = Settings.get_path
            try:
                test_path = os.path.join(tmpdir, "test_settings.json")
                Settings.get_path = classmethod(lambda cls: test_path)

                # Default load
                s1 = Settings.load()
                self.assertEqual(s1.animation_speed, "Normal")
                self.assertFalse(s1.muted)

                # Modify and save
                s1.animation_speed = "Fast"
                s1.master_volume = 0.65
                s1.muted = True
                s1.save()

                # Re-load
                s2 = Settings.load()
                self.assertEqual(s2.animation_speed, "Fast")
                self.assertAlmostEqual(s2.master_volume, 0.65)
                self.assertTrue(s2.muted)
                self.assertTrue(s2.is_muted)
            finally:
                Settings.get_path = orig_get_path

    def test_all_token_types_render(self):
        """All 6 original Indonesian cultural vector tokens render without error."""
        surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        color = (231, 76, 60)
        center = (100, 100)
        radius = 20

        for token in TOKEN_TYPES:
            token_id = token[0]
            surf.fill((0, 0, 0, 0))
            # Test non-active render
            TokenRenderer.draw_token(surf, token_id, center, radius, color, is_active=False)
            # Test active glow render
            TokenRenderer.draw_token(surf, token_id, center, radius, color, is_active=True)

    def test_audio_generator_and_manager(self):
        """Sound generator creates valid 16-bit PCM WAV assets and manager applies volume."""
        with tempfile.TemporaryDirectory() as tmpdir:
            SoundGenerator.generate_all(tmpdir)
            sfx_click = os.path.join(tmpdir, "assets", "audio", "sfx", "click.wav")
            bgm_loop = os.path.join(tmpdir, "assets", "audio", "music", "ambient_loop.wav")

            self.assertTrue(os.path.exists(sfx_click))
            self.assertTrue(os.path.exists(bgm_loop))
            self.assertGreater(os.path.getsize(sfx_click), 100)
            self.assertGreater(os.path.getsize(bgm_loop), 1000)

            # Test audio manager instance
            mgr = AudioManager.get_instance(base_dir=tmpdir)
            mgr.set_master_volume(0.5)
            self.assertAlmostEqual(mgr.master_volume, 0.5)
            mgr.set_mute(True)
            self.assertTrue(mgr.is_muted)
            mgr.toggle_mute()
            self.assertFalse(mgr.is_muted)

    def test_dice_animation_progression(self):
        """DiceAnimation updates through roll duration and fires callback."""
        dice_anim = DiceAnimation()
        completed = [False]

        def on_done():
            completed[0] = True

        dice_anim.start(target1=4, target2=6, speed="Normal", on_complete=on_done)
        self.assertTrue(dice_anim.is_active)

        # Advance delta-time
        dice_anim.update(0.3)
        self.assertTrue(dice_anim.is_active)
        self.assertFalse(completed[0])

        dice_anim.update(0.6)  # Total 0.9s exceeds normal roll duration 0.85s
        self.assertFalse(dice_anim.is_active)
        self.assertTrue(completed[0])
        self.assertEqual(dice_anim.face1, 4)
        self.assertEqual(dice_anim.face2, 6)

    def test_movement_animation_and_skip(self):
        """MovementAnimation handles step progression and skipping."""
        move_anim = MovementAnimation()
        completed = [False]

        def on_done():
            completed[0] = True

        # Move from tile 0 to 4 along path [0, 1, 2, 3, 4]
        move_anim.start(
            path=[0, 1, 2, 3, 4],
            start_tile=0,
            target_tile=4,
            speed="Normal",
            on_complete=on_done
        )
        self.assertTrue(move_anim.is_active)
        self.assertEqual(move_anim.remaining_steps, 5)

        # Skip movement
        move_anim.skip()
        self.assertFalse(move_anim.is_active)
        self.assertEqual(move_anim.current_tile, 4)
        self.assertTrue(completed[0])

    def test_toast_manager(self):
        """ToastManager adds, fades, and draws floating messages."""
        tm = ToastManager()
        tm.add("Rp2.000.000 (Lewat MULAI)", color=(101, 189, 139))
        self.assertEqual(len(tm.toasts), 1)

        # Update 1.0s -> still alive
        tm.update(1.0)
        self.assertEqual(len(tm.toasts), 1)

        # Update 1.5s -> total 2.5s exceeds 2.2s duration, expires
        tm.update(1.5)
        self.assertEqual(len(tm.toasts), 0)

    def test_board_renderer_tile_hit_test(self):
        """BoardRenderer correctly maps screen coordinates to tile positions."""
        renderer = BoardRenderer()
        renderer.update_layout(1440, 900)

        # Tile 0 (MULAI) should be located at bottom-right of board
        rect0 = renderer.tile_rects.get(0)
        self.assertIsNotNone(rect0)

        hit = renderer.get_tile_at_pos(rect0.center)
        self.assertEqual(hit, 0)

        # Click outside board should return None
        self.assertIsNone(renderer.get_tile_at_pos((10, 10)))

    def test_deferred_movement_flow(self):
        """GameEngine deferred movement decouples dice roll from movement completion."""
        engine = GameEngine()
        engine.initialize_game([
            {"name": "P1", "color": (231, 76, 60), "token_type": "monas"},
            {"name": "P2", "color": (52, 152, 219), "token_type": "becak"}
        ])

        p1 = engine.current_player
        self.assertEqual(p1.position, 0)

        # Roll dice with fixed values
        ok, msg = engine.roll_dice(fixed_values=(2, 3), defer_movement=True)
        self.assertTrue(ok)
        self.assertIsNotNone(engine.pending_movement)

        # Position is still at starting tile 0 before animation finishes
        self.assertEqual(p1.position, 0)
        self.assertEqual(engine.pending_movement["target_pos"], 5)
        self.assertEqual(engine.pending_movement["path"], [1, 2, 3, 4, 5])

        # Complete movement
        engine.complete_deferred_movement()
        self.assertIsNone(engine.pending_movement)
        self.assertEqual(p1.position, 5)

    def test_transaction_notification_queue(self):
        """Engine transactions are logged and handled by GamePlayScreen."""
        engine = GameEngine()
        engine.initialize_game([
            {"name": "P1", "color": (231, 76, 60), "token_type": "monas"},
            {"name": "P2", "color": (52, 152, 219), "token_type": "becak"}
        ])
        settings = Settings()
        gps = GamePlayScreen(engine, settings, on_main_menu=lambda: None)

        engine.notify_transaction(player_id=0, amount=2000000, description="Bonus MULAI")
        self.assertEqual(len(engine.transactions), 1)

        gps.update(0.016)
        self.assertEqual(len(gps.toast_mgr.toasts), 1)
        self.assertIn("MULAI", gps.toast_mgr.toasts[0].text)

    def test_settings_screen_interactions(self):
        """SettingsScreen buttons cycle values."""
        settings = Settings()
        saved = [False]
        screen = SettingsScreen(settings, on_back=lambda: saved.append(True))
        screen.update_layout(1440, 900)

        # Verify buttons exist
        self.assertGreater(len(screen.buttons), 3)

        # Cycle animation speed
        initial_speed = settings.animation_speed
        screen._cycle_speed()
        self.assertNotEqual(settings.animation_speed, initial_speed)

        # Toggle mute
        screen._toggle_mute()
        self.assertTrue(settings.muted)


if __name__ == "__main__":
    unittest.main()
