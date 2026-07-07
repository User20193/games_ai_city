import pygame
from src.core import config

class PassportUI:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self.width = 320 # Увеличили ширину (было 300)
        self.height = 190 # Чуть увеличили высоту (было 180)
        self.padding = 15

        # Цвета
        self.bg_color = config.COLORS["passport_bg"]
        self.border_color = config.COLORS["passport_border"]
        self.text_color = config.COLORS["white"]
        self.accent_color = config.COLORS["passport_accent"]
        self.photo_bg = config.COLORS["passport_photo_bg"]

        # Шрифты
        self.title_size = config.FONTS["passport_title"]
        self.text_size = config.FONTS["passport_text"]
        self.small_size = config.FONTS["passport_small"]

        # Кэшируем полупрозрачную подложку
        self.bg_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.bg_surf, self.bg_color, (0, 0, self.width, self.height), border_radius=8)

    def render(self, surface, citizen, screen_width, screen_height):
        if not citizen:
            return

        # Позиция: справа по центру
        x = screen_width - self.width - 20
        y = (screen_height - self.height) // 2

        # Подложка
        bg_rect = pygame.Rect(x, y, self.width, self.height)

        # Рисуем полупрозрачный фон из кэша
        surface.blit(self.bg_surf, (x, y))

        # Рамка
        pygame.draw.rect(surface, self.border_color, bg_rect, width=2, border_radius=8)

        # Заголовок (пишем Паспорт, чтобы гарантированно влезло)
        title = self.asset_manager.render_text("Паспорт", self.title_size, self.border_color)
        surface.blit(title, (x + self.padding, y + self.padding))

        # Линия под заголовком
        pygame.draw.line(surface, self.border_color,
                         (x + self.padding, y + self.padding + 30),
                         (x + self.width - self.padding, y + self.padding + 30), 2)

        content_y = y + self.padding + 45

        # --- ФОТО (Аватарка) ---
        photo_size = 64
        photo_rect = pygame.Rect(x + self.padding, content_y, photo_size, photo_size)

        # Фон фото
        pygame.draw.rect(surface, self.photo_bg, photo_rect)
        pygame.draw.rect(surface, self.border_color, photo_rect, width=2)

        # Рисуем "человечка" внутри фото
        # Пропорции: Голова 6/18, Тело 7/18 от высоты.
        # Поскольку это фото на паспорт, мы рисуем его укрупненно (по пояс).
        p_head_h = int((6 / 13) * photo_size) # Берем только 13 единиц (голова 6 + тело 7)
        p_body_h = photo_size - p_head_h

        p_body_w = int(photo_size * 0.8) # Ширина тела чуть меньше ширины фото
        p_head_w = int((6 / 8) * p_body_w)

        center_offset_x = (photo_size - p_body_w) // 2
        head_offset_x = center_offset_x + (p_body_w - p_head_w) // 2

        # Тело
        pygame.draw.rect(surface, citizen.shirt_color, (x + self.padding + center_offset_x, content_y + p_head_h, p_body_w, p_body_h))
        # Голова
        pygame.draw.rect(surface, citizen.skin_color, (x + self.padding + head_offset_x, content_y + int(photo_size*0.1), p_head_w, p_head_h))

        # --- ДАННЫЕ ---
        text_x = x + self.padding + photo_size + 15

        # Имя
        name_label = self.asset_manager.render_text("Имя:", self.small_size, self.accent_color)
        surface.blit(name_label, (text_x, content_y))
        name_val = self.asset_manager.render_text(citizen.first_name, self.text_size, self.text_color)
        surface.blit(name_val, (text_x, content_y + 15))

        # Фамилия
        last_label = self.asset_manager.render_text("Фамилия:", self.small_size, self.accent_color)
        surface.blit(last_label, (text_x, content_y + 40))
        last_val = self.asset_manager.render_text(citizen.last_name, self.text_size, self.text_color)
        surface.blit(last_val, (text_x, content_y + 55))

        # Возраст и Профессия внизу
        bottom_y = content_y + photo_size + 15

        age_label = self.asset_manager.render_text(f"Возраст: {citizen.age}", self.text_size, self.text_color)
        surface.blit(age_label, (x + self.padding, bottom_y))

        # Пишем просто "Работа:"
        job_label = self.asset_manager.render_text(f"Работа: {citizen.job}", self.text_size, self.text_color)
        surface.blit(job_label, (x + self.padding, bottom_y + 25))
