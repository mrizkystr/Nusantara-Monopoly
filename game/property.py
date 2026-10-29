"""Tile and Property definitions."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from game.state import TileType, PropertyColorGroup


@dataclass
class Tile:
    id: str
    position: int
    name: str
    type: TileType
    description: str = ""
    color_group: Optional[PropertyColorGroup] = None
    purchase_price: int = 0
    mortgage_value: int = 0
    building_cost: int = 0
    rent_table: List[int] = field(default_factory=list)
    multipliers: List[int] = field(default_factory=list)
    tax_amount: int = 0

    # Runtime state
    owner_id: Optional[int] = None
    is_mortgaged: bool = False
    houses: int = 0
    hotels: int = 0

    @property
    def is_ownable(self) -> bool:
        """Check if this tile can be purchased."""
        return self.type in (TileType.PROPERTY, TileType.TRANSPORT, TileType.UTILITY)

    @property
    def unmortgage_cost(self) -> int:
        """Cost to lift mortgage (principal + 10% interest)."""
        return int(self.mortgage_value * 1.10)

    @property
    def house_sell_value(self) -> int:
        """Value gained from selling one house (50% of cost)."""
        return self.building_cost // 2

    @property
    def total_buildings(self) -> int:
        """Total building level: 0-4 for houses, 5 for hotel."""
        if self.hotels > 0:
            return 5
        return self.houses

    def reset_ownership(self) -> None:
        """Reset tile ownership and developments back to bank."""
        self.owner_id = None
        self.is_mortgaged = False
        self.houses = 0
        self.hotels = 0

    def to_state_dict(self) -> Dict[str, Any]:
        """Serialize runtime state for save files."""
        return {
            "position": self.position,
            "owner_id": self.owner_id,
            "is_mortgaged": self.is_mortgaged,
            "houses": self.houses,
            "hotels": self.hotels
        }

    def load_state_dict(self, data: Dict[str, Any]) -> None:
        """Load runtime state from dictionary."""
        self.owner_id = data.get("owner_id")
        self.is_mortgaged = data.get("is_mortgaged", False)
        self.houses = data.get("houses", 0)
        self.hotels = data.get("hotels", 0)
