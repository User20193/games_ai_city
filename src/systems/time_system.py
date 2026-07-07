import pygame

class TimeSystem:
    def __init__(self, game):
        self.game = game
        self.game_time = 12.0 # Начинаем в полдень (12:00)
        self.time_speed = 1.0 # 1 игровой час проходит за 1 реальную минуту (1 / 60 часов в секунду)

        # Кэш для UI
        self.last_text = ""
        self.cached_ui_surf = None
        self.cached_shadow_surf = None

    def update(self, dt):
        self.game_time += dt * (self.time_speed / 60.0)
        if self.game_time >= 24.0:
            self.game_time -= 24.0

    def render_day_night_cycle(self, surface):
        """Отрисовывает полупрозрачный слой в зависимости от времени суток."""
        alpha = 0

        if self.game_time < 5.0 or self.game_time > 20.0:
            alpha = 180 # Ночь
        elif 5.0 <= self.game_time < 8.0:
            # Рассвет (светлеет)
            progress = (self.game_time - 5.0) / 3.0
            alpha = int(180 * (1.0 - progress))
        elif 17.0 <= self.game_time <= 20.0:
            # Закат (темнеет)
            progress = (self.game_time - 17.0) / 3.0
            alpha = int(180 * progress)

        if alpha > 0:
            dark_surface = pygame.Surface((self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT), pygame.SRCALPHA)
            dark_surface.fill((10, 10, 30, alpha))
            surface.blit(dark_surface, (0, 0))

    def render_ui(self, surface):
        """Отрисовывает интерфейс времени."""
        hours = int(self.game_time)
        minutes = int((self.game_time - hours) * 60)
        time_str = f"{hours:02d}:{minutes:02d}"

        status = "День"
        if self.game_time < 6.0 or self.game_time > 20.0:
            status = "Ночь"
        elif 6.0 <= self.game_time < 9.0:
            status = "Утро"
        elif 18.0 <= self.game_time <= 20.0:
            status = "Вечер"

        text = f"{status} | {time_str}"

        # Обновляем кэш если текст изменился
        if text != self.last_text or not self.cached_ui_surf:
            self.last_text = text
            try:
                self.cached_shadow_surf = self.game.asset_manager.render_text(text, 24, (0, 0, 0))
                self.cached_ui_surf = self.game.asset_manager.render_text(text, 24, (255, 255, 255))
            except:
                pass

        if self.cached_shadow_surf and self.cached_ui_surf:
            surface.blit(self.cached_shadow_surf, (self.game.WINDOW_WIDTH - 250 + 2, 12))
            surface.blit(self.cached_ui_surf, (self.game.WINDOW_WIDTH - 250, 10))
