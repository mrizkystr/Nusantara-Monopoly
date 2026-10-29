"""Board representation and validation."""
import json
import os
from typing import List, Dict, Optional
from game.property import Tile
from game.state import TileType, PropertyColorGroup


class Board:
    def __init__(self, config_path: Optional[str] = None):
        self.tiles: List[Tile] = []
        self._tile_by_id: Dict[str, Tile] = {}
        self._group_tiles: Dict[PropertyColorGroup, List[Tile]] = {
            group: [] for group in PropertyColorGroup
        }
        self.go_salary: int = 2000000
        self.jail_bail: int = 500000

        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "board.json")
        self.load_from_json(config_path)

    def load_from_json(self, file_path: str) -> None:
        """Load board tiles from JSON file and validate configuration."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.go_salary = data.get("go_salary", 2000000)
        self.jail_bail = data.get("jail_bail", 500000)
        raw_tiles = data.get("tiles", [])

        self.tiles = []
        self._tile_by_id = {}
        self._group_tiles = {group: [] for group in PropertyColorGroup}

        for raw in raw_tiles:
            tile_type = TileType(raw["type"])
            color_group = None
            if "color_group" in raw and raw["color_group"]:
                color_group = PropertyColorGroup(raw["color_group"])

            tile = Tile(
                id=raw["id"],
                position=raw["position"],
                name=raw["name"],
                type=tile_type,
                description=raw.get("description", ""),
                color_group=color_group,
                purchase_price=raw.get("purchase_price", 0),
                mortgage_value=raw.get("mortgage_value", 0),
                building_cost=raw.get("building_cost", 0),
                rent_table=raw.get("rent_table", []),
                multipliers=raw.get("multipliers", []),
                tax_amount=raw.get("tax_amount", 0)
            )

            self.tiles.append(tile)
            self._tile_by_id[tile.id] = tile
            if color_group:
                self._group_tiles[color_group].append(tile)

        self.validate()

    def validate(self) -> None:
        """Validate the board configuration."""
        if len(self.tiles) != 40:
            raise ValueError(f"Board must have exactly 40 tiles, found {len(self.tiles)}")

        positions = set()
        ids = set()

        for idx, tile in enumerate(self.tiles):
            if tile.position != idx:
                raise ValueError(f"Tile at index {idx} has mismatched position {tile.position}")
            if tile.position in positions:
                raise ValueError(f"Duplicate tile position: {tile.position}")
            if tile.id in ids:
                raise ValueError(f"Duplicate tile id: {tile.id}")
            positions.add(tile.position)
            ids.add(tile.id)

            if tile.type == TileType.PROPERTY:
                if not tile.color_group:
                    raise ValueError(f"Property tile {tile.name} must have a color group")
                if tile.purchase_price <= 0:
                    raise ValueError(f"Property tile {tile.name} must have a positive purchase price")
                if len(tile.rent_table) != 7:
                    raise ValueError(f"Property tile {tile.name} rent table must contain exactly 7 values")

            elif tile.type == TileType.TRANSPORT:
                if tile.purchase_price <= 0 or len(tile.rent_table) != 4:
                    raise ValueError(f"Transport tile {tile.name} must have valid price and 4 rent tiers")

            elif tile.type == TileType.UTILITY:
                if tile.purchase_price <= 0 or len(tile.multipliers) != 2:
                    raise ValueError(f"Utility tile {tile.name} must have valid price and 2 multipliers")

            elif tile.type == TileType.TAX:
                if tile.tax_amount <= 0:
                    raise ValueError(f"Tax tile {tile.name} must have a positive tax amount")

    def get_tile(self, position: int) -> Optional[Tile]:
        """Get tile by board position (0-39)."""
        if 0 <= position < len(self.tiles):
            return self.tiles[position]
        return None

    def get_tile_by_id(self, tile_id: str) -> Optional[Tile]:
        """Get tile by string identifier."""
        return self._tile_by_id.get(tile_id)

    def get_group_tiles(self, color_group: PropertyColorGroup) -> List[Tile]:
        """Get all tiles belonging to a specific color group."""
        return self._group_tiles.get(color_group, [])

    def is_monopoly(self, player_id: int, color_group: PropertyColorGroup) -> bool:
        """Check if a player owns all properties in a color group."""
        group_tiles = self.get_group_tiles(color_group)
        if not group_tiles:
            return False
        return all(t.owner_id == player_id for t in group_tiles)

    def has_mortgaged_in_group(self, color_group: PropertyColorGroup) -> bool:
        """Check if any property in this group is mortgaged."""
        return any(t.is_mortgaged for t in self.get_group_tiles(color_group))

    def get_player_properties(self, player_id: int) -> List[Tile]:
        """Return all properties currently owned by player_id."""
        return [t for t in self.tiles if t.owner_id == player_id]

    def count_transports_owned(self, player_id: int) -> int:
        """Count transport stations owned by a player."""
        return sum(1 for t in self.tiles if t.type == TileType.TRANSPORT and t.owner_id == player_id)

    def count_utilities_owned(self, player_id: int) -> int:
        """Count utility properties owned by a player."""
        return sum(1 for t in self.tiles if t.type == TileType.UTILITY and t.owner_id == player_id)
