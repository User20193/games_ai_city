import sys
import pygame
import os

os.environ['SDL_VIDEODRIVER'] = 'dummy'

try:
    from src.core import config
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

    from src.data.language import LanguageSystem
    lang = LanguageSystem()

    from src.world.world import World
    from src.systems.asset_manager import AssetManager

    w = World(800, 600)
    am = AssetManager()

    # Check that Citizen anim logic passes compilation
    from src.entities.citizen import Citizen
    c = Citizen(0,0,lang,w,am)
    c.update(0.016)

    from src.core.camera import Camera
    cam = Camera(800, 600)
    c.render(screen, cam)

    # Check roof rendering passes compilation
    w.render_roof(screen, cam)

    # Check lighting rendering passes compilation
    from src.systems.time_system import TimeSystem
    ts = TimeSystem(w)
    ts.lights = [(0,0,10,(255,255,255,100))]
    ts.render_day_night_cycle(screen, cam)

    print("Test: Compilation passed.")
    sys.exit(0)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
