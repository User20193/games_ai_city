# Настройки окна
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TARGET_FPS = 60
TITLE = "Лисеу-Сити"

# Настройки мира и сетки
TILE_SIZE = 8
CHUNK_SIZE = 16
WORLD_WIDTH = 20  # В чанках
WORLD_HEIGHT = 20 # В чанках

# Цвета (RGB)
COLORS = {
    # UI и общие
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "void_bg": (30, 30, 30), # Фон за пределами карты

    # Кнопки
    "btn_base": (200, 200, 200),
    "btn_hover": (255, 215, 0),

    # UI Паспорта
    "passport_bg": (40, 45, 55, 230),
    "passport_border": (100, 150, 200),
    "passport_accent": (200, 200, 200),
    "passport_photo_bg": (100, 100, 120),

    # Сущности
    "skin_default": (255, 224, 189),
    "pants_default": (40, 40, 60),

    # Время суток (Фильтр)
    "night_filter": (10, 10, 30),

    # Декорации (Меню)
    "menu_sky_top": (10, 10, 40),
    "menu_sky_bottom": (40, 30, 90),
    "menu_building": (15, 15, 25),
    "menu_window_1": (255, 255, 100),
    "menu_window_2": (200, 200, 255),
}

# Шрифты
FONTS = {
    "default_path": "assets/fonts/pixel_font.ttf",
    "title_size": 48,
    "menu_size": 24,
    "thought_size": 12,
    "passport_title": 24,
    "passport_text": 18,
    "passport_small": 14
}

# Внутриигровое время
TIME_START_HOUR = 12.0
TIME_SPEED_MULTIPLIER = 1.0 # 1 реальная минута = 1 игровой час
