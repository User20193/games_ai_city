import pygame
from src.core import config

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
        self.default_font_path = config.FONTS["default_path"]
        self.MAX_CACHE_SIZE = 100 # LRU (или просто очистка) для предотвращения утечки

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
            # Очистка кэша, если он становится слишком большим (очень простая защита от утечки памяти динамичного текста)
            if len(self.text_cache) > self.MAX_CACHE_SIZE:
                # Очищаем только половину самых старых ключей (Python 3.7+ гарантирует порядок вставки в dict)
                keys_to_delete = list(self.text_cache.keys())[:self.MAX_CACHE_SIZE//2]
                for k in keys_to_delete:
                    del self.text_cache[k]

            font = self.get_font(size, path)
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]

    def clear_text_cache(self):
        self.text_cache.clear()
