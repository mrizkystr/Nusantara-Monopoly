"""Game settings management and persistence."""
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Settings:
    fullscreen: bool = False
    master_volume: float = 0.8
    music_volume: float = 0.5
    sfx_volume: float = 0.8
    muted: bool = False
    animation_speed: str = "Normal"  # "Normal", "Fast", "Instant"
    skip_movement: bool = False
    confirm_dialogs: bool = True

    @property
    def is_fullscreen(self) -> bool:
        return self.fullscreen

    @property
    def is_muted(self) -> bool:
        return self.muted

    @classmethod
    def get_path(cls) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "settings.json")

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from JSON, returning defaults if missing or corrupted."""
        path = cls.get_path()
        if not os.path.exists(path):
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(
                fullscreen=bool(data.get("fullscreen", False)),
                master_volume=max(0.0, min(1.0, float(data.get("master_volume", 0.8)))),
                music_volume=max(0.0, min(1.0, float(data.get("music_volume", 0.5)))),
                sfx_volume=max(0.0, min(1.0, float(data.get("sfx_volume", 0.8)))),
                muted=bool(data.get("muted", False)),
                animation_speed=data.get("animation_speed", "Normal"),
                skip_movement=bool(data.get("skip_movement", False)),
                confirm_dialogs=bool(data.get("confirm_dialogs", True))
            )
        except Exception:
            return cls()

    def save(self) -> None:
        """Persist settings to JSON file."""
        path = self.get_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception:
            pass

    def apply_to_audio(self, audio_manager) -> None:
        """Sync volume and mute status with the audio manager."""
        if audio_manager:
            audio_manager.set_master_volume(self.master_volume)
            audio_manager.set_music_volume(self.music_volume)
            audio_manager.set_sfx_volume(self.sfx_volume)
            audio_manager.set_mute(self.muted)
