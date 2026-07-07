import pygame
from src.core import config

class PassportUI:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        # Сделали шире (280) и прозрачнее
        self.width = 280
        self.height = 360
        self.padding = 15

        self.bg_color = config.COLORS["passport_bg"]
        self.border_color = config.COLORS["passport_border"]
        self.text_color = config.COLORS["white"]
        self.accent_color = config.COLORS["passport_accent"]
        self.photo_bg = config.COLORS["passport_photo_bg"]

        self.title_size = config.FONTS["passport_title"] # 20
        self.text_size = config.FONTS["passport_text"] # 16
        self.small_size = config.FONTS["passport_small"] # 12

        self.bg_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.bg_surf, self.bg_color, (0, 0, self.width, self.height), border_radius=12)

    def render(self, surface, citizen, screen_width, screen_height):
        if not citizen:
            return

        x = screen_width - self.width - 20
        y = (screen_height - self.height) // 2

        bg_rect = pygame.Rect(x, y, self.width, self.height)
        surface.blit(self.bg_surf, (x, y))
        pygame.draw.rect(surface, self.border_color, bg_rect, width=3, border_radius=12)

        title = self.asset_manager.render_text("ID-КАРТА", self.title_size, self.border_color)
        title_rect = title.get_rect(centerx=x + self.width // 2, top=y + self.padding)
        surface.blit(title, title_rect)

        pygame.draw.line(surface, self.border_color,
                         (x + self.padding, y + self.padding + 25),
                         (x + self.width - self.padding, y + self.padding + 25), 2)

        content_y = y + self.padding + 40

        # --- ФОТО ---
        photo_size = 80
        photo_x = x + (self.width - photo_size) // 2
        photo_rect = pygame.Rect(photo_x, content_y, photo_size, photo_size)

        pygame.draw.rect(surface, self.photo_bg, photo_rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, photo_rect, width=2, border_radius=4)

        p_head_h = int((6 / 13) * photo_size)
        p_body_h = photo_size - p_head_h

        p_body_w = int(photo_size * 0.8)
        p_head_w = int((6 / 8) * p_body_w)

        center_offset_x = (photo_size - p_body_w) // 2
        head_offset_x = center_offset_x + (p_body_w - p_head_w) // 2

        pygame.draw.rect(surface, citizen.shirt_color, (photo_x + center_offset_x, content_y + p_head_h, p_body_w, p_body_h))
        pygame.draw.rect(surface, citizen.skin_color, (photo_x + head_offset_x, content_y + int(photo_size*0.1), p_head_w, p_head_h))

        # --- ДАННЫЕ СТОЛБИКОМ ---
        text_y = content_y + photo_size + 15
        line_spacing = 25

        name_str = f"{citizen.first_name} {citizen.last_name}"
        name_val = self.asset_manager.render_text(name_str, self.title_size, self.text_color)
        name_rect = name_val.get_rect(centerx=x + self.width // 2, top=text_y)
        surface.blit(name_val, name_rect)

        text_y += line_spacing + 15

        def draw_stat(label, value, y_pos):
            lbl_surf = self.asset_manager.render_text(label, self.small_size, self.accent_color)
            val_surf = self.asset_manager.render_text(str(value), self.text_size, self.text_color)
            # Лейбл слева (чуть сдвинем правее для красоты)
            surface.blit(lbl_surf, (x + self.padding + 10, y_pos + 2)) # +2 для выравнивания с текстом
            # Значение справа
            val_rect = val_surf.get_rect(right=x + self.width - self.padding - 10, top=y_pos)
            surface.blit(val_surf, val_rect)

        draw_stat("Возраст:", citizen.age, text_y)
        text_y += line_spacing

        draw_stat("Работа:", citizen.job, text_y)
        text_y += line_spacing

        home_str = getattr(citizen, 'home', 'Бездомный')
        draw_stat("Жилье:", home_str, text_y)
