"""Player-to-player property trading system."""
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
from game.board import Board
from game.player import Player
from game.property import Tile


@dataclass
class TradeOffer:
    sender_id: int
    receiver_id: int
    offered_cash: int = 0
    requested_cash: int = 0
    offered_properties: List[int] = field(default_factory=list)
    requested_properties: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "offered_cash": self.offered_cash,
            "requested_cash": self.requested_cash,
            "offered_properties": list(self.offered_properties),
            "requested_properties": list(self.requested_properties)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeOffer":
        return cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            offered_cash=data.get("offered_cash", 0),
            requested_cash=data.get("requested_cash", 0),
            offered_properties=data.get("offered_properties", []),
            requested_properties=data.get("requested_properties", [])
        )


class TradeManager:
    @staticmethod
    def validate_trade(
        offer: TradeOffer,
        players: Dict[int, Player],
        board: Board
    ) -> Tuple[bool, str]:
        """Validate if a trade offer is legal and feasible."""
        sender = players.get(offer.sender_id)
        receiver = players.get(offer.receiver_id)

        if not sender or not receiver:
            return False, "Pemain tidak ditemukan."

        if sender.is_bankrupt or receiver.is_bankrupt:
            return False, "Pemain yang bangkrut tidak dapat berdagang."

        if offer.sender_id == offer.receiver_id:
            return False, "Tidak dapat berdagang dengan diri sendiri."

        if offer.offered_cash < 0 or offer.requested_cash < 0:
            return False, "Jumlah uang tidak boleh bernilai negatif."

        if not sender.can_afford(offer.offered_cash):
            return False, f"{sender.name} tidak memiliki cukup uang untuk tawaran ini."

        if not receiver.can_afford(offer.requested_cash):
            return False, f"{receiver.name} tidak memiliki cukup uang untuk permintaan ini."

        # At least one asset or cash must be exchanged
        has_offered = offer.offered_cash > 0 or len(offer.offered_properties) > 0
        has_requested = offer.requested_cash > 0 or len(offer.requested_properties) > 0
        if not (has_offered and has_requested):
            return False, "Pertukaran harus saling menguntungkan (ada aset/uang yang ditukar)."

        # Validate offered properties
        for pos in offer.offered_properties:
            tile = board.get_tile(pos)
            if not tile or tile.owner_id != sender.id:
                return False, f"{sender.name} tidak memiliki properti pada petak {pos}."
            # Check for buildings in the color group
            if tile.color_group:
                group_tiles = board.get_group_tiles(tile.color_group)
                if any(t.total_buildings > 0 for t in group_tiles):
                    return False, f"Properti {tile.name} masih memiliki bangunan dalam kelompok warnanya. Jual bangunan terlebih dahulu."

        # Validate requested properties
        for pos in offer.requested_properties:
            tile = board.get_tile(pos)
            if not tile or tile.owner_id != receiver.id:
                return False, f"{receiver.name} tidak memiliki properti pada petak {pos}."
            if tile.color_group:
                group_tiles = board.get_group_tiles(tile.color_group)
                if any(t.total_buildings > 0 for t in group_tiles):
                    return False, f"Properti {tile.name} masih memiliki bangunan dalam kelompok warnanya. Jual bangunan terlebih dahulu."

        return True, "Tawaran perdagangan valid."

    @staticmethod
    def execute_trade(
        offer: TradeOffer,
        players: Dict[int, Player],
        board: Board
    ) -> Tuple[bool, str]:
        """Execute the trade atomically."""
        valid, msg = TradeManager.validate_trade(offer, players, board)
        if not valid:
            return False, msg

        sender = players[offer.sender_id]
        receiver = players[offer.receiver_id]

        # Transfer cash
        if offer.offered_cash > 0:
            sender.deduct_cash(offer.offered_cash)
            receiver.add_cash(offer.offered_cash)

        if offer.requested_cash > 0:
            receiver.deduct_cash(offer.requested_cash)
            sender.add_cash(offer.requested_cash)

        # Transfer sender's offered properties to receiver
        for pos in offer.offered_properties:
            tile = board.get_tile(pos)
            if tile:
                tile.owner_id = receiver.id
                if pos in sender.properties:
                    sender.properties.remove(pos)
                if pos not in receiver.properties:
                    receiver.properties.append(pos)

        # Transfer receiver's requested properties to sender
        for pos in offer.requested_properties:
            tile = board.get_tile(pos)
            if tile:
                tile.owner_id = sender.id
                if pos in receiver.properties:
                    receiver.properties.remove(pos)
                if pos not in sender.properties:
                    sender.properties.append(pos)

        return True, "Perdagangan berhasil diselesaikan!"
