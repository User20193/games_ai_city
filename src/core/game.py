import pygame
import sys
from src.data.language import LanguageSystem
from src.systems.asset_manager import AssetManager
from src.core import config

class Game:
    def __init__(self):
        pygame.init()
        self.WINDOW_WIDTH = config.WINDOW_WIDTH
        self.WINDOW_HEIGHT = config.WINDOW_HEIGHT
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption(config.TITLE)

        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0

        # Стек состояний
        self.state_stack = []

        # Загрузка глобальных ресурсов и подсистем
        self.language = LanguageSystem()
        self.asset_manager = AssetManager()
        self.load_assets()

    def load_assets(self):
        self.title_font = self.asset_manager.get_font(config.FONTS["title_size"])
        self.menu_font = self.asset_manager.get_font(config.FONTS["menu_size"])

    def get_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
        return events

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            display_info = pygame.display.Info()
            self.WINDOW_WIDTH = display_info.current_w
            self.WINDOW_HEIGHT = display_info.current_h
            self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.FULLSCREEN)
        else:
            self.WINDOW_WIDTH = config.WINDOW_WIDTH
            self.WINDOW_HEIGHT = config.WINDOW_HEIGHT
            self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))

    def update(self, events):
        if self.state_stack:
            self.state_stack[-1].update(self.dt, events)

    def render(self):
        if self.state_stack:
            self.state_stack[-1].render(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.dt = self.clock.tick(config.TARGET_FPS) / 1000.0
            events = self.get_events()
            self.update(events)
            self.render()

        pygame.quit()
        sys.exit()
