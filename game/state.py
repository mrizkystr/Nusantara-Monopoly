"""Game state definitions and enumerations."""
from enum import Enum


class GameState(Enum):
    MAIN_MENU = "MAIN_MENU"
    PLAYER_SETUP = "PLAYER_SETUP"
    TURN_START = "TURN_START"
    WAITING_FOR_ROLL = "WAITING_FOR_ROLL"
    MOVING = "MOVING"
    RESOLVING_TILE = "RESOLVING_TILE"
    PROPERTY_DECISION = "PROPERTY_DECISION"
    AUCTION = "AUCTION"
    CARD_RESOLUTION = "CARD_RESOLUTION"
    DEBT_RESOLUTION = "DEBT_RESOLUTION"
    PROPERTY_MANAGEMENT = "PROPERTY_MANAGEMENT"
    TRADE_NEGOTIATION = "TRADE_NEGOTIATION"
    JAIL_DECISION = "JAIL_DECISION"
    TURN_END = "TURN_END"
    GAME_OVER = "GAME_OVER"


class TileType(Enum):
    GO = "go"
    PROPERTY = "property"
    COMMUNITY_CHEST = "community_chest"
    CHANCE = "chance"
    TAX = "tax"
    TRANSPORT = "transport"
    JAIL = "jail"
    UTILITY = "utility"
    FREE_PARKING = "free_parking"
    GO_TO_JAIL = "go_to_jail"


class PropertyColorGroup(Enum):
    BROWN = "brown"
    LIGHT_BLUE = "light_blue"
    PINK = "pink"
    ORANGE = "orange"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    DARK_BLUE = "dark_blue"
