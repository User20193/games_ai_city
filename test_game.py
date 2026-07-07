import sys
import pygame
import os

os.environ['SDL_VIDEODRIVER'] = 'dummy'

try:
    from src.core import config
    from src.states.main_menu import MainMenu
    from src.states.game_state import GameState

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    game_state = GameState(screen)

    for _ in range(5):
        game_state.update(0.016)

    print("Test: Basic update passed.")
    sys.exit(0)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
