"""Economy, rent calculations, building inventory, and currency formatting."""
from typing import Dict, Any, Optional
from game.property import Tile
from game.state import TileType, PropertyColorGroup
from game.board import Board


def format_rupiah(amount: int) -> str:
    """Format an integer amount into standard Indonesian Rupiah notation (e.g. Rp15.000.000)."""
    sign = "-" if amount < 0 else ""
    abs_amt = abs(amount)
    formatted = f"{abs_amt:,}".replace(",", ".")
    return f"{sign}Rp{formatted}"


class BankInventory:
    """Manages the finite bank supply of houses and hotels."""
    TOTAL_HOUSES = 32
    TOTAL_HOTELS = 12

    def __init__(self, houses: int = TOTAL_HOUSES, hotels: int = TOTAL_HOTELS):
        self.houses: int = houses
        self.hotels: int = hotels

    def can_build_house(self, count: int = 1) -> bool:
        """Check if bank has enough houses available."""
        return self.houses >= count

    def can_build_hotel(self, count: int = 1) -> bool:
        """Check if bank has enough hotels available."""
        return self.hotels >= count

    def take_houses(self, count: int = 1) -> None:
        """Deduct houses from bank inventory."""
        if not self.can_build_house(count):
            raise ValueError("Bank has insufficient houses")
        self.houses -= count

    def return_houses(self, count: int = 1) -> None:
        """Return houses back to bank inventory."""
        self.houses = min(self.TOTAL_HOUSES, self.houses + count)

    def take_hotel(self) -> None:
        """Deduct one hotel from bank inventory."""
        if not self.can_build_hotel(1):
            raise ValueError("Bank has insufficient hotels")
        self.hotels -= 1

    def return_hotel(self) -> None:
        """Return one hotel back to bank inventory."""
        self.hotels = min(self.TOTAL_HOTELS, self.hotels + 1)

    def to_dict(self) -> Dict[str, int]:
        """Serialize bank inventory."""
        return {
            "houses": self.houses,
            "hotels": self.hotels
        }

    def load_dict(self, data: Dict[str, int]) -> None:
        """Load bank inventory."""
        self.houses = data.get("houses", self.TOTAL_HOUSES)
        self.hotels = data.get("hotels", self.TOTAL_HOTELS)


class Economy:
    """Calculates rent and enforces construction / mortgage rules."""

    @staticmethod
    def calculate_rent(tile: Tile, board: Board, dice_roll: int) -> int:
        """Calculate rent due when landing on a tile."""
        if not tile.is_ownable or tile.owner_id is None or tile.is_mortgaged:
            return 0

        if tile.type == TileType.PROPERTY:
            if tile.hotels > 0:
                # 1 hotel is at index 6
                return tile.rent_table[6]
            elif tile.houses > 0:
                # 1 house -> index 2, 2 houses -> index 3, etc.
                return tile.rent_table[tile.houses + 1]
            else:
                # No buildings: check if player has monopoly on this group
                if tile.color_group and board.is_monopoly(tile.owner_id, tile.color_group):
                    return tile.rent_table[1]  # Monopolized base rent (2x base)
                return tile.rent_table[0]  # Standard base rent

        elif tile.type == TileType.TRANSPORT:
            count = board.count_transports_owned(tile.owner_id)
            if 1 <= count <= 4:
                return tile.rent_table[count - 1]
            return 0

        elif tile.type == TileType.UTILITY:
            count = board.count_utilities_owned(tile.owner_id)
            if count == 1:
                return tile.multipliers[0] * dice_roll
            elif count >= 2:
                return tile.multipliers[1] * dice_roll
            return 0

        return 0

    @staticmethod
    def can_build_on_property(tile: Tile, board: Board, bank: BankInventory, player_cash: int) -> tuple[bool, str]:
        """Validate if a house or hotel can be built on this property."""
        if tile.type != TileType.PROPERTY:
            return False, "Hanya petak properti kota yang dapat dibangun."

        if tile.owner_id is None:
            return False, "Properti belum dimiliki."

        if not tile.color_group:
            return False, "Properti tidak memiliki kelompok warna."

        if not board.is_monopoly(tile.owner_id, tile.color_group):
            return False, "Anda harus memiliki seluruh kota dalam kelompok warna ini."

        if board.has_mortgaged_in_group(tile.color_group):
            return False, "Tidak dapat membangun jika ada properti yang digadaikan dalam kelompok ini."

        if player_cash < tile.building_cost:
            return False, f"Uang tidak cukup. Biaya pembangunan adalah {format_rupiah(tile.building_cost)}."

        # Check max development (1 hotel)
        if tile.hotels >= 1:
            return False, "Properti sudah memiliki sebuah hotel (pembangunan maksimal)."

        # Check even building rule across group
        group_tiles = board.get_group_tiles(tile.color_group)
        current_level = tile.total_buildings

        for other in group_tiles:
            if other.total_buildings < current_level:
                return False, f"Pembangunan harus merata. Bangun di {other.name} terlebih dahulu."

        if current_level < 4:
            # Building a house
            if not bank.can_build_house(1):
                return False, "Stok rumah di Bank sedang habis."
            return True, "Dapat membangun rumah."
        else:
            # Building a hotel
            if not bank.can_build_hotel(1):
                return False, "Stok hotel di Bank sedang habis."
            return True, "Dapat membangun hotel."

    @staticmethod
    def can_sell_building_on_property(tile: Tile, board: Board) -> tuple[bool, str]:
        """Validate if a house or hotel can be sold from this property."""
        if tile.type != TileType.PROPERTY:
            return False, "Bukan petak properti."

        if tile.total_buildings <= 0:
            return False, "Tidak ada bangunan di properti ini untuk dijual."

        # Enforce even selling rule
        group_tiles = board.get_group_tiles(tile.color_group)
        current_level = tile.total_buildings

        for other in group_tiles:
            if other.total_buildings > current_level:
                return False, f"Penjualan harus merata. Jual bangunan di {other.name} terlebih dahulu."

        return True, "Dapat menjual bangunan."

    @staticmethod
    def can_mortgage(tile: Tile, board: Board) -> tuple[bool, str]:
        """Validate if a property can be mortgaged."""
        if not tile.is_ownable:
            return False, "Petak ini tidak dapat digadaikan."

        if tile.is_mortgaged:
            return False, "Properti ini sudah dalam status tergadai."

        if tile.type == TileType.PROPERTY and tile.color_group:
            # Check if any property in the group has buildings
            group_tiles = board.get_group_tiles(tile.color_group)
            if any(t.total_buildings > 0 for t in group_tiles):
                return False, "Harus menjual seluruh rumah/hotel di kelompok warna ini sebelum menggadaikan."

        return True, "Dapat digadaikan."

    @staticmethod
    def can_unmortgage(tile: Tile, player_cash: int) -> tuple[bool, str]:
        """Validate if a mortgaged property can be redeemed."""
        if not tile.is_mortgaged:
            return False, "Properti tidak sedang digadaikan."

        cost = tile.unmortgage_cost
        if player_cash < cost:
            return False, f"Uang tidak cukup untuk menebus. Dibutuhkan {format_rupiah(cost)}."

        return True, "Dapat ditebus."
