"""
Visual Quality Validation — Script to render and save all 10 required screenshots.
Ensures headless rendering works using SDL_VIDEODRIVER='dummy' if needed, or normal window.
"""
import os
import pygame

# Set dummy audio driver if no audio device
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
pygame.font.init()

from game.engine import GameEngine
from game.settings import Settings
from game.state import GameState
from ui.screens import MainMenuScreen, SetupScreen, GamePlayScreen

SCREEN_W = 1440
SCREEN_H = 900
screen = pygame.Surface((SCREEN_W, SCREEN_H))
settings = Settings()

output_dir = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(output_dir, exist_ok=True)

artifact_dir = "/home/rezzypu/.gemini/antigravity/brain/30458dcb-1926-4bd5-8c65-c6b182a0a7bb/screenshots"
os.makedirs(artifact_dir, exist_ok=True)

def save_shot(name: str):
    path1 = os.path.join(output_dir, name)
    path2 = os.path.join(artifact_dir, name)
    pygame.image.save(screen, path1)
    pygame.image.save(screen, path2)
    print(f"Captured: {path1}")

# 1. Main Menu
menu = MainMenuScreen(lambda: None, lambda: None, lambda: None, lambda: None, lambda: None)
menu.update_layout(SCREEN_W, SCREEN_H)
menu.update(0.5)
menu.draw(screen)
save_shot("01_main_menu.png")

# 2. Player Setup
setup = SetupScreen(lambda cfgs: None, lambda: None)
setup.update_layout(SCREEN_W, SCREEN_H)
setup.update(0.5)
setup.draw(screen)
save_shot("02_player_setup.png")

# Setup game engine with rich game state for board and gameplay screenshots
engine = GameEngine()
engine.initialize_game([
    {"name": "Budi Santoso", "color": (231, 76, 60), "token_type": "monas"},
    {"name": "Siti Rahma", "color": (52, 152, 219), "token_type": "becak"},
    {"name": "Wayan Putra", "color": (46, 204, 113), "token_type": "pinisi"},
    {"name": "Agus Wijaya", "color": (241, 196, 15), "token_type": "komodo"}
])

# Give players some properties and buildings for rich board visual
# Budi owns Bogor properties with houses
t1 = engine.board.get_tile(1)
t3 = engine.board.get_tile(3)
t1.owner_id = 0
t3.owner_id = 0
t1.houses = 2
t3.houses = 2
engine.players[0].properties.extend([1, 3])

# Siti owns Bandung with 4 houses & hotel
t11 = engine.board.get_tile(11)
t13 = engine.board.get_tile(13)
t14 = engine.board.get_tile(14)
t11.owner_id = 1
t13.owner_id = 1
t14.owner_id = 1
t11.houses = 3
t13.houses = 4
t14.hotels = 1
engine.players[1].properties.extend([11, 13, 14])

# Wayan owns Bali
t21 = engine.board.get_tile(21)
t23 = engine.board.get_tile(23)
t21.owner_id = 2
t23.owner_id = 2
t21.houses = 1
engine.players[2].properties.extend([21, 23])

# Agus owns Surabaya
t16 = engine.board.get_tile(16)
t18 = engine.board.get_tile(18)
t16.owner_id = 3
t18.owner_id = 3
t18.is_mortgaged = True
engine.players[3].properties.extend([16, 18])

# Player positions around board
engine.players[0].position = 6
engine.players[1].position = 14
engine.players[2].position = 23
engine.players[3].position = 35

gameplay = GamePlayScreen(engine, settings, on_main_menu=lambda: None)
gameplay.update_layout(SCREEN_W, SCREEN_H)

# 3. Full Board (WAITING_FOR_ROLL)
engine.state = GameState.WAITING_FOR_ROLL
gameplay.update(0.016)
gameplay.draw(screen)
save_shot("03_full_board.png")

# 4. Dice Rolling
gameplay.dice_anim.start(4, 5, speed="Normal")
gameplay.dice_anim.update(0.2)  # mid-roll
gameplay.update(0.016)
gameplay.draw(screen)
save_shot("04_dice_rolling.png")
gameplay.dice_anim.is_active = False

# 5. Property Purchase Modal
engine.current_player.position = 6
engine.state = GameState.PROPERTY_DECISION
engine.pending_tile_pos = 6
gameplay.update_layout(SCREEN_W, SCREEN_H)
gameplay.draw(screen)
save_shot("05_property_purchase.png")

# 6. Property Development (Manage Assets Modal)
engine.state = GameState.WAITING_FOR_ROLL
gameplay.show_manage_modal = True
gameplay.update_layout(SCREEN_W, SCREEN_H)
gameplay.draw(screen)
save_shot("06_property_development.png")
gameplay.show_manage_modal = False

# 7. Chance Card Modal
engine.state = GameState.CARD_RESOLUTION
card = engine.cards.get_card_by_id("c_01")
if not card:
    card = engine.cards.draw_chance()
engine.current_card = card
gameplay.update_layout(SCREEN_W, SCREEN_H)
gameplay.draw(screen)
save_shot("07_chance_card.png")
engine.current_card = None

# 8. Auction Modal
from game.auction import Auction
tile_auc = engine.board.get_tile(8)
engine.auction = Auction(tile_auc, [0, 1, 2, 3])
engine.auction.place_bid(0, 1200000, 15000000)
engine.state = GameState.AUCTION
gameplay.update_layout(SCREEN_W, SCREEN_H)
gameplay.draw(screen)
save_shot("08_auction.png")
engine.auction = None

# 9. Jail Modal
engine.state = GameState.JAIL_DECISION
engine.current_player.in_jail = True
engine.current_player.jail_turns = 1
gameplay.update_layout(SCREEN_W, SCREEN_H)
gameplay.draw(screen)
save_shot("09_jail.png")
engine.current_player.in_jail = False

# 10. Game Over Modal
engine.state = GameState.GAME_OVER
engine.winner = engine.players[0]
engine.turn_count = 28
gameplay.update_layout(SCREEN_W, SCREEN_H)
gameplay.draw(screen)
save_shot("10_game_over.png")

print("All 10 visual validation screenshots captured successfully!")
