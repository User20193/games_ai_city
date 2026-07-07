import pygame
import random
import math
from .entity import Entity
from src.core import config
from .pathfinding import astar_search

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
        self.home_building = f"Многоэтажка {random.randint(1, 2)}"
        self.home_apt = random.randint(1, 40)
        self.home = f"Дом {self.home_building.split(' ')[1]}, Кв. {self.home_apt}"

        self.is_visible = True
        self.time_system = None
        self.market_system = None # Ссылка на рынок

        self.path = []

        # Экономика и потребности
        self.money = 1000
        self.hunger = random.uniform(50.0, 100.0)
        self.food_supplies = random.randint(0, 5)

        self.generate_thought()

    def generate_thought(self):
        if self.language:
            # Если очень голоден, думает только о еде
            if self.hunger < 30.0:
                food = self.language.get_word("nouns") # в идеале отфильтровать съедобное
                self.thought = f"Хочется {food}..."
            else:
                self.thought = self.language.generate_thought()

            self.thought_timer = random.uniform(7.0, 10.0)

            if self.thought and self.asset_manager:
                font_size = config.FONTS["thought_size"]
                self.thought_surface = self.asset_manager.render_text(self.thought, font_size, config.COLORS["black"])
            else:
                self.thought_surface = None

    def _check_collision(self, check_x, check_y):
        margin_x = 2
        foot_height = 4

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

    def _move_towards_target(self, dt):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < 1.0:
            return True

        step_x = (dx / dist) * self.speed * dt
        step_y = (dy / dist) * self.speed * dt

        if not self._check_collision(self.x + step_x, self.y):
            self.x += step_x

        if not self._check_collision(self.x, self.y + step_y):
            self.y += step_y

        return False

    def update(self, dt):
        # Обновление потребностей
        # Ускорение падения голода если время ускорено
        speed_mult = self.time_system.time_speed if self.time_system else 1.0
        # Голод падает на 10 единиц в игровой час (60 сек)
        self.hunger -= (10.0 / 60.0) * dt * speed_mult
        if self.hunger < 0: self.hunger = 0.0
        if self.hunger > 100.0: self.hunger = 100.0

        # Питание дома (утром или вечером, если есть запасы)
        if self.state == "SLEEPING_INSIDE" and self.hunger < 80.0 and self.food_supplies > 0:
            self.food_supplies -= 1
            self.hunger = 100.0

        # 1. Расписание
        if self.time_system:
            t = self.time_system.game_time
            is_night = (t >= 22.0 or t < 6.0)

            # Работа кассиром
            if self.job == "Кассир" and not is_night:
                if 7.8 <= t < 19.8: # Рабочая смена 07:50 - 19:50
                    if self.state != "WORKING":
                        self.state = "WORKING"
                        if self.world and self.world.shop_cashier_pos:
                            start_pos = (self.x + self.width/2, self.y + self.height)
                            self.path = astar_search(self.world, start_pos, self.world.shop_cashier_pos)
                            if self.path:
                                self.target_x, self.target_y = self.path.pop(0)
                                self.target_x -= self.width / 2
                                self.target_y -= self.height
                            else:
                                self.target_x, self.target_y = self.world.shop_cashier_pos
                                self.target_x -= self.width / 2
                                self.target_y -= self.height
                elif self.state == "WORKING":
                    self.state = "IDLE" # Смена закончилась

            # Поход в магазин за едой (только днем, если не кассир)
            if self.job != "Кассир" and not is_night and self.state in ["IDLE", "WANDER"]:
                # Если голоден или нет еды дома
                if (self.hunger < 40.0 or self.food_supplies == 0) and self.money >= 50:
                    self.state = "SHOPPING_GOTO_SHELF"
                    if self.world and self.world.shop_shelves:
                        shelf_pos = random.choice(self.world.shop_shelves)
                        start_pos = (self.x + self.width/2, self.y + self.height)
                        self.path = astar_search(self.world, start_pos, shelf_pos)
                        if self.path:
                            self.target_x, self.target_y = self.path.pop(0)
                            self.target_x -= self.width / 2
                            self.target_y -= self.height

            # Комендантский час
            if is_night and self.state not in ["GOING_HOME", "SLEEPING_INSIDE"]:
                self.state = "GOING_HOME"
                door_coords = self.world.building_doors.get(self.home_building)
                if door_coords:
                    start_pos = (self.x + self.width/2, self.y + self.height)
                    self.path = astar_search(self.world, start_pos, door_coords)

                    if self.path:
                        self.target_x, self.target_y = self.path.pop(0)
                        self.target_x -= self.width / 2
                        self.target_y -= self.height
                    else:
                        self.target_x, self.target_y = door_coords
                        self.target_x -= self.width / 2
                        self.target_y -= self.height
                else:
                    self.is_visible = False
                    self.state = "SLEEPING_INSIDE"

            elif not is_night and self.state == "SLEEPING_INSIDE":
                self.state = "IDLE"
                self.is_visible = True
                self.state_timer = 2.0

        if self.state == "SLEEPING_INSIDE":
            self.thought_timer = 0
            self.thought = ""
            self.thought_surface = None
            return

        # 2. Обновление мыслей
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

        # 3. FSM
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
            reached = self._move_towards_target(dt)
            if reached:
                self.state = "IDLE"
                self.state_timer = random.uniform(1.0, 4.0)

        elif self.state in ["GOING_HOME", "WORKING", "SHOPPING_GOTO_SHELF", "SHOPPING_GOTO_CASHIER"]:
            reached = self._move_towards_target(dt)
            if reached:
                if self.path:
                    self.target_x, self.target_y = self.path.pop(0)
                    self.target_x -= self.width / 2
                    self.target_y -= self.height
                else:
                    # Достигли финальной точки
                    if self.state == "GOING_HOME":
                        self.state = "SLEEPING_INSIDE"
                        self.is_visible = False
                    elif self.state == "WORKING":
                        # Пришли на кассу, стоим работаем
                        pass
                    elif self.state == "SHOPPING_GOTO_SHELF":
                        # Дошли до полки, выбираем товар (стоим 2 сек)
                        self.state = "SHOPPING_PICKING"
                        self.state_timer = 2.0
                    elif self.state == "SHOPPING_GOTO_CASHIER":
                        # Дошли до кассы, покупаем
                        if self.market_system:
                            price = self.market_system.buy_goods()
                            if self.money >= price:
                                self.money -= price
                                self.food_supplies += 3 # Купили еды
                                self.hunger = 100.0 # Поели по дороге
                        self.state = "IDLE" # Идем гулять дальше

        elif self.state == "SHOPPING_PICKING":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "SHOPPING_GOTO_CASHIER"
                if self.world and hasattr(self.world, 'shop_queue_pos'):
                    start_pos = (self.x + self.width/2, self.y + self.height)
                    self.path = astar_search(self.world, start_pos, self.world.shop_queue_pos)
                    if self.path:
                        self.target_x, self.target_y = self.path.pop(0)
                        self.target_x -= self.width / 2
                        self.target_y -= self.height


    def check_click(self, mouse_world_x, mouse_world_y):
        if not self.is_visible:
            return False
        rect = self.get_rect()
        return rect.collidepoint(mouse_world_x, mouse_world_y)

    def render(self, surface, camera):
        if not self.is_visible:
            return

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

    def render_ui(self, surface, camera):
        if not self.is_visible:
            return

        if self.thought_timer > 0 and self.thought_surface:
            screen_rect = camera.apply(self.get_rect())
            sx = int(screen_rect.x)
            sy = int(screen_rect.y)
            body_w = int(screen_rect.width)

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
