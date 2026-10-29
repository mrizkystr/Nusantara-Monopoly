"""Player model and asset management."""
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any


@dataclass
class Player:
    id: int
    name: str
    color: Tuple[int, int, int]
    cash: int = 15000000
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    jail_cards: List[str] = field(default_factory=list)
    is_bankrupt: bool = False
    consecutive_doubles: int = 0
    token_type: str = "monas"
    properties: List[int] = field(default_factory=list)

    def can_afford(self, amount: int) -> bool:
        """Check if the player has enough cash for an amount."""
        return self.cash >= amount

    def add_cash(self, amount: int) -> None:
        """Add cash to player balance."""
        if amount < 0:
            raise ValueError("Amount cannot be negative in add_cash")
        self.cash += amount

    def deduct_cash(self, amount: int) -> None:
        """Deduct cash from player balance."""
        if amount < 0:
            raise ValueError("Amount cannot be negative in deduct_cash")
        self.cash -= amount

    def get_net_worth(self, board=None) -> int:
        """Calculate total net worth: cash + properties + buildings."""
        total = self.cash
        if board is not None:
            for pos in self.properties:
                tile = board.get_tile(pos)
                if tile:
                    if tile.is_mortgaged:
                        total += tile.mortgage_value
                    else:
                        total += tile.purchase_price
                    # Add building values (50% or 100% of purchase cost; usually building cost itself)
                    if hasattr(tile, "houses") and tile.houses > 0:
                        total += tile.houses * tile.building_cost
                    if hasattr(tile, "hotels") and tile.hotels > 0:
                        total += tile.hotels * tile.building_cost * 5
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Serialize player to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "color": list(self.color),
            "cash": self.cash,
            "position": self.position,
            "in_jail": self.in_jail,
            "jail_turns": self.jail_turns,
            "jail_cards": list(self.jail_cards),
            "is_bankrupt": self.is_bankrupt,
            "consecutive_doubles": self.consecutive_doubles,
            "token_type": self.token_type,
            "properties": list(self.properties)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Deserialize player from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            color=tuple(data["color"]),
            cash=data.get("cash", 15000000),
            position=data.get("position", 0),
            in_jail=data.get("in_jail", False),
            jail_turns=data.get("jail_turns", 0),
            jail_cards=data.get("jail_cards", []),
            is_bankrupt=data.get("is_bankrupt", False),
            consecutive_doubles=data.get("consecutive_doubles", 0),
            token_type=data.get("token_type", "monas"),
            properties=data.get("properties", [])
        )
