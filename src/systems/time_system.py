import pygame
from src.core import config

class TimeSystem:
    def __init__(self, game):
        self.game = game
        self.game_time = config.TIME_START_HOUR
        self.time_speed = config.TIME_SPEED_MULTIPLIER

        # Кэш для UI
        self.last_text = ""
        self.cached_ui_surf = None
        self.cached_shadow_surf = None

        # Размеры выпадающей панельки
        self.ui_width = 180
        self.ui_height = 50

        # Кэш иконок
        self.icons = self._generate_icons()

    def _generate_icons(self):
        """Программно генерирует пиксельные иконки для фаз времени (24x24)."""
        icons = {}
        size = 24

        # Иконка солнца
        sun = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(sun, (255, 215, 0), (size//2, size//2), 8) # Желтый круг
        # Лучи (пиксельные линии)
        pygame.draw.line(sun, (255, 215, 0), (size//2, 2), (size//2, 4), 2)
        pygame.draw.line(sun, (255, 215, 0), (size//2, size-5), (size//2, size-3), 2)
        pygame.draw.line(sun, (255, 215, 0), (2, size//2), (4, size//2), 2)
        pygame.draw.line(sun, (255, 215, 0), (size-5, size//2), (size-3, size//2), 2)
        icons["sun"] = sun

        # Иконка луны
        moon = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(moon, (200, 200, 220), (size//2, size//2), 8)
        # Вырезаем "тень", чтобы получился месяц
        pygame.draw.circle(moon, (0, 0, 0, 0), (size//2 - 4, size//2 - 4), 7)
        icons["moon"] = moon

        # Иконка восхода/заката (половинка солнца на горизонте)
        half_sun = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(half_sun, (255, 140, 0), (size//2, size//2 + 4), 8)
        # Отрезаем нижнюю половину
        pygame.draw.rect(half_sun, (0, 0, 0, 0), (0, size//2 + 4, size, size))
        # Горизонт
        pygame.draw.line(half_sun, (100, 100, 255), (2, size//2 + 4), (size-3, size//2 + 4), 2)
        icons["half_sun"] = half_sun

        return icons

    def get_time_phase(self):
        """
        Возвращает фазу времени и соответствующий ей цвет и иконку.
        Утро: 06:00 - 12:00
        День: 12:00 - 18:00
        Вечер: 18:00 - 00:00
        Ночь: 00:00 - 06:00
        Дополнительно (для визуала):
        Рассвет 05:00 - 07:00
        Закат 18:00 - 20:00
        """
        t = self.game_time
        if 5.0 <= t < 7.0:
            return "Рассвет", (255, 200, 150), self.icons["half_sun"]
        elif 7.0 <= t < 12.0:
            return "Утро", (255, 255, 200), self.icons["sun"]
        elif 12.0 <= t < 18.0:
            return "День", (255, 255, 255), self.icons["sun"]
        elif 18.0 <= t < 20.0:
            return "Закат", (255, 150, 150), self.icons["half_sun"]
        elif 20.0 <= t < 24.0:
            return "Вечер", (150, 150, 200), self.icons["moon"]
        else: # 0.0 - 5.0
            return "Ночь", (100, 100, 150), self.icons["moon"]

    def update(self, dt):
        self.game_time += dt * (self.time_speed / 60.0)
        if self.game_time >= 24.0:
            self.game_time -= 24.0

    def render_day_night_cycle(self, surface):
        """Отрисовывает полупрозрачный слой в зависимости от времени суток."""
        alpha = 0
        t = self.game_time

        if t < 5.0 or t >= 20.0:
            alpha = 180 # Ночь
        elif 5.0 <= t < 7.0:
            # Рассвет (светлеет)
            progress = (t - 5.0) / 2.0
            alpha = int(180 * (1.0 - progress))
        elif 18.0 <= t < 20.0:
            # Закат (темнеет)
            progress = (t - 18.0) / 2.0
            alpha = int(180 * progress)

        if alpha > 0:
            dark_surface = pygame.Surface((self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT), pygame.SRCALPHA)
            base_r, base_g, base_b = config.COLORS["night_filter"]
            dark_surface.fill((base_r, base_g, base_b, alpha))
            surface.blit(dark_surface, (0, 0))

    def render_ui(self, surface):
        """Отрисовывает выпадающую панельку со временем сверху по центру."""
        hours = int(self.game_time)
        minutes = int((self.game_time - hours) * 60)
        time_str = f"{hours:02d}:{minutes:02d}"

        phase_name, phase_color, icon = self.get_time_phase()

        # Размеры панельки
        x = (self.game.WINDOW_WIDTH - self.ui_width) // 2
        y = 0

        # Рисуем подложку (как бы висит сверху)
        panel_rect = pygame.Rect(x, y, self.ui_width, self.ui_height)
        pygame.draw.rect(surface, (40, 45, 55, 230), panel_rect, border_bottom_left_radius=15, border_bottom_right_radius=15)
        pygame.draw.rect(surface, config.COLORS["passport_border"], panel_rect, width=2, border_bottom_left_radius=15, border_bottom_right_radius=15)

        # Рисуем "язычок" снизу (декоративный элемент)
        tab_w = 40
        tab_h = 10
        tab_rect = pygame.Rect(x + (self.ui_width - tab_w)//2, y + self.ui_height, tab_w, tab_h)
        pygame.draw.rect(surface, (40, 45, 55, 230), tab_rect, border_bottom_left_radius=5, border_bottom_right_radius=5)
        pygame.draw.rect(surface, config.COLORS["passport_border"], tab_rect, width=2, border_bottom_left_radius=5, border_bottom_right_radius=5)

        # Отрисовка иконки слева
        surface.blit(icon, (x + 15, y + 12))

        # Отрисовка названия фазы (с цветом, зависящим от времени суток)
        phase_surf = self.game.asset_manager.render_text(phase_name, config.FONTS["passport_small"], phase_color)
        surface.blit(phase_surf, (x + 45, y + 15))

        # Отрисовка самого времени (справа)
        # Если время изменилось, обновляем кэш
        if time_str != self.last_text or not self.cached_ui_surf:
            self.last_text = time_str
            self.cached_ui_surf = self.game.asset_manager.render_text(time_str, config.FONTS["passport_title"], config.COLORS["white"])

        if self.cached_ui_surf:
            # Выравниваем по правому краю
            time_rect = self.cached_ui_surf.get_rect(right=x + self.ui_width - 15, centery=y + self.ui_height//2)
            surface.blit(self.cached_ui_surf, time_rect)
