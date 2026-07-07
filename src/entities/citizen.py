import pygame
import random
import math
from .entity import Entity
from src.core import config

class Citizen(Entity):
    def __init__(self, x, y, language_system, world, asset_manager=None):
        super().__init__(x, y, 8, 18)

        self.language = language_system
        self.world = world
        self.asset_manager = asset_manager

        self.skin_color = config.COLORS["skin_default"]
        self.shirt_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.pants_color = config.COLORS["pants_default"]

        self.state = "IDLE"
        self.state_timer = 0
        self.target_x = self.x
        self.target_y = self.y
        self.speed = 15

        self.thought = ""
        self.thought_timer = 0
        self.thought_surface = None

        self.first_name = "Неизвестный"
        self.last_name = "Гражданин"
        if self.language:
            self.first_name = self.language.get_word("first_names")
            self.last_name = self.language.get_word("last_names")

        self.age = random.randint(18, 80)
        self.job = "Безработный"

        self.generate_thought()

    def generate_thought(self):
        if self.language:
            self.thought = self.language.generate_thought()
            self.thought_timer = random.uniform(7.0, 10.0)

            if self.thought and self.asset_manager:
                font_size = config.FONTS["thought_size"]
                self.thought_surface = self.asset_manager.render_text(self.thought, font_size, config.COLORS["black"])
            else:
                self.thought_surface = None

    def _check_collision(self, check_x, check_y):
        """Возвращает True, если житель столкнется со стеной в переданных координатах."""
        # Уменьшаем хитбокс по ширине на 2 пикселя с каждой стороны,
        # чтобы они могли спокойно проходить в двери (ширина двери 16px)
        margin_x = 2
        # Хитбокс по Y - это только самый низ ног (последние 4 пикселя)
        foot_height = 4

        # 4 точки: Левый-верх ног, Правый-верх ног, Левый-низ, Правый-низ
        points = [
            (check_x + margin_x, check_y + self.height - foot_height),
            (check_x + self.width - margin_x, check_y + self.height - foot_height),
            (check_x + margin_x, check_y + self.height - 1),
            (check_x + self.width - margin_x, check_y + self.height - 1)
        ]

        for px, py in points:
            tile_idx = self.world.get_tile_index(px, py)
            if tile_idx is not None:
                tile = self.world.tile_registry.get_tile(tile_idx)
                if tile and tile.is_solid:
                    return True
        return False

    def update(self, dt):
        if self.thought_timer > 0:
            self.thought_timer -= dt
            if self.thought_timer <= 0:
                self.thought = ""
                self.thought_surface = None
                self.thought_timer = -random.uniform(5.0, 15.0)
        elif self.thought_timer < 0:
            self.thought_timer += dt
            if self.thought_timer >= 0:
                self.generate_thought()

        if self.state == "IDLE":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "WANDER"
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(10, 50)
                self.target_x = self.x + math.cos(angle) * distance
                self.target_y = self.y + math.sin(angle) * distance

                if self.world:
                    max_world_x = self.world.WORLD_WIDTH * self.world.CHUNK_SIZE * self.world.TILE_SIZE
                    max_world_y = self.world.WORLD_HEIGHT * self.world.CHUNK_SIZE * self.world.TILE_SIZE
                else:
                    max_world_x = config.WORLD_WIDTH * config.CHUNK_SIZE * config.TILE_SIZE
                    max_world_y = config.WORLD_HEIGHT * config.CHUNK_SIZE * config.TILE_SIZE

                self.target_x = max(0, min(self.target_x, max_world_x - self.width))
                self.target_y = max(0, min(self.target_y, max_world_y - self.height))

        elif self.state == "WANDER":
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.hypot(dx, dy)

            if dist < 1.0:
                self.state = "IDLE"
                self.state_timer = random.uniform(1.0, 4.0)
            else:
                step_x = (dx / dist) * self.speed * dt
                step_y = (dy / dist) * self.speed * dt

                # Двигаем по X
                if not self._check_collision(self.x + step_x, self.y):
                    self.x += step_x

                # Двигаем по Y независимо от X (позволяет скользить вдоль стен)
                if not self._check_collision(self.x, self.y + step_y):
                    self.y += step_y

                # Если мы застряли и не можем двигаться ни по X, ни по Y,
                # нужно сбросить цель, чтобы выбрать новый путь.
                if self._check_collision(self.x + step_x, self.y) and self._check_collision(self.x, self.y + step_y):
                    self.state = "IDLE"
                    self.state_timer = random.uniform(0.5, 1.5)
                    self.target_x = self.x
                    self.target_y = self.y

    def check_click(self, mouse_world_x, mouse_world_y):
        rect = self.get_rect()
        return rect.collidepoint(mouse_world_x, mouse_world_y)

    def render(self, surface, camera):
        screen_rect = camera.apply(self.get_rect())

        sx = int(screen_rect.x)
        sy = int(screen_rect.y)

        head_h = int((6 / 18) * screen_rect.height)
        body_h = int((7 / 18) * screen_rect.height)
        legs_h = screen_rect.height - head_h - body_h

        body_w = int(screen_rect.width)
        head_w = int((6 / 8) * screen_rect.width)
        head_offset_x = (body_w - head_w) // 2

        pygame.draw.rect(surface, self.pants_color, (sx, sy + head_h + body_h, body_w, legs_h))
        pygame.draw.rect(surface, self.shirt_color, (sx, sy + head_h, body_w, body_h))
        pygame.draw.rect(surface, self.skin_color, (sx + head_offset_x, sy, head_w, head_h))

        if self.thought_timer > 0 and self.thought_surface:
            text_rect = self.thought_surface.get_rect()

            padding = 4
            bubble_rect = pygame.Rect(
                0, 0,
                text_rect.width + padding * 2,
                text_rect.height + padding * 2
            )
            bubble_rect.midbottom = (sx + body_w // 2, sy - 5)

            pygame.draw.rect(surface, config.COLORS["white"], bubble_rect, border_radius=4)
            pygame.draw.rect(surface, config.COLORS["black"], bubble_rect, width=1, border_radius=4)

            text_rect.center = bubble_rect.center
            surface.blit(self.thought_surface, text_rect)
