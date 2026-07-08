import pygame
from src.core import config

class PassportUI:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self.width = 280
        self.height = 420
        self.padding = 15

        self.bg_color = config.COLORS["passport_bg"]
        self.border_color = config.COLORS["passport_border"]
        self.text_color = config.COLORS["white"]
        self.accent_color = config.COLORS["passport_accent"]
        self.photo_bg = config.COLORS["passport_photo_bg"]

        self.title_size = config.FONTS["passport_title"]
        self.text_size = config.FONTS["passport_text"]
        self.small_size = config.FONTS["passport_small"]

        self.bg_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.bg_surf, self.bg_color, (0, 0, self.width, self.height), border_radius=12)

        # Состояние выдвижной панели (потребностей)
        self.is_needs_open = False
        self.needs_height = 120
        self.current_needs_y = 0.0

        # Состояние вкладки Биография
        self.is_bio_open = False
        self.bio_width = 300
        self.current_bio_x = 0.0

    def check_tab_click(self, mouse_pos, screen_width, screen_height):
        x = screen_width - self.width - 20
        y = (screen_height - self.height) // 2

        # Клик по нижней вкладке (Потребности)
        tab_w = 60
        tab_h = 15
        tab_y = y + self.height + int(self.current_needs_y)
        tab_rect = pygame.Rect(x + (self.width - tab_w)//2, tab_y, tab_w, tab_h)

        # Клик по боковой вкладке (Биография)
        bio_tab_w = 20
        bio_tab_h = 80
        bio_tab_x = x - bio_tab_w - int(self.current_bio_x)
        bio_tab_y = y + 50
        bio_tab_rect = pygame.Rect(bio_tab_x, bio_tab_y, bio_tab_w, bio_tab_h)

        if tab_rect.collidepoint(mouse_pos):
            self.is_needs_open = not self.is_needs_open
            return True
        elif bio_tab_rect.collidepoint(mouse_pos):
            self.is_bio_open = not self.is_bio_open
            return True
        return False

    def update(self, dt):
        target_y = self.needs_height if self.is_needs_open else 0.0
        self.current_needs_y += (target_y - self.current_needs_y) * 15 * dt

        target_x = self.bio_width if self.is_bio_open else 0.0
        self.current_bio_x += (target_x - self.current_bio_x) * 15 * dt

    def _draw_text_wrapped(self, surface, text, font_size, color, rect):
        words = text.split(' ')
        lines = []
        current_line = []

        # Хакаем, т.к. AssetManager возвращает готовый Surface, а не Font
        # Получим сам объект Font из AssetManager для расчетов ширины
        font = self.asset_manager.get_font(font_size)

        for word in words:
            current_line.append(word)
            fw, fh = font.size(' '.join(current_line))
            if fw > rect.width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))

        y = rect.top
        for line in lines:
            if not line: continue
            line_surf = self.asset_manager.render_text(line, font_size, color)
            surface.blit(line_surf, (rect.left, y))
            y += font.size(line)[1] + 4

    def render(self, surface, citizen, screen_width, screen_height):
        if not citizen:
            return

        x = screen_width - self.width - 20
        y = (screen_height - self.height) // 2

        # --- Выдвижная панель потребностей (рисуется ПОД паспортом) ---
        if self.current_needs_y > 1:
            needs_rect = pygame.Rect(x + 10, y + self.height - 20, self.width - 20, int(self.current_needs_y) + 20)
            pygame.draw.rect(surface, (50, 55, 65, 230), needs_rect, border_bottom_left_radius=12, border_bottom_right_radius=12)
            pygame.draw.rect(surface, self.border_color, needs_rect, width=2, border_bottom_left_radius=12, border_bottom_right_radius=12)

            # Контент потребностей
            if self.current_needs_y > 40:
                content_y = y + self.height + 5

                # Деньги
                money = getattr(citizen, 'money', 0)
                money_surf = self.asset_manager.render_text(f"Баланс: {money} L", self.small_size, (255, 215, 0))
                surface.blit(money_surf, (x + 25, content_y))

                # Запасы еды
                food = getattr(citizen, 'food_supplies', 0)
                food_surf = self.asset_manager.render_text(f"Еда дома: {food}", self.small_size, self.text_color)
                surface.blit(food_surf, (x + 25, content_y + 20))

                # Шкала голода
                hunger = getattr(citizen, 'hunger', 100.0)
                hunger_surf = self.asset_manager.render_text("Сытость:", self.small_size, self.text_color)
                surface.blit(hunger_surf, (x + 25, content_y + 45))

                # Корзина продуктов
                cart = getattr(citizen, 'shopping_cart', [])
                if len(cart) > 0:
                    cart_str = "В корзине: " + ", ".join(cart[:3])
                    if len(cart) > 3: cart_str += "..."
                    cart_surf = self.asset_manager.render_text(cart_str, 10, (150, 255, 150))
                    surface.blit(cart_surf, (x + 25, content_y + 65))


                bar_x = x + 90
                bar_y = content_y + 45
                bar_w = self.width - 130
                bar_h = 12

                pygame.draw.rect(surface, (100, 30, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                fill_w = max(0, int(bar_w * (hunger / 100.0)))

                # Цвет шкалы зависит от уровня голода
                bar_color = (50, 200, 50) if hunger > 50 else ((200, 200, 50) if hunger > 25 else (255, 50, 50))
                if fill_w > 0:
                    pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
                pygame.draw.rect(surface, self.border_color, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)

                # --- Выдвижная боковая панель (Биография) ---
        if self.current_bio_x > 1:
            bio_rect = pygame.Rect(x - int(self.current_bio_x), y + 20, int(self.current_bio_x) + 10, self.height - 40)
            pygame.draw.rect(surface, (40, 45, 55, 240), bio_rect, border_top_left_radius=12, border_bottom_left_radius=12)
            pygame.draw.rect(surface, self.border_color, bio_rect, width=2, border_top_left_radius=12, border_bottom_left_radius=12)

            if self.current_bio_x > 50:
                bio_title = self.asset_manager.render_text("БИОГРАФИЯ", self.title_size, self.border_color)
                surface.blit(bio_title, (x - int(self.current_bio_x) + 15, y + 35))

                pygame.draw.line(surface, self.border_color,
                         (x - int(self.current_bio_x) + 15, y + 65),
                         (x - 15, y + 65), 2)

                bio_text = getattr(citizen, 'biography', "Нет данных о прошлом...")
                text_rect = pygame.Rect(x - int(self.current_bio_x) + 15, y + 80, self.bio_width - 30, self.height - 100)

                self._draw_text_wrapped(surface, bio_text, self.small_size, self.text_color, text_rect)

        # --- Боковой язычок (Биография) ---
        bio_tab_w = 20
        bio_tab_h = 80
        bio_tab_x = x - bio_tab_w - int(self.current_bio_x) + 2
        bio_tab_y = y + 50
        bio_tab_rect = pygame.Rect(bio_tab_x, bio_tab_y, bio_tab_w, bio_tab_h)
        pygame.draw.rect(surface, self.bg_color, bio_tab_rect, border_top_left_radius=6, border_bottom_left_radius=6)
        pygame.draw.rect(surface, self.border_color, bio_tab_rect, width=2, border_top_left_radius=6, border_bottom_left_radius=6)

        # Иконка книжки на язычке (или просто текст)
        b_text = self.asset_manager.render_text("B", 14, self.border_color)
        surface.blit(b_text, (bio_tab_x + 5, bio_tab_y + 30))

        # --- Основная панель паспорта ---
        bg_rect = pygame.Rect(x, y, self.width, self.height)
        surface.blit(self.bg_surf, (x, y))
        pygame.draw.rect(surface, self.border_color, bg_rect, width=3, border_radius=12)

        # Язычок
        tab_w = 60
        tab_h = 15
        tab_y = y + self.height + int(self.current_needs_y) - 2 # -2 чтобы скрыть шов
        tab_rect = pygame.Rect(x + (self.width - tab_w)//2, tab_y, tab_w, tab_h)
        pygame.draw.rect(surface, self.bg_color, tab_rect, border_bottom_left_radius=6, border_bottom_right_radius=6)
        pygame.draw.rect(surface, self.border_color, tab_rect, width=2, border_bottom_left_radius=6, border_bottom_right_radius=6)

        # Заголовок
        title = self.asset_manager.render_text("ID-КАРТА", self.title_size, self.border_color)
        title_rect = title.get_rect(centerx=x + self.width // 2, top=y + self.padding)
        surface.blit(title, title_rect)

        pygame.draw.line(surface, self.border_color,
                         (x + self.padding, y + self.padding + 25),
                         (x + self.width - self.padding, y + self.padding + 25), 2)

        content_y = y + self.padding + 40

        # ФОТО
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

        # ДАННЫЕ СТОЛБИКОМ
        text_y = content_y + photo_size + 15

        name_str = f"{citizen.first_name} {citizen.last_name}"
        name_val = self.asset_manager.render_text(name_str, self.title_size, self.text_color)
        name_rect = name_val.get_rect(centerx=x + self.width // 2, top=text_y)
        surface.blit(name_val, name_rect)

        text_y += 35

        def draw_stacked_stat(label, value, y_pos):
            lbl_surf = self.asset_manager.render_text(label, self.small_size, self.accent_color)
            surface.blit(lbl_surf, (x + self.padding + 10, y_pos))
            val_surf = self.asset_manager.render_text(str(value), self.text_size, self.text_color)
            surface.blit(val_surf, (x + self.padding + 10, y_pos + 16))
            return y_pos + 42

        text_y = draw_stacked_stat("Возраст:", citizen.age, text_y)
        text_y = draw_stacked_stat("Работа:", citizen.job, text_y)
        home_str = getattr(citizen, 'home', 'Бездомный')
        draw_stacked_stat("Жилье:", home_str, text_y)
