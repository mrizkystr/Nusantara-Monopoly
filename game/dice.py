"""Dice system with doubles tracking and injectable RNG."""
import random
from typing import Tuple, Optional


class Dice:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng if rng is not None else random.Random()
        self.dice1: int = 1
        self.dice2: int = 1
        self.consecutive_doubles: int = 0

    @property
    def total(self) -> int:
        """Sum of both dice."""
        return self.dice1 + self.dice2

    @property
    def is_double(self) -> bool:
        """Check if both dice show the same value."""
        return self.dice1 == self.dice2

    def roll(self, fixed_values: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
        """
        Roll the two dice.
        Allows specifying fixed_values for deterministic unit tests.
        """
        if fixed_values is not None:
            self.dice1, self.dice2 = fixed_values
        else:
            self.dice1 = self.rng.randint(1, 6)
            self.dice2 = self.rng.randint(1, 6)

        if self.is_double:
            self.consecutive_doubles += 1
        else:
            self.consecutive_doubles = 0

        return self.dice1, self.dice2

    def reset_consecutive(self) -> None:
        """Reset consecutive doubles counter."""
        self.consecutive_doubles = 0

    def to_dict(self) -> dict:
        """Serialize dice state."""
        return {
            "dice1": self.dice1,
            "dice2": self.dice2,
            "consecutive_doubles": self.consecutive_doubles
        }

    def load_dict(self, data: dict) -> None:
        """Load dice state."""
        self.dice1 = data.get("dice1", 1)
        self.dice2 = data.get("dice2", 1)
        self.consecutive_doubles = data.get("consecutive_doubles", 0)
