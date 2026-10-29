"""Comprehensive unit test suite for Nusantara Property Tycoon."""
import unittest
import os
import random
from game.state import GameState, TileType, PropertyColorGroup
from game.board import Board
from game.player import Player
from game.property import Tile
from game.dice import Dice
from game.economy import Economy, BankInventory, format_rupiah
from game.cards import CardManager, Card
from game.auction import Auction
from game.trading import TradeManager, TradeOffer
from game.save_manager import SaveManager
from game.engine import GameEngine


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_board_size_and_indexing(self):
        """Board has exactly 40 tiles indexed 0 to 39."""
        self.assertEqual(len(self.board.tiles), 40)
        for i, tile in enumerate(self.board.tiles):
            self.assertEqual(tile.position, i)

    def test_tile_ids_unique(self):
        """All tile IDs must be unique."""
        ids = [t.id for t in self.board.tiles]
        self.assertEqual(len(ids), len(set(ids)))

    def test_corners(self):
        """Verify the 4 corner tiles."""
        self.assertEqual(self.board.tiles[0].type, TileType.GO)
        self.assertEqual(self.board.tiles[10].type, TileType.JAIL)
        self.assertEqual(self.board.tiles[20].type, TileType.FREE_PARKING)
        self.assertEqual(self.board.tiles[30].type, TileType.GO_TO_JAIL)

    def test_color_groups_distribution(self):
        """Verify the 8 property color groups exist with correct tile counts."""
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.BROWN)), 2)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.LIGHT_BLUE)), 3)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.PINK)), 3)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.ORANGE)), 3)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.RED)), 3)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.YELLOW)), 3)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.GREEN)), 3)
        self.assertEqual(len(self.board.get_group_tiles(PropertyColorGroup.DARK_BLUE)), 2)

    def test_transport_and_utility_counts(self):
        """Verify 4 transports and 2 utilities."""
        transports = [t for t in self.board.tiles if t.type == TileType.TRANSPORT]
        utilities = [t for t in self.board.tiles if t.type == TileType.UTILITY]
        self.assertEqual(len(transports), 4)
        self.assertEqual(len(utilities), 2)


class TestDiceAndMovement(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "Pemain 1", "color": (255, 0, 0)},
            {"name": "Pemain 2", "color": (0, 0, 255)}
        ])

    def test_dice_roll_range(self):
        """Dice produce values between 1 and 6, total 2 to 12."""
        dice = Dice()
        for _ in range(100):
            d1, d2 = dice.roll()
            self.assertTrue(1 <= d1 <= 6)
            self.assertTrue(1 <= d2 <= 6)
            self.assertTrue(2 <= dice.total <= 12)

    def test_normal_movement(self):
        """Player moves forward by dice total."""
        p = self.engine.current_player
        self.assertEqual(p.position, 0)
        self.engine.roll_dice(fixed_values=(1, 2))  # total 3 (Depok)
        self.assertEqual(p.position, 3)

    def test_lap_passing_mulai(self):
        """Passing MULAI awards Rp2.000.000 salary."""
        p = self.engine.current_player
        p.position = 38
        starting_cash = p.cash
        self.engine.roll_dice(fixed_values=(2, 3))  # 38 + 5 = 43 -> pos 3
        self.assertEqual(p.position, 3)
        self.assertEqual(p.cash, starting_cash + 2000000)

    def test_double_grants_extra_roll(self):
        """Rolling doubles grants extra turn."""
        self.engine.roll_dice(fixed_values=(3, 3))  # lands on pos 6 (Tangerang)
        self.assertTrue(self.engine.rolled_double)
        self.assertEqual(self.engine.state, GameState.PROPERTY_DECISION)
        self.engine.buy_current_property()
        # Because of double roll, player stays in WAITING_FOR_ROLL for extra turn
        self.assertEqual(self.engine.state, GameState.WAITING_FOR_ROLL)

    def test_three_consecutive_doubles_sends_to_jail(self):
        """Three consecutive doubles sends player to jail immediately without normal 3rd move."""
        self.engine.dice.consecutive_doubles = 2
        p = self.engine.current_player
        self.engine.roll_dice(fixed_values=(3, 3))
        self.assertTrue(p.in_jail)
        self.assertEqual(p.position, 10)
        self.assertEqual(self.engine.state, GameState.TURN_END)


