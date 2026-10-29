"""Cards management, deck shuffling, and card models."""
import json
import os
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Card:
    id: str
    deck: str
    title: str
    description: str
    action_type: str
    amount: int = 0
    target_position: int = 0
    pass_go_reward: bool = True
    steps: int = 0
    per_house: int = 0
    per_hotel: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Card":
        return cls(
            id=data["id"],
            deck=data["deck"],
            title=data["title"],
            description=data["description"],
            action_type=data["action_type"],
            amount=data.get("amount", 0),
            target_position=data.get("target_position", 0),
            pass_go_reward=data.get("pass_go_reward", True),
            steps=data.get("steps", 0),
            per_house=data.get("per_house", 0),
            per_hotel=data.get("per_hotel", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "deck": self.deck,
            "title": self.title,
            "description": self.description,
            "action_type": self.action_type,
            "amount": self.amount,
            "target_position": self.target_position,
            "pass_go_reward": self.pass_go_reward,
            "steps": self.steps,
            "per_house": self.per_house,
            "per_hotel": self.per_hotel
        }


class CardDeck:
    """Represents a single deck (Chance or Community Chest)."""

    def __init__(self, name: str, cards: List[Card], rng: Optional[random.Random] = None):
        self.name = name
        self.all_cards = {c.id: c for c in cards}
        self.rng = rng if rng is not None else random.Random()
        self.draw_pile: List[str] = [c.id for c in cards]
        self.discard_pile: List[str] = []
        self.held_cards: set[str] = set()  # Cards held by players (like get out of jail free)
        self.shuffle()

    def shuffle(self) -> None:
        """Shuffle the current draw pile."""
        self.rng.shuffle(self.draw_pile)

    def draw(self) -> Card:
        """Draw the top card. If empty, reshuffle discard pile."""
        if not self.draw_pile:
            if not self.discard_pile:
                raise RuntimeError(f"Deck {self.name} is completely empty!")
            self.draw_pile = list(self.discard_pile)
            self.discard_pile.clear()
            self.shuffle()

        card_id = self.draw_pile.pop(0)
        card = self.all_cards[card_id]

        if card.action_type == "get_out_of_jail_free":
            self.held_cards.add(card_id)
        else:
            self.discard_pile.append(card_id)

        return card

    def return_held_card(self, card_id: str) -> None:
        """Return a held card (e.g. Get Out of Jail Free) to discard pile."""
        if card_id in self.held_cards:
            self.held_cards.remove(card_id)
            self.discard_pile.append(card_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize deck state."""
        return {
            "name": self.name,
            "draw_pile": list(self.draw_pile),
            "discard_pile": list(self.discard_pile),
            "held_cards": list(self.held_cards)
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Load deck state."""
        self.draw_pile = data.get("draw_pile", [])
        self.discard_pile = data.get("discard_pile", [])
        self.held_cards = set(data.get("held_cards", []))


class CardManager:
    """Manages both Chance and Community Chest decks."""

    def __init__(self, config_path: Optional[str] = None, rng: Optional[random.Random] = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cards.json")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chance_cards = [Card.from_dict(c) for c in data.get("chance", [])]
        cc_cards = [Card.from_dict(c) for c in data.get("community_chest", [])]

        self.chance_deck = CardDeck("chance", chance_cards, rng=rng)
        self.community_chest_deck = CardDeck("community_chest", cc_cards, rng=rng)

    def draw_chance(self) -> Card:
        """Draw a card from Chance deck."""
        return self.chance_deck.draw()

    def draw_community_chest(self) -> Card:
        """Draw a card from Community Chest deck."""
        return self.community_chest_deck.draw()

    def return_card(self, card: Card) -> None:
        """Return a special card to its deck."""
        if card.deck == "chance":
            self.chance_deck.return_held_card(card.id)
        elif card.deck == "community_chest":
            self.community_chest_deck.return_held_card(card.id)

    def get_card_by_id(self, card_id: str) -> Optional[Card]:
        """Lookup card by ID from either deck."""
        if card_id in self.chance_deck.all_cards:
            return self.chance_deck.all_cards[card_id]
        if card_id in self.community_chest_deck.all_cards:
            return self.community_chest_deck.all_cards[card_id]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize both decks."""
        return {
            "chance": self.chance_deck.to_dict(),
            "community_chest": self.community_chest_deck.to_dict()
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Load states of both decks."""
        if "chance" in data:
            self.chance_deck.load_dict(data["chance"])
        if "community_chest" in data:
            self.community_chest_deck.load_dict(data["community_chest"])
