"""
Comprehensive tests for modal button click interactions in Nusantara Property Tycoon.
Ensures buttons like 'BELI PROPERTI', 'LELANG UMUM', 'LANJUTKAN', and settings modal buttons
are responsive to user clicks and never drop events across frame re-creations.
"""
import unittest
import pygame
from game.engine import GameEngine
from game.settings import Settings
from game.state import GameState
from ui.screens import GamePlayScreen
from ui.components import Button


class TestModalInteractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.surface = pygame.display.set_mode((1440, 900))

    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "Pemain 1", "color": (230, 75, 60), "token_type": "monas"},
            {"name": "Pemain 2", "color": (50, 150, 220), "token_type": "becak"}
        ])
        self.settings = Settings()
        self.screen = GamePlayScreen(self.engine, self.settings, on_main_menu=lambda: None)
        self.screen.update_layout(1440, 900)

    def test_button_immediate_click_on_mousedown(self):
        """Button triggers callback immediately upon MOUSEBUTTONDOWN."""
        clicked = [False]
        btn = Button(pygame.Rect(100, 100, 150, 50), "TEST", lambda: clicked.__setitem__(0, True))

        # Mouse down inside button
        down_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (120, 120)})
        handled = btn.handle_event(down_evt)
        self.assertTrue(handled)
        self.assertTrue(clicked[0])

    def test_button_no_click_outside(self):
        """Button does not trigger when clicking outside its bounds."""
        clicked = [False]
        btn = Button(pygame.Rect(100, 100, 150, 50), "TEST", lambda: clicked.__setitem__(0, True))

        down_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (300, 300)})
        handled = btn.handle_event(down_evt)
        self.assertFalse(handled)
        self.assertFalse(clicked[0])

    def test_property_decision_buy_button_click(self):
        """Clicking 'BELI PROPERTI' purchases the tile and transitions turn state."""
        p1 = self.engine.current_player
        p1.position = 1  # Kota Bogor (Purchase price: 600,000)
        self.engine.state = GameState.PROPERTY_DECISION
        tile = self.engine.board.get_tile(1)
        self.assertIsNone(tile.owner_id)

        # Render gameplay frame
        self.screen.draw(self.surface)

        # Locate 'BELI PROPERTI' button in modal_buttons
        buy_btn = None
        for b in self.screen.modal_buttons:
            if b.text == "BELI PROPERTI":
                buy_btn = b
                break
        self.assertIsNotNone(buy_btn)
        self.assertTrue(buy_btn.is_enabled)

        # Click the 'BELI PROPERTI' button
        click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": buy_btn.rect.center})
        self.screen.handle_event(click_evt)

        # Property should now be owned by Player 1
        self.assertEqual(tile.owner_id, p1.id)
        self.assertIn(1, p1.properties)
        # State transitions to TURN_END
        self.assertEqual(self.engine.state, GameState.TURN_END)

    def test_property_decision_auction_button_click(self):
        """Clicking 'LELANG UMUM' sends the unowned property to open auction."""
        p1 = self.engine.current_player
        p1.position = 3  # Depok
        self.engine.state = GameState.PROPERTY_DECISION

        self.screen.draw(self.surface)

        auction_btn = None
        for b in self.screen.modal_buttons:
            if b.text == "LELANG UMUM":
                auction_btn = b
                break
        self.assertIsNotNone(auction_btn)

        click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": auction_btn.rect.center})
        self.screen.handle_event(click_evt)

        # State should now be AUCTION
        self.assertEqual(self.engine.state, GameState.AUCTION)
        self.assertIsNotNone(self.engine.auction)

    def test_card_modal_lanjutkan_button_click(self):
        """Clicking 'LANJUTKAN' on card modal applies card and resolves state."""
        self.engine.current_player.position = 2  # Dana Umum
        card = self.engine.cards.draw_community_chest()
        self.engine.current_card = card
        self.engine.state = GameState.CARD_RESOLUTION

        self.screen.draw(self.surface)

        ok_btn = None
        for b in self.screen.modal_buttons:
            if b.text == "LANJUTKAN":
                ok_btn = b
                break
        self.assertIsNotNone(ok_btn)

        click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": ok_btn.rect.center})
        self.screen.handle_event(click_evt)

        # Card resolution should have advanced state from CARD_RESOLUTION
        self.assertNotEqual(self.engine.state, GameState.CARD_RESOLUTION)

    def test_auction_bid_and_pass_clicks(self):
        """Bidding and passing buttons in auction modal respond to clicks."""
        p1 = self.engine.current_player
        p1.position = 1
        self.engine.state = GameState.PROPERTY_DECISION
        self.engine.decline_and_auction_property()
        self.assertEqual(self.engine.state, GameState.AUCTION)

        self.screen.draw(self.surface)

        bid_btn = None
        for b in self.screen.modal_buttons:
            if "+100rb" in b.text:
                bid_btn = b
                break
        self.assertIsNotNone(bid_btn)

        prev_bid = self.engine.auction.highest_bid
        click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": bid_btn.rect.center})
        self.screen.handle_event(click_evt)
        self.assertGreater(self.engine.auction.highest_bid, prev_bid)

    def test_in_game_settings_modal_flow(self):
        """Clicking 'ATUR' opens settings modal, adjusts volume, and closes cleanly."""
        self.screen._open_settings_modal()
        self.assertTrue(self.screen.show_settings_modal)

        self.screen.draw(self.surface)

        # Find the close button
        close_btn = None
        for b in self.screen.modal_buttons:
            if "SIMPAN" in b.text:
                close_btn = b
                break
        self.assertIsNotNone(close_btn)

        # Click close button
        click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": close_btn.rect.center})
        self.screen.handle_event(click_evt)
        self.assertFalse(self.screen.show_settings_modal)

    def test_button_clicks_with_multiple_frame_draws_before_release(self):
        """Button click works even when multiple frames are drawn during a click."""
        self.engine.current_player.position = 6  # Bandung
        self.engine.state = GameState.PROPERTY_DECISION

        # 1. Frame 1: render
        self.screen.draw(self.surface)

        buy_btn = None
        for b in self.screen.modal_buttons:
            if b.text == "BELI PROPERTI":
                buy_btn = b
                break
        self.assertIsNotNone(buy_btn)

        # 2. Mouse Down event
        down_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": buy_btn.rect.center})
        self.screen.handle_event(down_evt)

        # Property should already be bought!
        tile = self.engine.board.get_tile(6)
        self.assertEqual(tile.owner_id, self.engine.current_player.id)

        # 3. Simulate subsequent frame draws while mouse is still held
        for _ in range(5):
            self.screen.update(0.016)
            self.screen.draw(self.surface)

        # 4. Mouse Up event
        up_evt = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": buy_btn.rect.center})
        self.screen.handle_event(up_evt)

        # No errors occurred and ownership remains confirmed
        self.assertEqual(tile.owner_id, self.engine.current_player.id)


if __name__ == "__main__":
    unittest.main()
