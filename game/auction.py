"""Auction system with turn-based bidding and pass mechanics."""
from typing import List, Optional, Tuple, Dict, Any
from game.property import Tile


class Auction:
    def __init__(self, tile: Tile, eligible_player_ids: List[int], starting_bid: int = 0, min_increment: int = 100000):
        self.tile = tile
        self.active_bidders: List[int] = list(eligible_player_ids)
        self.current_bidder_idx: int = 0
        self.highest_bid: int = starting_bid
        self.highest_bidder_id: Optional[int] = None
        self.min_increment: int = min_increment
        self.is_completed: bool = False

    def get_current_bidder_id(self) -> Optional[int]:
        """Get the ID of the player whose turn it is to bid or pass."""
        if self.is_finished:
            return None
        if not self.active_bidders:
            return None
        return self.active_bidders[self.current_bidder_idx]

    @property
    def is_finished(self) -> bool:
        """Check if auction has concluded."""
        if self.is_completed:
            return True
        # If no active bidders left
        if len(self.active_bidders) == 0:
            return True
        # If only 1 bidder left and there has been at least one valid bid
        if len(self.active_bidders) == 1 and self.highest_bidder_id is not None:
            return True
        return False

    @property
    def minimum_next_bid(self) -> int:
        """Minimum valid bid amount for the current turn."""
        if self.highest_bid == 0:
            return self.min_increment
        return self.highest_bid + self.min_increment

    def place_bid(self, player_id: int, amount: int, player_cash: int) -> Tuple[bool, str]:
        """Place a bid for the current player."""
        if self.is_finished:
            return False, "Lelang telah selesai."

        current_id = self.get_current_bidder_id()
        if current_id != player_id:
            return False, "Bukan giliran Anda untuk menawar."

        if amount < self.minimum_next_bid:
            return False, f"Tawaran minimal adalah Rp{self.minimum_next_bid:,}."

        if amount > player_cash:
            return False, "Uang kas Anda tidak mencukupi untuk tawaran ini."

        self.highest_bid = amount
        self.highest_bidder_id = player_id

        # Advance turn to next bidder
        if len(self.active_bidders) > 1:
            self.current_bidder_idx = (self.current_bidder_idx + 1) % len(self.active_bidders)

        self._check_completion()
        return True, "Tawaran berhasil diajukan."

    def pass_bid(self, player_id: int) -> Tuple[bool, str]:
        """Current player passes and exits this auction permanently."""
        if self.is_finished:
            return False, "Lelang telah selesai."

        current_id = self.get_current_bidder_id()
        if current_id != player_id:
            return False, "Bukan giliran Anda."

        # Remove player from active bidders
        self.active_bidders.remove(player_id)

        # Adjust index
        if self.active_bidders:
            self.current_bidder_idx = self.current_bidder_idx % len(self.active_bidders)

        self._check_completion()
        return True, "Anda telah keluar dari lelang."

    def _check_completion(self) -> None:
        """Check if conditions for concluding auction are satisfied."""
        if len(self.active_bidders) == 0:
            self.is_completed = True
        elif len(self.active_bidders) == 1 and self.highest_bidder_id is not None:
            self.is_completed = True

    def get_winner(self) -> Optional[int]:
        """Return the winner player_id if any."""
        if self.is_finished and self.highest_bidder_id is not None:
            return self.highest_bidder_id
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize auction state."""
        return {
            "tile_position": self.tile.position,
            "active_bidders": list(self.active_bidders),
            "current_bidder_idx": self.current_bidder_idx,
            "highest_bid": self.highest_bid,
            "highest_bidder_id": self.highest_bidder_id,
            "min_increment": self.min_increment,
            "is_completed": self.is_completed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], tile: Tile) -> "Auction":
        """Deserialize auction state."""
        auction = cls(
            tile=tile,
            eligible_player_ids=data.get("active_bidders", []),
            starting_bid=data.get("highest_bid", 0),
            min_increment=data.get("min_increment", 100000)
        )
        auction.current_bidder_idx = data.get("current_bidder_idx", 0)
        auction.highest_bidder_id = data.get("highest_bidder_id")
        auction.is_completed = data.get("is_completed", False)
        return auction
