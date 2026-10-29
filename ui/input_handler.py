"""Input handling and event loop routing with global shortcut support."""
import pygame
from typing import Optional, Any
from ui.audio import AudioManager


class InputHandler:
    def __init__(self):
        self.quit_requested = False

    def process_events(self, active_screen: Any) -> bool:
        """
        Process all pending Pygame events and forward to active screen.
        Returns False if the application should terminate.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
                return False

            elif event.type == pygame.VIDEORESIZE:
                # Handle window resizing
                w = max(1100, event.w)
                h = max(700, event.h)
                pygame.display.set_mode((w, h), pygame.RESIZABLE)
                if hasattr(active_screen, "update_layout"):
                    active_screen.update_layout(w, h)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    # Toggle fullscreen
                    pygame.display.toggle_fullscreen()
                    w, h = pygame.display.get_surface().get_size()
                    if hasattr(active_screen, "update_layout"):
                        active_screen.update_layout(w, h)
                elif event.key == pygame.K_m:
                    # Toggle sound mute shortcut
                    AudioManager.get_instance().toggle_mute()

            # Forward event to the active screen
            if hasattr(active_screen, "handle_event"):
                active_screen.handle_event(event)

        return not self.quit_requested
