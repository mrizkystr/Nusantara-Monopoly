"""Integration tests for UI screens, layout resizing, and modal rendering."""
import os
import unittest
# Force dummy video driver for headless environments
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
from main import NusantaraGameApp
from game.state import GameState


class TestUIFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    def setUp(self):
        self.app = NusantaraGameApp()

    def test_navigation_between_screens(self):
        """User can navigate between Main Menu, Setup, Rules, and Game."""
        self.assertEqual(self.app.current_screen_id, "MENU")

        # Open Rules
        self.app._open_rules()
        self.assertEqual(self.app.current_screen_id, "RULES")
        self.app.active_screen.draw(self.app.screen)

        # Back to Menu
        self.app._open_menu()
        self.assertEqual(self.app.current_screen_id, "MENU")

        # Open Setup
        self.app._open_setup()
        self.assertEqual(self.app.current_screen_id, "SETUP")
        self.app.active_screen.draw(self.app.screen)

        # Start match with 3 players
        configs = [
            {"name": "Konglomerat A", "color": (231, 76, 60)},
            {"name": "Konglomerat B", "color": (52, 152, 219)},
            {"name": "Konglomerat C", "color": (46, 204, 113)}
        ]
        self.app._start_match(configs)
        self.assertEqual(self.app.current_screen_id, "GAME")
        self.assertEqual(len(self.app.engine.players), 3)

        # Render gameplay screen
        self.app.active_screen.draw(self.app.screen)

    def test_gameplay_modals_render(self):
        """All gameplay modals render without crashing."""
        self.app._start_match([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])
        screen = self.app.gameplay_screen

        # Test Property Decision Modal
        self.app.engine.current_player.position = 1
        self.app.engine.state = GameState.PROPERTY_DECISION
        self.app.engine.pending_tile_pos = 1
        screen.draw(self.app.screen)

        # Test Auction Modal
        self.app.engine.decline_and_auction_property()
        self.assertEqual(self.app.engine.state, GameState.AUCTION)
        screen.draw(self.app.screen)

        # Test Jail Modal
        self.app.engine.state = GameState.JAIL_DECISION
        screen.draw(self.app.screen)

        # Test Debt Modal
        self.app.engine.state = GameState.DEBT_RESOLUTION
        self.app.engine.debt_amount = 1500000
        self.app.engine.debt_reason = "Uji coba utang"
        screen.draw(self.app.screen)

        # Test Manage Assets Modal
        self.app.engine.state = GameState.WAITING_FOR_ROLL
        screen.show_manage_modal = True
        screen.draw(self.app.screen)
        screen.show_manage_modal = False

        # Test Trade Modal
        screen._open_trade()
        self.assertTrue(screen.show_trade_modal)
        screen.draw(self.app.screen)
        screen.show_trade_modal = False

        # Test Game Over Modal
        self.app.engine.state = GameState.GAME_OVER
        self.app.engine.winner = self.app.engine.players[0]
        screen.draw(self.app.screen)

    def test_screen_resizing(self):
        """Layout dynamically updates on window resize."""
        self.app._start_match([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

        # Test minimum supported resolution 1100x700
        self.app.screen = pygame.display.set_mode((1100, 700))
        self.app.gameplay_screen.update_layout(1100, 700)
        self.app.gameplay_screen.draw(self.app.screen)

        # Test high resolution 1920x1080
        self.app.screen = pygame.display.set_mode((1920, 1080))
        self.app.gameplay_screen.update_layout(1920, 1080)
        self.app.gameplay_screen.draw(self.app.screen)


if __name__ == "__main__":
    unittest.main()
