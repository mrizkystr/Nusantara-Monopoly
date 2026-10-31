"""
Dynamic 2.5D Camera System for Nusantara Property Tycoon.
Supports smooth panning, zooming, focusing on players/tiles, and screen-to-world coordinate mapping.
"""
import math
from enum import Enum
from typing import Tuple, Optional
import pygame


class CameraState(Enum):
    BOARD_OVERVIEW = "BOARD_OVERVIEW"
    PLAYER_FOCUS = "PLAYER_FOCUS"
    MOVEMENT_FOLLOW = "MOVEMENT_FOLLOW"
    PROPERTY_FOCUS = "PROPERTY_FOCUS"
    EVENT_FOCUS = "EVENT_FOCUS"


class Camera:
    """
    Interpolating 2D/2.5D camera system.
    Transforms board rendering space to screen viewport with smooth easing.
    """

    def __init__(self, viewport_width: int, viewport_height: int):
        self.viewport_w = viewport_width
        self.viewport_h = viewport_height

        # World focus point (center of camera view in world coordinates)
        self.world_x: float = viewport_width / 2.0
        self.world_y: float = viewport_height / 2.0
        self.target_x: float = self.world_x
        self.target_y: float = self.world_y

        # Zoom level (1.0 = normal overview, > 1.0 = zoomed in)
        self.zoom: float = 1.0
        self.target_zoom: float = 1.0

        # State machine
        self.state: CameraState = CameraState.BOARD_OVERVIEW
        self.default_center: Tuple[float, float] = (self.world_x, self.world_y)

        # Smooth damping factor (higher = faster snap, lower = smoother drift)
        self.pan_speed: float = 6.5
        self.zoom_speed: float = 5.0

        # Focus target reference
        self.focused_tile: Optional[int] = None
        self.auto_return_timer: float = 0.0

    def set_viewport(self, w: int, h: int, default_center: Optional[Tuple[float, float]] = None) -> None:
        """Update viewport dimensions on window resize."""
        self.viewport_w = w
        self.viewport_h = h
        if default_center:
            self.default_center = default_center
        else:
            self.default_center = (w / 2.0, h / 2.0)

        if self.state == CameraState.BOARD_OVERVIEW:
            self.target_x, self.target_y = self.default_center
            self.world_x, self.world_y = self.default_center
            self.target_zoom = 1.0
            self.zoom = 1.0

    def reset_overview(self) -> None:
        """Smoothly reset view to show the entire game board."""
        self.state = CameraState.BOARD_OVERVIEW
        self.target_x, self.target_y = self.default_center
        self.target_zoom = 1.0
        self.focused_tile = None
        self.auto_return_timer = 0.0

    def focus_tile(self, tile_center: Tuple[int, int], zoom: float = 1.25, state: CameraState = CameraState.PROPERTY_FOCUS, auto_return_sec: float = 0.0) -> None:
        """Smoothly pan and zoom to a specific tile center."""
        self.state = state
        self.target_x = float(tile_center[0])
        self.target_y = float(tile_center[1])
        self.target_zoom = zoom
        self.auto_return_timer = auto_return_sec

    def focus_player(self, token_pos: Tuple[int, int], zoom: float = 1.22) -> None:
        """Focus camera on the current active player token."""
        self.state = CameraState.PLAYER_FOCUS
        self.target_x = float(token_pos[0])
        self.target_y = float(token_pos[1])
        self.target_zoom = zoom
        self.auto_return_timer = 0.0

    def follow_movement(self, current_tile_center: Tuple[int, int]) -> None:
        """Smoothly follow player movement between tiles."""
        self.state = CameraState.MOVEMENT_FOLLOW
        self.target_x = float(current_tile_center[0])
        self.target_y = float(current_tile_center[1])
        self.target_zoom = 1.18

    def update(self, dt: float) -> None:
        """Advance camera interpolation."""
        # Pan interpolation using exponential smoothing
        t_pan = min(1.0, dt * self.pan_speed)
        self.world_x += (self.target_x - self.world_x) * t_pan
        self.world_y += (self.target_y - self.world_y) * t_pan

        # Zoom interpolation
        t_zoom = min(1.0, dt * self.zoom_speed)
        self.zoom += (self.target_zoom - self.zoom) * t_zoom

        # Auto return to overview timer
        if self.auto_return_timer > 0.0:
            self.auto_return_timer -= dt
            if self.auto_return_timer <= 0.0:
                self.reset_overview()

    def screen_to_world(self, screen_pt: Tuple[int, int]) -> Tuple[int, int]:
        """Convert screen mouse coordinates to world board coordinates."""
        sx, sy = screen_pt
        # Screen center
        sc_x = self.viewport_w / 2.0
        sc_y = self.viewport_h / 2.0

        # World offset from camera center
        wx = self.world_x + (sx - sc_x) / self.zoom
        wy = self.world_y + (sy - sc_y) / self.zoom
        return int(round(wx)), int(round(wy))

    def world_to_screen(self, world_pt: Tuple[int, int]) -> Tuple[int, int]:
        """Convert world coordinates to viewport screen coordinates."""
        wx, wy = world_pt
        sc_x = self.viewport_w / 2.0
        sc_y = self.viewport_h / 2.0

        sx = sc_x + (wx - self.world_x) * self.zoom
        sy = sc_y + (wy - self.world_y) * self.zoom
        return int(round(sx)), int(round(sy))

    def get_transform_matrix(self) -> Tuple[float, float, float]:
        """Return (offset_x, offset_y, zoom) for rendering pipeline."""
        sc_x = self.viewport_w / 2.0
        sc_y = self.viewport_h / 2.0
        off_x = sc_x - self.world_x * self.zoom
        off_y = sc_y - self.world_y * self.zoom
        return off_x, off_y, self.zoom
