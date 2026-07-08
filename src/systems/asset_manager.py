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

    def get_tile_texture(self, tile_name):
        """Возвращает процедурно сгенерированную текстуру 8x8 (Pygame Surface) по имени"""
        if not hasattr(self, 'textures'):
            self.textures = {}

        if tile_name in self.textures:
            return self.textures[tile_name]

        surf = pygame.Surface((8, 8), pygame.SRCALPHA)

        if tile_name == "MeatShelf_TopLeft":
            surf.fill((200, 200, 220)) # Холодильник
            pygame.draw.rect(surf, (220, 50, 50), (1, 3, 3, 2)) # Мясо
            pygame.draw.rect(surf, (255, 100, 100), (5, 4, 2, 2)) # Мясо
            pygame.draw.line(surf, (150, 150, 180), (0,0), (7,0))

        elif tile_name == "MeatShelf_TopRight":
            surf.fill((200, 200, 220))
            pygame.draw.rect(surf, (220, 50, 50), (2, 2, 4, 3))
            pygame.draw.line(surf, (150, 150, 180), (0,0), (7,0))
            pygame.draw.line(surf, (150, 150, 180), (7,0), (7,7))

        elif tile_name == "MeatShelf_BotLeft":
            surf.fill((200, 200, 220))
            pygame.draw.rect(surf, (255, 150, 150), (2, 2, 3, 2)) # Рыба
            pygame.draw.line(surf, (150, 150, 180), (0,0), (0,7))
            pygame.draw.line(surf, (150, 150, 180), (0,7), (7,7))

        elif tile_name == "MeatShelf_BotRight":
            surf.fill((200, 200, 220))
            pygame.draw.rect(surf, (255, 150, 150), (1, 3, 4, 2))
            pygame.draw.line(surf, (150, 150, 180), (7,0), (7,7))
            pygame.draw.line(surf, (150, 150, 180), (0,7), (7,7))

        # Овощи/Фрукты (Зеленые лотки)
        elif tile_name == "FruitShelf_TopLeft":
            surf.fill((50, 120, 50))
            pygame.draw.rect(surf, (255, 50, 50), (2, 2, 4, 4)) # Яблоки
            pygame.draw.line(surf, (30, 80, 30), (0,0), (7,0))

        elif tile_name == "FruitShelf_TopRight":
            surf.fill((50, 120, 50))
            pygame.draw.rect(surf, (255, 255, 0), (1, 2, 5, 3)) # Бананы

        elif tile_name == "FruitShelf_BotLeft":
            surf.fill((50, 120, 50))
            pygame.draw.rect(surf, (255, 150, 0), (2, 2, 4, 4)) # Апельсины
            pygame.draw.line(surf, (30, 80, 30), (0,7), (7,7))

        elif tile_name == "FruitShelf_BotRight":
            surf.fill((50, 120, 50))
            pygame.draw.rect(surf, (200, 50, 200), (2, 1, 4, 5)) # Виноград
            pygame.draw.line(surf, (30, 80, 30), (0,7), (7,7))

        # Молочка (Белый стеллаж)
        elif tile_name == "DairyShelf_TopLeft":
            surf.fill((240, 240, 255))
            pygame.draw.rect(surf, (50, 50, 255), (1, 2, 2, 4)) # Пакет молока
            pygame.draw.rect(surf, (50, 50, 255), (5, 2, 2, 4))
            pygame.draw.line(surf, (200, 200, 220), (0,0), (7,0))

        elif tile_name == "DairyShelf_TopRight":
            surf.fill((240, 240, 255))
            pygame.draw.rect(surf, (255, 255, 50), (2, 3, 4, 3)) # Сыр

        elif tile_name == "DairyShelf_BotLeft":
            surf.fill((240, 240, 255))
            pygame.draw.rect(surf, (255, 200, 200), (1, 3, 2, 3)) # Йогурт
            pygame.draw.rect(surf, (255, 200, 200), (5, 3, 2, 3))
            pygame.draw.line(surf, (200, 200, 220), (0,7), (7,7))

        elif tile_name == "DairyShelf_BotRight":
            surf.fill((240, 240, 255))
            pygame.draw.rect(surf, (255, 255, 200), (1, 4, 6, 2)) # Масло
            pygame.draw.line(surf, (200, 200, 220), (0,7), (7,7))

        # Бакалея (Деревянные полки)
        elif tile_name == "GroceryShelf_TopLeft":
            surf.fill((139, 69, 19))
            pygame.draw.rect(surf, (240, 230, 210), (1, 1, 3, 5)) # Мука

        elif tile_name == "GroceryShelf_TopRight":
            surf.fill((139, 69, 19))
            pygame.draw.rect(surf, (150, 100, 50), (2, 2, 4, 3)) # Хлеб

        elif tile_name == "GroceryShelf_BotLeft":
            surf.fill((139, 69, 19))
            pygame.draw.rect(surf, (200, 200, 200), (1, 3, 5, 3)) # Сахар/Рис
            pygame.draw.line(surf, (101, 67, 33), (0,7), (7,7))

        elif tile_name == "GroceryShelf_BotRight":
            surf.fill((139, 69, 19))
            pygame.draw.rect(surf, (100, 50, 20), (2, 2, 4, 4)) # Гречка
            pygame.draw.line(surf, (101, 67, 33), (0,7), (7,7))

        elif tile_name == "Streetlamp":
            surf.fill((0, 0, 0, 0)) # Прозрачный фон
            pygame.draw.rect(surf, (50, 50, 60), (3, 3, 2, 5)) # Столб
            pygame.draw.rect(surf, (255, 255, 200), (2, 0, 4, 3)) # Лампа
            pygame.draw.rect(surf, (255, 255, 0), (3, 1, 2, 1)) # Яркая сердцевина

        self.textures[tile_name] = surf
        return surf
