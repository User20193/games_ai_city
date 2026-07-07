import pygame
import random
from .base_state import State
from src.core.camera import Camera
from src.world.world import World
from src.entities.citizen import Citizen
from src.systems.entity_manager import EntityManager
from src.systems.time_system import TimeSystem
from src.ui.passport import PassportUI
from src.core import config

class PlayState(State):
    def __init__(self, game):
        super().__init__(game)

        self.world = World(self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT)
        self.camera = Camera(self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT)

        world_pixel_width = self.world.WORLD_WIDTH * self.world.CHUNK_SIZE * self.world.TILE_SIZE
        world_pixel_height = self.world.WORLD_HEIGHT * self.world.CHUNK_SIZE * self.world.TILE_SIZE

        self.camera.x = (world_pixel_width / 2) - (self.camera.width / 2)
        self.camera.y = (world_pixel_height / 2) - (self.camera.height / 2)

        self.show_roofs = True

        self.time_system = TimeSystem(self.game)
        self.entity_manager = EntityManager()

        self.passport_ui = PassportUI(self.game.asset_manager)
        self.selected_citizen = None

        mayor_x = world_pixel_width / 2
        mayor_y = world_pixel_height / 2
        mayor = Citizen(mayor_x, mayor_y, self.game.language, self.world, self.game.asset_manager)
        mayor.job = "Мэр" # Жестко задаем профессию первому жителю
        self.entity_manager.add_entity(mayor)

        # Спавним еще парочку жителей для тестов
        for _ in range(5):
            cx = mayor_x + random.randint(-100, 100)
            cy = mayor_y + random.randint(-100, 100)
            c = Citizen(cx, cy, self.game.language, self.world, self.game.asset_manager)
            self.entity_manager.add_entity(c)

        self.last_debug_text = ""
        self.cached_debug_surf = None

    def update(self, dt, events):
        self.time_system.update(dt)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.exit_state()
                elif event.key == pygame.K_r:
                    self.show_roofs = not self.show_roofs
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Обработка клика по жителям
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Переводим экранные координаты мыши в мировые
                world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)

                clicked_citizen = None
                # Проверяем в обратном порядке, чтобы кликать по тому, кто рисуется поверх других (последним)
                for entity in reversed(self.entity_manager.entities):
                    if isinstance(entity, Citizen) and entity.check_click(world_x, world_y):
                        clicked_citizen = entity
                        break

                self.selected_citizen = clicked_citizen

        keys = pygame.key.get_pressed()
        self.camera.update(dt, keys, events)
        self.camera.update_screen_size(self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT)
        self.entity_manager.update(dt)

    def render(self, surface):
        surface.fill(config.COLORS["void_bg"])

        self.world.render_ground(surface, self.camera)
        self.entity_manager.render(surface, self.camera)

        if self.show_roofs:
            self.world.render_roof(surface, self.camera)

        self.time_system.render_day_night_cycle(surface)

        debug_text = f"Cam: ({int(self.camera.x)}, {int(self.camera.y)}) | Zoom: {self.camera.zoom:.2f}"

        if debug_text != self.last_debug_text or not self.cached_debug_surf:
            self.last_debug_text = debug_text
            try:
                font_size = config.FONTS["menu_size"]
                self.cached_debug_surf = self.game.asset_manager.render_text(debug_text, font_size, config.COLORS["white"])
            except:
                pass

        if self.cached_debug_surf:
            surface.blit(self.cached_debug_surf, (10, 10))

        self.time_system.render_ui(surface)

        # Отрисовка паспорта поверх всего
        if self.selected_citizen:
            self.passport_ui.render(surface, self.selected_citizen, self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT)
