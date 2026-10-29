"""Authoritative Game Engine orchestrating state, turns, mechanics, and rules."""
import random
from typing import List, Dict, Optional, Tuple, Any
from game.state import GameState, TileType, PropertyColorGroup
from game.board import Board
from game.player import Player
from game.property import Tile
from game.dice import Dice
from game.economy import Economy, BankInventory, format_rupiah
from game.cards import CardManager, Card
from game.auction import Auction
from game.trading import TradeManager, TradeOffer


class GameEngine:
    def __init__(
        self,
        board_config_path: Optional[str] = None,
        cards_config_path: Optional[str] = None,
        rng: Optional[random.Random] = None
    ):
        self.rng = rng if rng is not None else random.Random()
        self.board = Board(board_config_path)
        self.cards = CardManager(cards_config_path, rng=self.rng)
        self.dice = Dice(rng=self.rng)
        self.bank = BankInventory()

        self.players: List[Player] = []
        self.current_player_idx: int = 0
        self.turn_count: int = 0
        self.state: GameState = GameState.MAIN_MENU

        # Turn & Action contexts
        self.has_rolled: bool = False
        self.rolled_double: bool = False
        self.pending_tile_pos: Optional[int] = None
        self.current_card: Optional[Card] = None
        self.auction: Optional[Auction] = None
        self.pending_movement: Optional[Dict[str, Any]] = None
        self.transactions: List[Dict[str, Any]] = []

        # Debt resolution context
        self.debt_amount: int = 0
        self.debt_creditor_id: Optional[int] = None
        self.debt_reason: str = ""

        # Notification & Event log
        self.event_log: List[str] = []
        self.winner: Optional[Player] = None

    def log(self, message: str) -> None:
        """Add message to recent event log (max 100 entries)."""
        self.event_log.append(message)
        if len(self.event_log) > 100:
            self.event_log.pop(0)

    def notify_transaction(self, player_id: int, amount: int, description: str) -> None:
        """Record confirmed financial transaction for visual feedback."""
        self.transactions.append({
            "player_id": player_id,
            "amount": amount,
            "description": description
        })
        if len(self.transactions) > 30:
            self.transactions.pop(0)

    @property
    def current_player(self) -> Optional[Player]:
        """Return the player whose turn it currently is."""
        if not self.players:
            return None
        return self.players[self.current_player_idx]

    @property
    def active_players(self) -> List[Player]:
        """Return list of non-bankrupt players."""
        return [p for p in self.players if not p.is_bankrupt]

    def get_player(self, player_id: int) -> Optional[Player]:
        """Find player by ID."""
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    # ---------------------------------------------------------
    # GAME INITIALIZATION
    # ---------------------------------------------------------
    def initialize_game(self, player_configs: List[Dict[str, Any]]) -> None:
        """
        Start a new game with 2-4 configured players.
        Each config dict: {'name': str, 'color': (R, G, B)}
        """
        if not (2 <= len(player_configs) <= 4):
            raise ValueError("Permainan harus memiliki antara 2 hingga 4 pemain.")

        self.players = []
        for idx, cfg in enumerate(player_configs):
            p = Player(
                id=idx,
                name=cfg["name"],
                color=tuple(cfg["color"]),
                cash=15000000,
                position=0,
                token_type=cfg.get("token_type", "monas")
            )
            self.players.append(p)

        # Reset board state
        for tile in self.board.tiles:
            tile.reset_ownership()

        # Reset bank inventory
        self.bank = BankInventory()

        # Reset contexts
        self.current_player_idx = 0
        self.turn_count = 1
        self.has_rolled = False
        self.rolled_double = False
        self.pending_tile_pos = None
        self.current_card = None
        self.auction = None
        self.debt_amount = 0
        self.debt_creditor_id = None
        self.winner = None
        self.event_log.clear()

        self.log("Permainan Nusantara Property Tycoon dimulai!")
        self.log(f"Giliran pertama: {self.current_player.name}")
        self._start_turn()

    def _start_turn(self) -> None:
        """Internal helper to begin the active player's turn."""
        p = self.current_player
        if p is None or p.is_bankrupt:
            self._advance_turn()
            return

        self.has_rolled = False
        self.rolled_double = False
        self.pending_tile_pos = None

        if p.in_jail:
            self.state = GameState.JAIL_DECISION
            self.log(f"{p.name} berada di Penjara (Masa tahanan: {p.jail_turns} giliran).")
        else:
            self.state = GameState.WAITING_FOR_ROLL

    # ---------------------------------------------------------
    # JAIL MECHANICS
    # ---------------------------------------------------------
    def pay_jail_bail(self) -> Tuple[bool, str]:
        """Pay Rp500.000 bail to immediately leave jail."""
        if self.state != GameState.JAIL_DECISION:
            return False, "Bukan saatnya mengambil keputusan penjara."

        p = self.current_player
        bail = self.board.jail_bail

        if p.can_afford(bail):
            p.deduct_cash(bail)
            self.notify_transaction(p.id, -bail, "Jaminan Penjara")
            p.in_jail = False
            p.jail_turns = 0
            self.log(f"{p.name} membayar uang jaminan {format_rupiah(bail)} dan bebas dari penjara.")
            self.state = GameState.WAITING_FOR_ROLL
            return True, "Bebas dari penjara."
        else:
            # Cannot afford bail -> initiate debt resolution to bank
            self.debt_amount = bail
            self.debt_creditor_id = None
            self.debt_reason = "Membayar uang jaminan bebas penjara"
            self.state = GameState.DEBT_RESOLUTION
            return False, f"Uang kas tidak cukup untuk membayar jaminan {format_rupiah(bail)}."

    def use_jail_card(self) -> Tuple[bool, str]:
        """Use a Get Out of Jail Free card."""
        if self.state != GameState.JAIL_DECISION:
            return False, "Bukan saatnya mengambil keputusan penjara."

        p = self.current_player
        if not p.jail_cards:
            return False, "Anda tidak memiliki Kartu Bebas Penjara."

        card_id = p.jail_cards.pop(0)
        card = self.cards.get_card_by_id(card_id)
        if card:
            self.cards.return_card(card)

        p.in_jail = False
        p.jail_turns = 0
        self.log(f"{p.name} menggunakan Kartu Bebas Penjara dan langsung bebas.")
        self.state = GameState.WAITING_FOR_ROLL
        return True, "Bebas dari penjara menggunakan kartu."

    def roll_jail_doubles(self, fixed_values: Optional[Tuple[int, int]] = None) -> Tuple[bool, str]:
        """Attempt to roll doubles to leave jail."""
        if self.state != GameState.JAIL_DECISION:
            return False, "Bukan saatnya mengambil keputusan penjara."

        p = self.current_player
        d1, d2 = self.dice.roll(fixed_values=fixed_values)
        self.has_rolled = True
        self.log(f"{p.name} mencoba melempar dadu di penjara: ({d1}, {d2}) Total = {self.dice.total}.")

        if self.dice.is_double:
            p.in_jail = False
            p.jail_turns = 0
            self.dice.reset_consecutive()
            self.log(f"{p.name} berhasil melempar dadu kembar dan bebas dari penjara!")
            # Move forward by dice total, but NO extra turn
            self.rolled_double = False
            self._move_player(self.dice.total)
            return True, "Berhasil melempar dadu kembar dan bebas!"
        else:
            p.jail_turns += 1
            if p.jail_turns >= 3:
                bail = self.board.jail_bail
                self.log(f"{p.name} telah gagal melempar dadu kembar 3 kali. Wajib membayar jaminan {format_rupiah(bail)}.")
                if p.can_afford(bail):
                    p.deduct_cash(bail)
                    p.in_jail = False
                    p.jail_turns = 0
                    self.log(f"{p.name} membayar jaminan {format_rupiah(bail)} dan dibebaskan.")
                    self.rolled_double = False
                    self._move_player(self.dice.total)
                    return True, "Membayar jaminan setelah 3 kali gagal dan bebas melangkah."
                else:
                    self.debt_amount = bail
                    self.debt_creditor_id = None
                    self.debt_reason = "Wajib bayar jaminan penjara setelah 3 putaran"
                    self.state = GameState.DEBT_RESOLUTION
                    return False, f"Uang kas tidak mencukupi untuk jaminan wajib {format_rupiah(bail)}."
            else:
                self.log(f"{p.name} gagal mendapatkan dadu kembar. Tetap berada di penjara.")
                self.state = GameState.TURN_END
                return True, "Gagal melempar dadu kembar. Tetap di penjara."

    # ---------------------------------------------------------
    # DICE & MOVEMENT
    # ---------------------------------------------------------
    def roll_dice(self, fixed_values: Optional[Tuple[int, int]] = None, defer_movement: bool = False) -> Tuple[bool, str]:
        """Roll two dice and initiate movement or jail penalty."""
        if self.state != GameState.WAITING_FOR_ROLL:
            return False, "Bukan saatnya melempar dadu."

        p = self.current_player
        d1, d2 = self.dice.roll(fixed_values=fixed_values)
        self.has_rolled = True
        is_double = self.dice.is_double
        self.rolled_double = is_double

        self.log(f"{p.name} melempar dadu: [{d1}] [{d2}] (Total: {self.dice.total})" + (" - KEMBAR!" if is_double else ""))

        # Check three consecutive doubles rule
        if self.dice.consecutive_doubles >= 3:
            self.log(f"{p.name} melempar dadu kembar 3 kali berturut-turut! Langsung Masuk Penjara!")
            self._send_to_jail(p)
            return True, "Tiga kali dadu kembar! Masuk penjara."

        if defer_movement:
            old_pos = p.position
            steps = self.dice.total
            target_pos = (old_pos + steps) % 40
            path = [(old_pos + s) % 40 for s in range(1, steps + 1)]
            self.pending_movement = {
                "player_id": p.id,
                "start_pos": old_pos,
                "target_pos": target_pos,
                "steps": steps,
                "path": path,
                "collect_go": True
            }
            self.state = GameState.MOVING
            return True, "Dadu dilempar, pemain melangkah."

        # Execute normal move
        self._move_player(self.dice.total)
        return True, "Berhasil melangkah."

    def complete_deferred_movement(self) -> None:
        """Complete deferred movement when animation finishes or is skipped."""
        if not self.pending_movement:
            return
        steps = self.pending_movement["steps"]
        collect_go = self.pending_movement["collect_go"]
        self.pending_movement = None
        self._move_player(steps, collect_go=collect_go)

    def _move_player(self, steps: int, collect_go: bool = True) -> None:
        """Advance player by number of steps."""
        p = self.current_player
        old_pos = p.position
        new_pos = (old_pos + steps) % 40

        # Check if passed or landed on MULAI
        if collect_go and steps > 0 and (new_pos < old_pos or new_pos == 0):
            p.add_cash(self.board.go_salary)
            self.notify_transaction(p.id, self.board.go_salary, "Gaji Petak MULAI")
            self.log(f"{p.name} melewati/mendarat di MULAI dan menerima gaji {format_rupiah(self.board.go_salary)}.")

        p.position = new_pos
        tile = self.board.get_tile(new_pos)
        self.log(f"{p.name} mendarat di petak {new_pos}: {tile.name}.")
        self.pending_tile_pos = new_pos
        self._resolve_tile(tile)

    def _send_to_jail(self, player: Player) -> None:
        """Directly transport player to jail without Go salary."""
        player.position = 10
        player.in_jail = True
        player.jail_turns = 0
        self.dice.reset_consecutive()
        self.rolled_double = False
        self.state = GameState.TURN_END

    # ---------------------------------------------------------
    # TILE RESOLUTION
    # ---------------------------------------------------------
    def _resolve_tile(self, tile: Tile) -> None:
        """Handle game logic according to the tile landed on."""
        p = self.current_player

        if tile.type == TileType.GO:
            self._conclude_action_or_turn()

        elif tile.type == TileType.FREE_PARKING:
            self.log(f"{p.name} beristirahat di Parkir Gratis.")
            self._conclude_action_or_turn()

        elif tile.type == TileType.JAIL:
            self.log(f"{p.name} hanya berkunjung ke Penjara.")
            self._conclude_action_or_turn()

        elif tile.type == TileType.GO_TO_JAIL:
            self.log(f"{p.name} mendarat di MASUK PENJARA! Segera dikirim ke penjara.")
            self._send_to_jail(p)

        elif tile.type == TileType.TAX:
            tax = tile.tax_amount
            self.log(f"{p.name} terkena kewajiban pajak sebesar {format_rupiah(tax)}.")
            if p.can_afford(tax):
                p.deduct_cash(tax)
                self.notify_transaction(p.id, -tax, f"Bayar {tile.name}")
                self.log(f"{p.name} telah membayar pajak {format_rupiah(tax)} ke kas negara.")
                self._conclude_action_or_turn()
            else:
                self.debt_amount = tax
                self.debt_creditor_id = None
                self.debt_reason = f"Bayar {tile.name}"
                self.state = GameState.DEBT_RESOLUTION

        elif tile.type == TileType.CHANCE:
            card = self.cards.draw_chance()
            self.current_card = card
            self.state = GameState.CARD_RESOLUTION
            self.log(f"{p.name} mengambil kartu Kesempatan: '{card.title}'")

        elif tile.type == TileType.COMMUNITY_CHEST:
            card = self.cards.draw_community_chest()
            self.current_card = card
            self.state = GameState.CARD_RESOLUTION
            self.log(f"{p.name} mengambil kartu Dana Umum: '{card.title}'")

        elif tile.is_ownable:
            if tile.owner_id is None:
                # Unowned -> Player can buy or auction
                self.state = GameState.PROPERTY_DECISION
                self.log(f"{tile.name} belum dimiliki siapa pun. Harga: {format_rupiah(tile.purchase_price)}.")
            elif tile.owner_id == p.id:
                self.log(f"{p.name} mengunjungi properti milik sendiri ({tile.name}).")
                self._conclude_action_or_turn()
            else:
                # Owned by opponent -> Calculate rent
                if tile.is_mortgaged:
                    self.log(f"{tile.name} milik {self.get_player(tile.owner_id).name} sedang digadaikan. Bebas sewa!")
                    self._conclude_action_or_turn()
                else:
                    rent = Economy.calculate_rent(tile, self.board, self.dice.total)
                    owner = self.get_player(tile.owner_id)
                    self.log(f"{p.name} harus membayar sewa {format_rupiah(rent)} kepada {owner.name} di {tile.name}.")
                    if p.can_afford(rent):
                        p.deduct_cash(rent)
                        owner.add_cash(rent)
                        self.notify_transaction(p.id, -rent, f"Sewa {tile.name}")
                        self.notify_transaction(owner.id, rent, f"Sewa {tile.name}")
                        self.log(f"{p.name} berhasil membayar sewa {format_rupiah(rent)} kepada {owner.name}.")
                        self._conclude_action_or_turn()
                    else:
                        self.debt_amount = rent
                        self.debt_creditor_id = owner.id
                        self.debt_reason = f"Sewa {tile.name} kepada {owner.name}"
                        self.state = GameState.DEBT_RESOLUTION

    def _conclude_action_or_turn(self) -> None:
        """Decide whether to grant extra roll (if doubles) or finish action."""
        if self.rolled_double and not self.current_player.in_jail:
            self.state = GameState.WAITING_FOR_ROLL
            self.log(f"{self.current_player.name} mendapat giliran tambahan karena lemparan kembar!")
        else:
            self.state = GameState.TURN_END

    # ---------------------------------------------------------
    # PROPERTY PURCHASE & AUCTION
    # ---------------------------------------------------------
    def buy_current_property(self) -> Tuple[bool, str]:
        """Current player buys the unowned property they landed on."""
        if self.state != GameState.PROPERTY_DECISION:
            return False, "Bukan saatnya mengambil keputusan pembelian properti."

        p = self.current_player
        tile = self.board.get_tile(p.position)

        if not tile or not tile.is_ownable or tile.owner_id is not None:
            return False, "Properti tidak dapat dibeli."

        if not p.can_afford(tile.purchase_price):
            return False, f"Uang kas tidak cukup. Diperlukan {format_rupiah(tile.purchase_price)}."

        p.deduct_cash(tile.purchase_price)
        tile.owner_id = p.id
        p.properties.append(tile.position)
        self.notify_transaction(p.id, -tile.purchase_price, f"Beli {tile.name}")
        self.log(f"{p.name} membeli {tile.name} seharga {format_rupiah(tile.purchase_price)}.")

        self._conclude_action_or_turn()
        return True, "Pembelian properti berhasil."

    def decline_and_auction_property(self) -> Tuple[bool, str]:
        """Current player declines purchase, sending property to public auction."""
        if self.state != GameState.PROPERTY_DECISION:
            return False, "Bukan saatnya mengambil keputusan properti."

        tile = self.board.get_tile(self.current_player.position)
        if not tile or not tile.is_ownable or tile.owner_id is not None:
            return False, "Properti tidak dapat dilelang."

        self.log(f"{self.current_player.name} melepas pembelian {tile.name}. Lelang umum dimulai!")
        eligible_bidders = [p.id for p in self.active_players]
        self.auction = Auction(tile, eligible_bidders)
        self.state = GameState.AUCTION
        return True, "Lelang dimulai."

    def place_auction_bid(self, player_id: int, amount: int) -> Tuple[bool, str]:
        """Place bid in active auction."""
        if self.state != GameState.AUCTION or not self.auction:
            return False, "Tidak ada lelang yang sedang berlangsung."

        player = self.get_player(player_id)
        if not player:
            return False, "Pemain tidak ditemukan."

        success, msg = self.auction.place_bid(player_id, amount, player.cash)
        if success:
            self.log(f"{player.name} menawar {format_rupiah(amount)} untuk {self.auction.tile.name}.")
            self._check_auction_end()
        return success, msg

    def pass_auction_bid(self, player_id: int) -> Tuple[bool, str]:
        """Pass turn in active auction."""
        if self.state != GameState.AUCTION or not self.auction:
            return False, "Tidak ada lelang yang sedang berlangsung."

        player = self.get_player(player_id)
        if not player:
            return False, "Pemain tidak ditemukan."

        success, msg = self.auction.pass_bid(player_id)
        if success:
            self.log(f"{player.name} mundur dari lelang.")
            self._check_auction_end()
        return success, msg

    def _check_auction_end(self) -> None:
        """Handle completion of auction if finished."""
        if not self.auction or not self.auction.is_finished:
            return

        winner_id = self.auction.get_winner()
        tile = self.auction.tile

        if winner_id is not None:
            winner = self.get_player(winner_id)
            winning_bid = self.auction.highest_bid
            winner.deduct_cash(winning_bid)
            tile.owner_id = winner.id
            winner.properties.append(tile.position)
            self.notify_transaction(winner.id, -winning_bid, f"Lelang {tile.name}")
            self.log(f"Lelang selesai! {winner.name} memenangkan {tile.name} seharga {format_rupiah(winning_bid)}.")
        else:
            self.log(f"Lelang selesai tanpa penawar. {tile.name} tetap menjadi milik Bank.")

        self.auction = None
        self._conclude_action_or_turn()

    # ---------------------------------------------------------
    # CARD RESOLUTION
    # ---------------------------------------------------------
    def apply_current_card(self) -> Tuple[bool, str]:
        """Apply the effect of the drawn card."""
        if self.state != GameState.CARD_RESOLUTION or not self.current_card:
            return False, "Tidak ada kartu yang menunggu penyelesaian."

        p = self.current_player
        card = self.current_card
        action = card.action_type
        self.log(f"Menerapkan efek kartu: {card.title}")

        if action == "receive_money":
            p.add_cash(card.amount)
            self.notify_transaction(p.id, card.amount, card.title)
            self.log(f"{p.name} menerima {format_rupiah(card.amount)} dari Bank.")
            self.current_card = None
            self._conclude_action_or_turn()
            return True, "Uang berhasil diterima."

        elif action == "pay_money":
            cost = card.amount
            if p.can_afford(cost):
                p.deduct_cash(cost)
                self.notify_transaction(p.id, -cost, card.title)
                self.log(f"{p.name} membayar {format_rupiah(cost)} ke Bank.")
                self.current_card = None
                self._conclude_action_or_turn()
                return True, "Uang berhasil dibayar."
            else:
                self.debt_amount = cost
                self.debt_creditor_id = None
                self.debt_reason = card.title
                self.current_card = None
                self.state = GameState.DEBT_RESOLUTION
                return False, f"Uang kas tidak cukup membayar {format_rupiah(cost)}."

        elif action == "move_to_tile":
            target = card.target_position
            old_pos = p.position
            self.current_card = None
            # Check pass go
            if card.pass_go_reward and target < old_pos and target != 0:
                p.add_cash(self.board.go_salary)
                self.notify_transaction(p.id, self.board.go_salary, "Gaji Petak MULAI")
                self.log(f"{p.name} melewati MULAI dan menerima {format_rupiah(self.board.go_salary)}.")
            elif target == 0 and card.pass_go_reward:
                p.add_cash(self.board.go_salary)
                self.notify_transaction(p.id, self.board.go_salary, "Gaji Petak MULAI")
                self.log(f"{p.name} sampai di MULAI dan menerima {format_rupiah(self.board.go_salary)}.")

            p.position = target
            tile = self.board.get_tile(target)
            self.log(f"{p.name} berpindah ke petak {target}: {tile.name}.")
            self._resolve_tile(tile)
            return True, f"Berpindah ke {tile.name}."

        elif action == "move_relative":
            steps = card.steps
            self.current_card = None
            new_pos = (p.position + steps) % 40
            p.position = new_pos
            tile = self.board.get_tile(new_pos)
            self.log(f"{p.name} melangkah {steps} petak menuju {tile.name}.")
            self._resolve_tile(tile)
            return True, f"Mundur/maju ke {tile.name}."

        elif action == "go_to_jail":
            self.current_card = None
            self.log(f"{p.name} langsung masuk ke Penjara oleh efek kartu!")
            self._send_to_jail(p)
            return True, "Masuk penjara."

        elif action == "get_out_of_jail_free":
            p.jail_cards.append(card.id)
            self.current_card = None
            self.log(f"{p.name} menyimpan Kartu Bebas Penjara.")
            self._conclude_action_or_turn()
            return True, "Menyimpan kartu bebas penjara."

        elif action == "pay_each_player":
            amount = card.amount
            opponents = [other for other in self.active_players if other.id != p.id]
            total_cost = amount * len(opponents)
            if p.can_afford(total_cost):
                p.deduct_cash(total_cost)
                self.notify_transaction(p.id, -total_cost, card.title)
                for other in opponents:
                    other.add_cash(amount)
                    self.notify_transaction(other.id, amount, card.title)
                self.log(f"{p.name} membayar {format_rupiah(amount)} kepada masing-masing dari {len(opponents)} pemain.")
                self.current_card = None
                self._conclude_action_or_turn()
                return True, "Pembayaran ke semua pemain berhasil."
            else:
                self.debt_amount = total_cost
                self.debt_creditor_id = None  # Bank acts as debt clearing
                self.debt_reason = card.title
                self.current_card = None
                self.state = GameState.DEBT_RESOLUTION
                return False, "Uang kas tidak cukup membayar pemain lain."

        elif action == "receive_from_each_player":
            amount = card.amount
            opponents = [other for other in self.active_players if other.id != p.id]
            total_got = 0
            for other in opponents:
                if other.can_afford(amount):
                    other.deduct_cash(amount)
                    p.add_cash(amount)
                    total_got += amount
                else:
                    # Collect remaining cash
                    avail = other.cash
                    other.cash = 0
                    p.add_cash(avail)
                    total_got += avail
            self.notify_transaction(p.id, total_got, card.title)
            self.log(f"{p.name} menerima {format_rupiah(amount)} dari setiap pemain.")
            self.current_card = None
            self._conclude_action_or_turn()
            return True, "Menerima uang dari pemain lain."

        elif action == "property_repairs":
            per_house = card.per_house
            per_hotel = card.per_hotel
            total_houses = 0
            total_hotels = 0
            for pos in p.properties:
                t = self.board.get_tile(pos)
                if t:
                    total_houses += t.houses
                    total_hotels += t.hotels
            cost = (total_houses * per_house) + (total_hotels * per_hotel)
            self.log(f"Biaya pemeliharaan ({total_houses} rumah, {total_hotels} hotel): {format_rupiah(cost)}.")
            if p.can_afford(cost):
                p.deduct_cash(cost)
                self.notify_transaction(p.id, -cost, card.title)
                self.current_card = None
                self._conclude_action_or_turn()
                return True, "Biaya perbaikan properti dibayar."
            else:
                self.debt_amount = cost
                self.debt_creditor_id = None
                self.debt_reason = card.title
                self.current_card = None
                self.state = GameState.DEBT_RESOLUTION
                return False, f"Uang kas tidak cukup membayar perbaikan {format_rupiah(cost)}."

        self.current_card = None
        self._conclude_action_or_turn()
        return True, "Kartu selesai."

    # ---------------------------------------------------------
    # PROPERTY MANAGEMENT (BUILD, SELL, MORTGAGE, UNMORTGAGE)
    # ---------------------------------------------------------
    def build_house(self, tile_position: int) -> Tuple[bool, str]:
        """Build a house or hotel on a property tile."""
        tile = self.board.get_tile(tile_position)
        if not tile:
            return False, "Petak tidak ditemukan."

        p = self.get_player(tile.owner_id) if tile.owner_id is not None else None
        if not p or p.id != self.current_player.id:
            return False, "Hanya pemilik yang dapat membangun di properti ini."

        can_build, reason = Economy.can_build_on_property(tile, self.board, self.bank, p.cash)
        if not can_build:
            return False, reason

        # Deduct cost
        p.deduct_cash(tile.building_cost)
        self.notify_transaction(p.id, -tile.building_cost, f"Bangun di {tile.name}")

        if tile.houses < 4:
            self.bank.take_houses(1)
            tile.houses += 1
            self.log(f"{p.name} membangun rumah ke-{tile.houses} di {tile.name} ({format_rupiah(tile.building_cost)}).")
            return True, f"Berhasil membangun rumah di {tile.name}."
        else:
            # Upgrade 4 houses to 1 hotel
            self.bank.return_houses(4)
            self.bank.take_hotel()
            tile.houses = 0
            tile.hotels = 1
            self.log(f"{p.name} meningkatkan 4 rumah menjadi sebuah HOTEL di {tile.name} ({format_rupiah(tile.building_cost)})!")
            return True, f"Berhasil membangun hotel di {tile.name}."

    def sell_building(self, tile_position: int) -> Tuple[bool, str]:
        """Sell a house or hotel from a property tile."""
        tile = self.board.get_tile(tile_position)
        if not tile:
            return False, "Petak tidak ditemukan."

        p = self.get_player(tile.owner_id) if tile.owner_id is not None else None
        if not p or p.id != self.current_player.id:
            return False, "Hanya pemilik yang dapat menjual bangunan."

        can_sell, reason = Economy.can_sell_building_on_property(tile, self.board)
        if not can_sell:
            return False, reason

        refund = tile.house_sell_value

        if tile.hotels > 0:
            # Downgrading hotel: if bank has 4 houses, return hotel and take 4 houses
            if self.bank.can_build_house(4):
                self.bank.return_hotel()
                self.bank.take_houses(4)
                tile.hotels = 0
                tile.houses = 4
                p.add_cash(refund)
                self.notify_transaction(p.id, refund, f"Jual Hotel di {tile.name}")
                self.log(f"{p.name} menjual hotel di {tile.name} (kembali menjadi 4 rumah) dan menerima {format_rupiah(refund)}.")
                return True, f"Hotel di {tile.name} dijual menjadi 4 rumah."
            else:
                # If bank does not have 4 houses, sell all buildings on this property completely
                total_refund = refund * 5
                self.bank.return_hotel()
                tile.hotels = 0
                tile.houses = 0
                p.add_cash(total_refund)
                self.notify_transaction(p.id, total_refund, f"Jual Hotel di {tile.name}")
                self.log(f"{p.name} menjual hotel di {tile.name} secara menyeluruh karena stok rumah Bank habis, menerima {format_rupiah(total_refund)}.")
                return True, f"Hotel di {tile.name} dijual tunai."
        else:
            tile.houses -= 1
            self.bank.return_houses(1)
            p.add_cash(refund)
            self.notify_transaction(p.id, refund, f"Jual Rumah di {tile.name}")
            self.log(f"{p.name} menjual 1 rumah di {tile.name} dan menerima {format_rupiah(refund)}.")
            return True, f"1 rumah di {tile.name} berhasil dijual."

    def mortgage_property(self, tile_position: int) -> Tuple[bool, str]:
        """Mortgage an owned property."""
        tile = self.board.get_tile(tile_position)
        if not tile:
            return False, "Petak tidak ditemukan."

        p = self.get_player(tile.owner_id) if tile.owner_id is not None else None
        if not p or p.id != self.current_player.id:
            return False, "Hanya pemilik yang dapat menggadaikan properti."

        can_mortgage, reason = Economy.can_mortgage(tile, self.board)
        if not can_mortgage:
            return False, reason

        tile.is_mortgaged = True
        p.add_cash(tile.mortgage_value)
        self.notify_transaction(p.id, tile.mortgage_value, f"Gadai {tile.name}")
        self.log(f"{p.name} menggadaikan {tile.name} dan menerima uang pinjaman {format_rupiah(tile.mortgage_value)}.")
        return True, f"{tile.name} berhasil digadaikan."

    def unmortgage_property(self, tile_position: int) -> Tuple[bool, str]:
        """Redeem a mortgaged property."""
        tile = self.board.get_tile(tile_position)
        if not tile:
            return False, "Petak tidak ditemukan."

        p = self.get_player(tile.owner_id) if tile.owner_id is not None else None
        if not p or p.id != self.current_player.id:
            return False, "Hanya pemilik yang dapat menebus properti."

        can_unmortgage, reason = Economy.can_unmortgage(tile, p.cash)
        if not can_unmortgage:
            return False, reason

        cost = tile.unmortgage_cost
        p.deduct_cash(cost)
        tile.is_mortgaged = False
        self.notify_transaction(p.id, -cost, f"Tebus {tile.name}")
        self.log(f"{p.name} menebus {tile.name} seharga {format_rupiah(cost)} (pokok + bunga 10%).")
        return True, f"{tile.name} berhasil ditebus."

    # ---------------------------------------------------------
    # TRADING
    # ---------------------------------------------------------
    def execute_trade(self, offer: TradeOffer) -> Tuple[bool, str]:
        """Execute a trade offer between two players."""
        players_map = {p.id: p for p in self.players}
        success, msg = TradeManager.execute_trade(offer, players_map, self.board)
        if success:
            sender = self.get_player(offer.sender_id)
            receiver = self.get_player(offer.receiver_id)
            self.log(f"Transaksi bisnis berhasil disepakati antara {sender.name} dan {receiver.name}!")
        return success, msg

    # ---------------------------------------------------------
    # DEBT RESOLUTION & BANKRUPTCY
    # ---------------------------------------------------------
    def pay_debt(self) -> Tuple[bool, str]:
        """Pay pending debt if player now has sufficient cash."""
        if self.state != GameState.DEBT_RESOLUTION:
            return False, "Tidak ada kewajiban utang yang aktif."

        p = self.current_player
        if not p.can_afford(self.debt_amount):
            return False, f"Uang kas belum mencukupi. Masih kurang {format_rupiah(self.debt_amount - p.cash)}."

        p.deduct_cash(self.debt_amount)
        if self.debt_creditor_id is not None:
            creditor = self.get_player(self.debt_creditor_id)
            if creditor:
                creditor.add_cash(self.debt_amount)
                self.log(f"{p.name} melunasi utang {format_rupiah(self.debt_amount)} kepada {creditor.name}.")
        else:
            self.log(f"{p.name} melunasi kewajiban {format_rupiah(self.debt_amount)} ke Bank.")

        self.debt_amount = 0
        self.debt_creditor_id = None
        self.debt_reason = ""
        self._conclude_action_or_turn()
        return True, "Utang berhasil dilunasi."

    def declare_bankruptcy(self) -> Tuple[bool, str]:
        """Declare bankruptcy and eliminate current player from game."""
        if self.state != GameState.DEBT_RESOLUTION:
            return False, "Hanya dapat menyatakan bangkrut saat dalam penyelesaian utang."

        p = self.current_player
        p.is_bankrupt = True
        self.log(f"BANGKRUT! {p.name} resmi dinyatakan pailit dan tersingkir dari permainan.")

        if self.debt_creditor_id is not None:
            creditor = self.get_player(self.debt_creditor_id)
            if creditor:
                # Transfer remaining cash
                if p.cash > 0:
                    creditor.add_cash(p.cash)
                    p.cash = 0
                # Transfer properties
                for pos in list(p.properties):
                    tile = self.board.get_tile(pos)
                    if tile:
                        tile.owner_id = creditor.id
                        creditor.properties.append(pos)
                p.properties.clear()
                # Transfer get out of jail cards
                creditor.jail_cards.extend(p.jail_cards)
                p.jail_cards.clear()
                self.log(f"Seluruh aset {p.name} diserahkan kepada {creditor.name}.")
        else:
            # Bankrupted to bank: return buildings, clear ownership
            for pos in list(p.properties):
                tile = self.board.get_tile(pos)
                if tile:
                    self.bank.return_houses(tile.houses)
                    self.bank.return_hotel() if tile.hotels > 0 else None
                    tile.reset_ownership()
            p.properties.clear()
            p.cash = 0
            # Return jail cards to decks
            for card_id in p.jail_cards:
                card = self.cards.get_card_by_id(card_id)
                if card:
                    self.cards.return_card(card)
            p.jail_cards.clear()
            self.log(f"Seluruh aset {p.name} dikembalikan ke Bank.")

        self.debt_amount = 0
        self.debt_creditor_id = None
        self.debt_reason = ""

        # Check if winner remains
        remaining = self.active_players
        if len(remaining) <= 1:
            self._declare_winner()
            return True, "Permainan berakhir! Pemenang ditentukan."

        self._advance_turn()
        return True, "Pemain bangkrut dan giliran berganti."

    def _declare_winner(self) -> None:
        """Trigger GAME_OVER and record winning player."""
        remaining = self.active_players
        if remaining:
            self.winner = remaining[0]
            self.log(f"SELAMAT! {self.winner.name} adalah pemenang Nusantara Property Tycoon!")
        else:
            self.winner = None
        self.state = GameState.GAME_OVER

    # ---------------------------------------------------------
    # TURN ADVANCEMENT
    # ---------------------------------------------------------
    def end_turn(self) -> Tuple[bool, str]:
        """Manually end the turn and pass to next player."""
        if self.state != GameState.TURN_END:
            return False, "Belum dapat mengakhiri giliran saat aksi belum selesai."

        self._advance_turn()
        return True, "Giliran berganti."

    def _advance_turn(self) -> None:
        """Internal helper to switch turn to next non-bankrupt player."""
        remaining = self.active_players
        if len(remaining) <= 1:
            self._declare_winner()
            return

        self.dice.reset_consecutive()

        # Find next active player
        num_players = len(self.players)
        for step in range(1, num_players + 1):
            next_idx = (self.current_player_idx + step) % num_players
            if not self.players[next_idx].is_bankrupt:
                self.current_player_idx = next_idx
                break

        self.turn_count += 1
        self.log(f"--- Giliran #{self.turn_count}: {self.current_player.name} ---")
        self._start_turn()

    # ---------------------------------------------------------
    # SERIALIZATION / DESERIALIZATION
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete game state into dictionary."""
        return {
            "version": "1.0.0",
            "game_state": self.state.value,
            "turn_count": self.turn_count,
            "current_player_idx": self.current_player_idx,
            "has_rolled": self.has_rolled,
            "rolled_double": self.rolled_double,
            "pending_tile_pos": self.pending_tile_pos,
            "debt_amount": self.debt_amount,
            "debt_creditor_id": self.debt_creditor_id,
            "debt_reason": self.debt_reason,
            "players": [p.to_dict() for p in self.players],
            "board_tiles": [t.to_state_dict() for t in self.board.tiles],
            "bank_inventory": self.bank.to_dict(),
            "dice": self.dice.to_dict(),
            "cards": self.cards.to_dict(),
            "event_log": list(self.event_log),
            "winner_id": self.winner.id if self.winner else None
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Restore complete game state from dictionary."""
        self.state = GameState(data["game_state"])
        self.turn_count = data.get("turn_count", 1)
        self.current_player_idx = data["current_player_idx"]
        self.has_rolled = data.get("has_rolled", False)
        self.rolled_double = data.get("rolled_double", False)
        self.pending_tile_pos = data.get("pending_tile_pos")
        self.debt_amount = data.get("debt_amount", 0)
        self.debt_creditor_id = data.get("debt_creditor_id")
        self.debt_reason = data.get("debt_reason", "")

        # Restore players
        self.players = [Player.from_dict(pd) for pd in data["players"]]

        # Restore tiles
        tile_map = {td["position"]: td for td in data["board_tiles"]}
        for tile in self.board.tiles:
            if tile.position in tile_map:
                tile.load_state_dict(tile_map[tile.position])

        # Restore bank inventory
        if "bank_inventory" in data:
            self.bank.load_dict(data["bank_inventory"])

        # Restore dice
        if "dice" in data:
            self.dice.load_dict(data["dice"])

        # Restore cards
        if "cards" in data:
            self.cards.load_dict(data["cards"])

        # Restore logs
        self.event_log = data.get("event_log", [])

        # Restore winner
        winner_id = data.get("winner_id")
        self.winner = self.get_player(winner_id) if winner_id is not None else None