class TestPropertyPurchaseAndRent(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_purchase_property(self):
        """Player can buy unowned property when landing on it."""
        p1 = self.engine.current_player
        self.engine.roll_dice(fixed_values=(1, 0))  # pos 1 (Bogor, price 600.000)
        self.assertEqual(self.engine.state, GameState.PROPERTY_DECISION)

        initial_cash = p1.cash
        success, _ = self.engine.buy_current_property()
        self.assertTrue(success)
        tile = self.board_tile = self.engine.board.get_tile(1)
        self.assertEqual(tile.owner_id, p1.id)
        self.assertEqual(p1.cash, initial_cash - tile.purchase_price)
        self.assertIn(1, p1.properties)

    def test_rent_unmonopolized(self):
        """Landing on opponent property incurs base rent."""
        tile = self.engine.board.get_tile(1)
        tile.owner_id = 1  # Owned by P2
        self.engine.board.get_tile(1).owner_id = 1

        p1 = self.engine.current_player
        p2 = self.engine.get_player(1)
        p1_initial = p1.cash
        p2_initial = p2.cash

        self.engine.roll_dice(fixed_values=(1, 0))  # Land on Bogor (base rent 20.000)
        self.assertEqual(p1.cash, p1_initial - 20000)
        self.assertEqual(p2.cash, p2_initial + 20000)

    def test_monopoly_double_rent(self):
        """Owning full color group doubles base rent on undeveloped properties."""
        # P2 owns Bogor (1) and Depok (3)
        self.engine.board.get_tile(1).owner_id = 1
        self.engine.board.get_tile(3).owner_id = 1

        p1 = self.engine.current_player
        p2 = self.engine.get_player(1)
        p1_initial = p1.cash
        p2_initial = p2.cash

        self.engine.roll_dice(fixed_values=(1, 0))  # Land on Bogor (monopoly rent 40.000)
        self.assertEqual(p1.cash, p1_initial - 40000)
        self.assertEqual(p2.cash, p2_initial + 40000)

    def test_mortgaged_property_no_rent(self):
        """Mortgaged property produces no rent."""
        tile = self.engine.board.get_tile(1)
        tile.owner_id = 1
        tile.is_mortgaged = True

        p1 = self.engine.current_player
        p1_initial = p1.cash
        self.engine.roll_dice(fixed_values=(1, 0))
        self.assertEqual(p1.cash, p1_initial)


class TestTransportAndUtilityRent(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_transport_rent_scaling(self):
        """Transport rent scales: 1 station = 250k, 2 = 500k, 3 = 1M, 4 = 2M."""
        t1 = self.engine.board.get_tile(5)   # Gambir
        t2 = self.engine.board.get_tile(15)  # Bandung
        t1.owner_id = 1
        t2.owner_id = 1

        rent = Economy.calculate_rent(t1, self.engine.board, 7)
        self.assertEqual(rent, 500000)

    def test_utility_rent_dice_multiplier(self):
        """Utility rent is 4x roll x 10.000 for 1 utility, 10x roll x 10.000 for 2."""
        u1 = self.engine.board.get_tile(12)  # Listrik
        u2 = self.engine.board.get_tile(28)  # Air
        u1.owner_id = 1

        rent_1 = Economy.calculate_rent(u1, self.engine.board, 8)
        self.assertEqual(rent_1, 40000 * 8)

        u2.owner_id = 1
        rent_2 = Economy.calculate_rent(u1, self.engine.board, 8)
        self.assertEqual(rent_2, 100000 * 8)


class TestBuildingsAndInventory(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_even_building_rule(self):
        """Must build evenly across color group."""
        p1 = self.engine.current_player
        b1 = self.engine.board.get_tile(1)
        b2 = self.engine.board.get_tile(3)
        b1.owner_id = p1.id
        b2.owner_id = p1.id
        p1.properties.extend([1, 3])

        # Build on b1
        success, _ = self.engine.build_house(1)
        self.assertTrue(success)
        self.assertEqual(b1.houses, 1)

        # Cannot build 2nd house on b1 before b2 has 1
        success, msg = self.engine.build_house(1)
        self.assertFalse(success)
        self.assertIn("merata", msg)

    def test_hotel_upgrade_and_inventory(self):
        """Upgrading to hotel returns 4 houses to bank inventory."""
        p1 = self.engine.current_player
        b1 = self.engine.board.get_tile(1)
        b2 = self.engine.board.get_tile(3)
        b1.owner_id = p1.id
        b2.owner_id = p1.id
        p1.properties.extend([1, 3])

        # Build 4 houses on each
        b1.houses = 4
        b2.houses = 4
        self.engine.bank.houses = 32 - 8  # 24 left

        # Upgrade b1 to hotel
        success, _ = self.engine.build_house(1)
        self.assertTrue(success)
        self.assertEqual(b1.houses, 0)
        self.assertEqual(b1.hotels, 1)
        self.assertEqual(self.engine.bank.houses, 28)  # 4 houses returned
        self.assertEqual(self.engine.bank.hotels, 11)  # 1 hotel taken


class TestAuctionSystem(unittest.TestCase):
    def test_auction_flow(self):
        """Turn-based auction where players pass until one winner remains."""
        tile = Tile(id="bogor", position=1, name="Bogor", type=TileType.PROPERTY, purchase_price=600000)
        auction = Auction(tile, eligible_player_ids=[0, 1, 2])

        # P0 bids 100.000
        ok, _ = auction.place_bid(0, 100000, 15000000)
        self.assertTrue(ok)
        self.assertEqual(auction.get_current_bidder_id(), 1)

        # P1 passes
        ok, _ = auction.pass_bid(1)
        self.assertTrue(ok)
        self.assertEqual(auction.get_current_bidder_id(), 2)

        # P2 passes
        ok, _ = auction.pass_bid(2)
        self.assertTrue(ok)

        # P0 should now be the winner
        self.assertTrue(auction.is_finished)
        self.assertEqual(auction.get_winner(), 0)
        self.assertEqual(auction.highest_bid, 100000)


class TestJailMechanics(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_landing_on_go_to_jail(self):
        """Landing on tile 30 sends player to jail immediately."""
        p = self.engine.current_player
        p.position = 28
        self.engine.roll_dice(fixed_values=(1, 1))  # lands on 30
        self.assertTrue(p.in_jail)
        self.assertEqual(p.position, 10)

    def test_pay_bail_escapes_jail(self):
        """Paying Rp500.000 allows player to leave jail and roll."""
        p = self.engine.current_player
        p.in_jail = True
        self.engine.state = GameState.JAIL_DECISION
        initial_cash = p.cash
        ok, _ = self.engine.pay_jail_bail()
        self.assertTrue(ok)
        self.assertFalse(p.in_jail)
        self.assertEqual(p.cash, initial_cash - 500000)
        self.assertEqual(self.engine.state, GameState.WAITING_FOR_ROLL)


class TestTradingAndMortgage(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_mortgage_and_unmortgage(self):
        """Mortgage gives mortgage value, unmortgage costs +10% interest."""
        p1 = self.engine.current_player
        tile = self.engine.board.get_tile(1)
        tile.owner_id = p1.id
        p1.properties.append(1)

        initial_cash = p1.cash
        mort_val = tile.mortgage_value
        ok, _ = self.engine.mortgage_property(1)
        self.assertTrue(ok)
        self.assertTrue(tile.is_mortgaged)
        self.assertEqual(p1.cash, initial_cash + mort_val)

        # Unmortgage
        unmort_cost = int(mort_val * 1.10)
        ok, _ = self.engine.unmortgage_property(1)
        self.assertTrue(ok)
        self.assertFalse(tile.is_mortgaged)
        self.assertEqual(p1.cash, initial_cash + mort_val - unmort_cost)

    def test_trade_properties(self):
        """Players can trade properties and cash atomically."""
        p1 = self.engine.get_player(0)
        p2 = self.engine.get_player(1)

        t1 = self.engine.board.get_tile(1)
        t2 = self.engine.board.get_tile(3)
        t1.owner_id = p1.id
        p1.properties.append(1)
        t2.owner_id = p2.id
        p2.properties.append(3)

        offer = TradeOffer(
            sender_id=p1.id,
            receiver_id=p2.id,
            offered_cash=100000,
            requested_cash=0,
            offered_properties=[1],
            requested_properties=[3]
        )

        ok, msg = self.engine.execute_trade(offer)
        self.assertTrue(ok)
        self.assertEqual(t1.owner_id, p2.id)
        self.assertEqual(t2.owner_id, p1.id)
        self.assertIn(3, p1.properties)
        self.assertIn(1, p2.properties)


class TestBankruptcyAndGameOver(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_bankruptcy_declares_winner(self):
        """When player declares bankruptcy in 2-player game, other player wins."""
        p1 = self.engine.current_player
        self.engine.state = GameState.DEBT_RESOLUTION
        self.engine.debt_amount = 50000000
        self.engine.debt_creditor_id = 1

        ok, _ = self.engine.declare_bankruptcy()
        self.assertTrue(ok)
        self.assertTrue(p1.is_bankrupt)
        self.assertEqual(self.engine.state, GameState.GAME_OVER)
        self.assertEqual(self.engine.winner.id, 1)


class TestSaveAndLoad(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_save_and_restore_state(self):
        """Engine can be serialized to JSON and cleanly restored."""
        p = self.engine.current_player
        p.cash = 9999999
        p.position = 14
        save_dict = self.engine.to_dict()

        ok, _ = SaveManager.save_game(save_dict, filename="test_save.json")
        self.assertTrue(ok)

        loaded_data, msg = SaveManager.load_game("test_save.json")
        self.assertIsNotNone(loaded_data)

        new_engine = GameEngine()
        new_engine.load_dict(loaded_data)
        self.assertEqual(new_engine.current_player.cash, 9999999)
        self.assertEqual(new_engine.current_player.position, 14)

        # Cleanup
        path = SaveManager.get_save_path("test_save.json")
        if os.path.exists(path):
            os.remove(path)


class TestCardEffects(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.initialize_game([
            {"name": "P1", "color": (255, 0, 0)},
            {"name": "P2", "color": (0, 0, 255)}
        ])

    def test_card_receive_and_pay(self):
        """Card can grant or deduct money."""
        p = self.engine.current_player
        init_cash = p.cash

        # Receive money card
        card_receive = Card(id="c1", deck="chance", title="Hadiah", description="", action_type="receive_money", amount=500000)
        self.engine.current_card = card_receive
        self.engine.state = GameState.CARD_RESOLUTION
        self.engine.apply_current_card()
        self.assertEqual(p.cash, init_cash + 500000)

        # Pay money card
        card_pay = Card(id="c2", deck="chance", title="Denda", description="", action_type="pay_money", amount=300000)
        self.engine.current_card = card_pay
        self.engine.state = GameState.CARD_RESOLUTION
        self.engine.apply_current_card()
        self.assertEqual(p.cash, init_cash + 200000)

    def test_card_move_to_tile(self):
        """Card moves player to specific tile with go reward if passed."""
        p = self.engine.current_player
        p.position = 35
        init_cash = p.cash
        card = Card(id="c3", deck="chance", title="Maju ke Gambir", description="", action_type="move_to_tile", target_position=5, pass_go_reward=True)
        self.engine.current_card = card
        self.engine.state = GameState.CARD_RESOLUTION
        self.engine.apply_current_card()
        self.assertEqual(p.position, 5)
        self.assertEqual(p.cash, init_cash + 2000000)  # Passed MULAI

    def test_card_pay_each_player(self):
        """Card forces player to pay each other player."""
        p1 = self.engine.get_player(0)
        p2 = self.engine.get_player(1)
        p1_cash = p1.cash
        p2_cash = p2.cash

        card = Card(id="c4", deck="chance", title="Traktir", description="", action_type="pay_each_player", amount=200000)
        self.engine.current_card = card
        self.engine.state = GameState.CARD_RESOLUTION
        self.engine.apply_current_card()

        self.assertEqual(p1.cash, p1_cash - 200000)
        self.assertEqual(p2.cash, p2_cash + 200000)

    def test_card_repairs(self):
        """Card calculates building repair bill based on houses and hotels."""
        p = self.engine.current_player
        t1 = self.engine.board.get_tile(1)
        t2 = self.engine.board.get_tile(3)
        t1.owner_id = p.id
        t2.owner_id = p.id
        p.properties.extend([1, 3])
        t1.houses = 3
        t2.hotels = 1

        init_cash = p.cash
        # per_house = 250k, per_hotel = 1000k -> 3*250k + 1*1000k = 1.750.000
        card = Card(id="c5", deck="chance", title="Renovasi", description="", action_type="property_repairs", per_house=250000, per_hotel=1000000)
        self.engine.current_card = card
        self.engine.state = GameState.CARD_RESOLUTION
        self.engine.apply_current_card()

        self.assertEqual(p.cash, init_cash - 1750000)


if __name__ == "__main__":
    unittest.main()
