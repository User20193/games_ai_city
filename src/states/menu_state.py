import pygame
import random
from .base_state import State
from src.ui.components import Button
from src.core import config

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.mouse_pos = (0, 0)

        self.bg_surface = pygame.Surface((self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT))
        self.generate_background()

        center_x = self.game.WINDOW_WIDTH // 2
        start_y = 300
        gap = 70
        base_color = config.COLORS["btn_base"]
        hover_color = config.COLORS["btn_hover"]

        self.buttons = {
            "new_game": Button(center_x, start_y, "Новая Игра", self.game.menu_font, base_color, hover_color),
            "settings": Button(center_x, start_y + gap, "Настройки", self.game.menu_font, base_color, hover_color),
            "credits": Button(center_x, start_y + gap * 2, "Авторы", self.game.menu_font, base_color, hover_color),
            "quit": Button(center_x, start_y + gap * 3, "Выйти", self.game.menu_font, base_color, hover_color)
        }

    def generate_background(self):
        # 1. Градиентное небо
        r_top, g_top, b_top = config.COLORS["menu_sky_top"]
        r_bot, g_bot, b_bot = config.COLORS["menu_sky_bottom"]

        for y in range(self.game.WINDOW_HEIGHT):
            ratio = y / self.game.WINDOW_HEIGHT
            r = int(r_top + (r_bot - r_top) * ratio)
            g = int(g_top + (g_bot - g_top) * ratio)
            b = int(b_top + (b_bot - b_top) * ratio)
            pygame.draw.line(self.bg_surface, (r, g, b), (0, y), (self.game.WINDOW_WIDTH, y))

        # 2. Звезды
        for _ in range(150):
            x = random.randint(0, self.game.WINDOW_WIDTH)
            y = random.randint(0, self.game.WINDOW_HEIGHT // 2)
            alpha = random.randint(100, 255)
            star = pygame.Surface((2, 2), pygame.SRCALPHA)
            star.fill((255, 255, 255, alpha))
            self.bg_surface.blit(star, (x, y))

        # 3. Силуэты зданий
        building_color = config.COLORS["menu_building"]
        win_colors = [config.COLORS["menu_window_1"], config.COLORS["menu_window_2"]]

        x = 0
        while x < self.game.WINDOW_WIDTH:
            width = random.randint(40, 120)
            height = random.randint(100, 400)
            rect = pygame.Rect(x, self.game.WINDOW_HEIGHT - height, width, height)
            pygame.draw.rect(self.bg_surface, building_color, rect)

            for win_x in range(x + 5, x + width - 10, 15):
                for win_y in range(self.game.WINDOW_HEIGHT - height + 10, self.game.WINDOW_HEIGHT - 10, 20):
                    if random.random() > 0.7:
                        window_color = random.choice(win_colors)
                        pygame.draw.rect(self.bg_surface, window_color, (win_x, win_y, 8, 12))

            x += width + random.randint(2, 10)

    def update(self, dt, events):
        self.mouse_pos = pygame.mouse.get_pos()

        for btn in self.buttons.values():
            btn.update(self.mouse_pos)

        for event in events:
            if self.buttons["quit"].check_click(self.mouse_pos, event):
                self.game.running = False
            elif self.buttons["new_game"].check_click(self.mouse_pos, event):
                from src.states.play_state import PlayState
                play_state = PlayState(self.game)
                play_state.enter_state()
            elif self.buttons["settings"].check_click(self.mouse_pos, event):
                print("Clicked: Settings (Not implemented yet)")
            elif self.buttons["credits"].check_click(self.mouse_pos, event):
                print("Clicked: Credits (Not implemented yet)")

    def render(self, surface):
        surface.blit(self.bg_surface, (0, 0))

        title_text = config.TITLE
        font_size = config.FONTS["title_size"]

        title_shadow = self.game.asset_manager.render_text(title_text, font_size, config.COLORS["black"])
        shadow_rect = title_shadow.get_rect(center=(self.game.WINDOW_WIDTH // 2 + 4, 154))
        surface.blit(title_shadow, shadow_rect)

        title_surf = self.game.asset_manager.render_text(title_text, font_size, config.COLORS["white"])
        title_rect = title_surf.get_rect(center=(self.game.WINDOW_WIDTH // 2, 150))
        surface.blit(title_surf, title_rect)

        for btn in self.buttons.values():
            btn.draw(surface)
