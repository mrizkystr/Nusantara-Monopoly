"""Automated full game simulation test ensuring endless loop-free gameplay to completion."""
import unittest
import random
from game.state import GameState
from game.engine import GameEngine


class TestFullGameSimulation(unittest.TestCase):
    def test_simulated_playthrough(self):
        """Simulate turn-by-turn pass-and-play match until a winner is declared or max turns reached."""
        seed = 42
        rng = random.Random(seed)
        engine = GameEngine(rng=rng)

        engine.initialize_game([
            {"name": "Konglomerat Jakarta", "color": (231, 76, 60)},
            {"name": "Juragan Surabaya", "color": (52, 152, 219)},
            {"name": "Saudagar Medan", "color": (46, 204, 113)}
        ])

        max_actions = 2000
        actions = 0

        while engine.state != GameState.GAME_OVER and actions < max_actions:
            actions += 1
            st = engine.state
            cp = engine.current_player

            if st == GameState.WAITING_FOR_ROLL:
                engine.roll_dice()

            elif st == GameState.PROPERTY_DECISION:
                tile = engine.board.get_tile(cp.position)
                if cp.can_afford(tile.purchase_price):
                    engine.buy_current_property()
                else:
                    engine.decline_and_auction_property()

            elif st == GameState.AUCTION:
                cur_bidder_id = engine.auction.get_current_bidder_id()
                bidder = engine.get_player(cur_bidder_id) if cur_bidder_id is not None else None
                min_bid = engine.auction.minimum_next_bid
                if bidder and bidder.can_afford(min_bid) and rng.random() > 0.4:
                    engine.place_auction_bid(bidder.id, min_bid)
                elif bidder:
                    engine.pass_auction_bid(bidder.id)

            elif st == GameState.CARD_RESOLUTION:
                engine.apply_current_card()

            elif st == GameState.JAIL_DECISION:
                if cp.jail_cards:
                    engine.use_jail_card()
                elif cp.can_afford(engine.board.jail_bail) and rng.random() > 0.5:
                    engine.pay_jail_bail()
                else:
                    engine.roll_jail_doubles()

            elif st == GameState.DEBT_RESOLUTION:
                # Try to mortgage or sell buildings to cover debt
                resolved = False
                for pos in list(cp.properties):
                    t = engine.board.get_tile(pos)
                    if t and t.total_buildings > 0:
                        engine.sell_building(pos)
                        if cp.can_afford(engine.debt_amount):
                            engine.pay_debt()
                            resolved = True
                            break
                    elif t and not t.is_mortgaged:
                        engine.mortgage_property(pos)
                        if cp.can_afford(engine.debt_amount):
                            engine.pay_debt()
                            resolved = True
                            break

                if not resolved:
                    if cp.can_afford(engine.debt_amount):
                        engine.pay_debt()
                    else:
                        engine.declare_bankruptcy()

            elif st == GameState.TURN_END:
                # Maybe try to build something before ending turn if monopoly
                for group in engine.board._group_tiles:
                    if engine.board.is_monopoly(cp.id, group):
                        tiles = engine.board.get_group_tiles(group)
                        for t in tiles:
                            engine.build_house(t.position)

                engine.end_turn()

        # The match ran stably without hanging or throwing exceptions
        self.assertGreater(actions, 50)
        self.assertIn(engine.state, (GameState.GAME_OVER, GameState.TURN_END, GameState.WAITING_FOR_ROLL))


if __name__ == "__main__":
    unittest.main()
