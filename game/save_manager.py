"""Save and load game state with atomic file operations and validation."""
import json
import os
import tempfile
from typing import Dict, Any, Optional, List


class SaveManager:
    DEFAULT_SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saves")
    DEFAULT_SAVE_FILE = "autosave.json"

    @classmethod
    def get_save_path(cls, filename: str = DEFAULT_SAVE_FILE) -> str:
        if not os.path.isabs(filename):
            return os.path.join(cls.DEFAULT_SAVE_DIR, filename)
        return filename

    @classmethod
    def has_save_file(cls, filename: str = DEFAULT_SAVE_FILE) -> bool:
        """Check if a save file exists."""
        path = cls.get_save_path(filename)
        return os.path.exists(path) and os.path.isfile(path)

    @classmethod
    def save_game(cls, game_state_dict: Dict[str, Any], filename: str = DEFAULT_SAVE_FILE) -> tuple[bool, str]:
        """Atomically save game state to JSON file."""
        target_path = cls.get_save_path(filename)
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)

        try:
            # Write to a temporary file in the same directory first
            with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tf:
                temp_name = tf.name
                json.dump(game_state_dict, tf, indent=2, ensure_ascii=False)
                tf.flush()
                os.fsync(tf.fileno())

            # Atomic replace
            os.replace(temp_name, target_path)
            return True, f"Permainan berhasil disimpan ke {os.path.basename(target_path)}."
        except Exception as e:
            if 'temp_name' in locals() and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except OSError:
                    pass
            return False, f"Gagal menyimpan permainan: {str(e)}"

    @classmethod
    def load_game(cls, filename: str = DEFAULT_SAVE_FILE) -> tuple[Optional[Dict[str, Any]], str]:
        """Load and validate game state from JSON file."""
        target_path = cls.get_save_path(filename)
        if not os.path.exists(target_path):
            return None, "File penyimpanan tidak ditemukan."

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate basic structure
            required_keys = ["version", "game_state", "players", "board_tiles", "current_player_idx"]
            for key in required_keys:
                if key not in data:
                    return None, f"File penyimpanan korup: kunci '{key}' tidak ditemukan."

            return data, "Permainan berhasil dimuat."
        except Exception as e:
            return None, f"Gagal memuat file penyimpanan: {str(e)}"

    @classmethod
    def list_save_files(cls) -> List[str]:
        """List all valid save files in the saves directory."""
        if not os.path.exists(cls.DEFAULT_SAVE_DIR):
            return []
        files = []
        for f in os.listdir(cls.DEFAULT_SAVE_DIR):
            if f.endswith(".json"):
                files.append(f)
        return sorted(files)
