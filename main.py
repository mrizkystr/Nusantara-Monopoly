"""Main entry point for Nusantara Property Tycoon."""
import os
import sys
from typing import Optional
import pygame
from game.engine import GameEngine
from game.settings import Settings
from game.save_manager import SaveManager
from ui.audio import AudioManager
from ui.input_handler import InputHandler
from ui.screens import MainMenuScreen, SetupScreen, RulesScreen, SettingsScreen, GamePlayScreen


class NusantaraGameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.settings = Settings.load()
        self.initial_width = 1440
        self.initial_height = 900
        self.min_width = 1100
        self.min_height = 700

        flags = pygame.FULLSCREEN if self.settings.is_fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode(
            (self.initial_width, self.initial_height),
            flags
        )
        pygame.display.set_caption("Nusantara Property Tycoon — Game Monopoli Indonesia")

        self.clock = pygame.time.Clock()
        self.input_handler = InputHandler()
        self.engine = GameEngine()

        # Initialize and configure audio
        self.audio = AudioManager.get_instance()
        self.audio.set_master_volume(self.settings.master_volume)
        self.audio.set_music_volume(self.settings.music_volume)
        self.audio.set_sfx_volume(self.settings.sfx_volume)
        self.audio.set_mute(self.settings.is_muted)
        self.audio.start_bgm()

        # Navigation state
        self.current_screen_id = "MENU"
        self.active_screen = None

        # Screens
        self.main_menu = MainMenuScreen(
            on_new_game=self._open_setup,
            on_load_game=self._load_game,
            on_rules=self._open_rules,
            on_settings=self._open_settings,
            on_quit=self._quit
        )
        self.setup_screen = SetupScreen(
            on_start=self._start_match,
            on_back=self._open_menu
        )
        self.rules_screen = RulesScreen(
            on_back=self._open_menu
        )
        self.settings_screen = SettingsScreen(
            self.settings,
            on_back=self._open_menu
        )
        self.gameplay_screen: Optional[GamePlayScreen] = None

        self._switch_screen("MENU")

    def _switch_screen(self, screen_id: str) -> None:
        self.current_screen_id = screen_id
        w, h = self.screen.get_size()

        if screen_id == "MENU":
            self.active_screen = self.main_menu
        elif screen_id == "SETUP":
            self.active_screen = self.setup_screen
        elif screen_id == "RULES":
            self.active_screen = self.rules_screen
        elif screen_id == "SETTINGS":
            self.active_screen = self.settings_screen
        elif screen_id == "GAME":
            self.active_screen = self.gameplay_screen

        if self.active_screen and hasattr(self.active_screen, "update_layout"):
            self.active_screen.update_layout(w, h)

    def _open_menu(self) -> None:
        self._switch_screen("MENU")

    def _open_setup(self) -> None:
        self._switch_screen("SETUP")

    def _open_rules(self) -> None:
        self._switch_screen("RULES")

    def _open_settings(self) -> None:
        self._switch_screen("SETTINGS")

    def _start_match(self, player_configs) -> None:
        self.engine.initialize_game(player_configs)
        self.gameplay_screen = GamePlayScreen(self.engine, self.settings, on_main_menu=self._open_menu)
        self._switch_screen("GAME")

    def _load_game(self) -> None:
        data, msg = SaveManager.load_game()
        if data:
            self.engine.load_dict(data)
            self.gameplay_screen = GamePlayScreen(self.engine, self.settings, on_main_menu=self._open_menu)
            self._switch_screen("GAME")
            self.engine.log(msg)
        else:
            self.engine.log(f"Gagal memuat: {msg}")

    def _quit(self) -> None:
        pygame.quit()
        sys.exit(0)

    def run(self) -> None:
        """Main game loop with delta-time animation updates and 60 FPS cap."""
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0

            # Handle events
            running = self.input_handler.process_events(self.active_screen)

            # Update active screen animations, toasts, and timers
            if self.active_screen and hasattr(self.active_screen, "update"):
                self.active_screen.update(dt)

            # Render
            if self.active_screen and hasattr(self.active_screen, "draw"):
                self.active_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def main():
    app = NusantaraGameApp()
    app.run()


if __name__ == "__main__":
    main()
