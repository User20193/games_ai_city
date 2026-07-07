import pygame
import os

class AssetManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.fonts = {}
        self.text_cache = {}
        self.default_font_path = os.path.join("assets", "fonts", "pixel_font.ttf")

    def get_font(self, size, path=None):
        if path is None:
            path = self.default_font_path

        key = (path, size)
        if key not in self.fonts:
            try:
                self.fonts[key] = pygame.font.Font(path, size)
            except:
                self.fonts[key] = pygame.font.Font(None, size)

        return self.fonts[key]

    def render_text(self, text, size, color, path=None):
        key = (text, size, color, path)
        if key not in self.text_cache:
            font = self.get_font(size, path)
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]

    def clear_text_cache(self):
        self.text_cache.clear()
