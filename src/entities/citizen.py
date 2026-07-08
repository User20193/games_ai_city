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
        self.market_system = None

        self.path = []

        self.money = 1000
        self.hunger = random.uniform(50.0, 100.0)
        self.food_supplies = random.randint(0, 5)

        self.has_groceries = False # Пакет с едой в руках
        self.shopping_cart = []
        self.shopping_list = []
        self.shopping_budget = 0
        self.queue_index = -1 # Позиция в очереди

        self.generate_thought()

    def generate_thought(self):
        if self.language:
            if self.hunger < 30.0:
                food = self.language.get_word("nouns")
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
        speed_mult = self.time_system.time_speed if self.time_system else 1.0
        self.hunger -= (10.0 / 60.0) * dt * speed_mult
        if self.hunger < 0: self.hunger = 0.0
        if self.hunger > 100.0: self.hunger = 100.0

        if self.hunger < 40.0 and self.food_supplies > 0:
            self.food_supplies -= 1
            self.hunger = 100.0

        if self.time_system:
            t = self.time_system.game_time
            is_night = (t >= 22.0 or t < 6.0)

            if self.job == "Кассир" and not is_night:
                if 7.8 <= t < 19.8:
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
                    self.state = "IDLE"

            # Если не кассир, голоден или нет еды и есть деньги
            if self.job != "Кассир" and not is_night and self.state in ["IDLE", "WANDER"]:
                if (self.hunger < 40.0 or self.food_supplies == 0) and self.money >= 15 and not self.has_groceries:
                    self.state = "SHOPPING_GOTO_SHELF"

                    # Генерируем список покупок
                    self.shopping_list = []
                    self.shopping_cart = []
                    self.shopping_budget = self.money

                    if self.market_system and hasattr(self.market_system, 'catalog'):
                        # Если совсем нет запасов, берем несколько товаров, если голод - берем 1-2 чтобы поесть
                        items_to_buy = random.randint(3, 5) if self.food_supplies == 0 else random.randint(1, 2)

                        all_items = []
                        for dept, items in self.market_system.catalog.items():
                            for item_name in items.keys():
                                all_items.append((dept, item_name))

                        random.shuffle(all_items)
                        for dept, item_name in all_items:
                            price = self.market_system.get_item_price(item_name)
                            if self.shopping_budget >= price:
                                self.shopping_list.append({"dept": dept, "name": item_name})
                                self.shopping_budget -= price
                            if len(self.shopping_list) >= items_to_buy:
                                break

                    self._goto_next_shelf()

            if is_night and self.state not in ["GOING_HOME", "SLEEPING_INSIDE"]:
                # Если наступила ночь, а мы были в очереди - выходим
                if self.queue_index != -1 and self in self.world.shop_queue:
                    self.world.shop_queue.remove(self)
                    self.queue_index = -1

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
                # Если у нас есть продукты в руках, идем домой, а не гуляем
                if self.has_groceries:
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

        elif self.state in ["GOING_HOME", "WORKING", "SHOPPING_GOTO_SHELF"]:
            reached = self._move_towards_target(dt)
            if reached:
                if self.path:
                    self.target_x, self.target_y = self.path.pop(0)
                    self.target_x -= self.width / 2
                    self.target_y -= self.height
                else:
                    if self.state == "GOING_HOME":
                        if self.has_groceries:
                            # Дошли домой с едой!
                            self.has_groceries = False
                            # За каждую вещь в корзине получаем +1 к запасам (и очищаем корзину)
                            self.food_supplies += len(self.shopping_cart)
                            self.shopping_cart.clear()
                            self.hunger = 100.0 # Немного перекусили сразу
                            self.state = "IDLE" # Идем гулять снова (если день)
                        else:
                            self.state = "SLEEPING_INSIDE"
                            self.is_visible = False
                    elif self.state == "WORKING":
                        pass
                    elif self.state == "SHOPPING_GOTO_SHELF":
                        self.state = "SHOPPING_WAITING_SHELF"
                        self.state_timer = 1.0 # Берет товар с полки

        elif self.state == "SHOPPING_WAITING_SHELF":
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.shopping_list:
                    item = self.shopping_list.pop(0)
                    self.shopping_cart.append(item["name"])

                if self.shopping_list:
                    self.state = "SHOPPING_GOTO_SHELF"
                    self._goto_next_shelf()
                else:
                    self.state = "SHOPPING_PICKING"
                    self.state_timer = 0

        elif self.state == "SHOPPING_PICKING":
            self.state_timer -= dt
            if self.state_timer <= 0:
                # Встаем в очередь
                if len(self.world.shop_queue) < len(self.world.shop_queue_slots):
                    self.world.shop_queue.append(self)
                    self.queue_index = len(self.world.shop_queue) - 1
                    self.state = "IN_QUEUE"
                    self.path = [] # Сбрасываем путь, чтобы построить новый до очереди
                else:
                    # Очередь заполнена, уходим расстроенными
                    self.shopping_cart.clear() # Бросаем корзину
                    self.state = "IDLE"

        elif self.state == "IN_QUEUE":
            # Узнаем свою позицию в очереди
            try:
                self.queue_index = self.world.shop_queue.index(self)
            except ValueError:
                self.queue_index = -1
                self.state = "IDLE"
                return

            # Идем к своему слоту в очереди
            slot_pos = self.world.shop_queue_slots[self.queue_index]

            # Если мы далеко от своего слота, используем astar
            dist_to_slot = math.hypot(self.x + self.width/2 - slot_pos[0], self.y + self.height - slot_pos[1])

            if dist_to_slot > 10.0 and not self.path:
                start_pos = (self.x + self.width/2, self.y + self.height)
                new_path = astar_search(self.world, start_pos, slot_pos)
                if new_path:
                    self.path = new_path

            if self.path:
                self.target_x, self.target_y = self.path[0]
                self.target_x -= self.width / 2
                self.target_y -= self.height
                reached = self._move_towards_target(dt)
                if reached:
                    self.path.pop(0)
            else:
                self.target_x = slot_pos[0] - self.width / 2
                self.target_y = slot_pos[1] - self.height
                reached = self._move_towards_target(dt)

                if reached and self.queue_index == 0:
                    # Мы на кассе (слот 0)!
                    self.state = "PAYING"
                    self.state_timer = 1.0 # Ждем 1 сек на оплату

        elif self.state == "PAYING":
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.market_system and self.shopping_cart:
                    price = self.market_system.buy_cart(self.shopping_cart)
                    if self.money >= price:
                        self.money -= price
                        self.has_groceries = True # Теперь несем пакет домой!
                    else:
                        self.shopping_cart.clear() # Не хватило денег (хотя алгоритм считал, но цены могли вырасти)

                # Выходим из очереди
                if self in self.world.shop_queue:
                    self.world.shop_queue.remove(self)
                self.queue_index = -1
                self.state = "IDLE" # Перейдет в GOING_HOME автоматически


    def _goto_next_shelf(self):
        if not self.shopping_list:
            # Корзина собрана, идем на кассу (В очередь)
            self.state = "SHOPPING_PICKING"
            self.state_timer = 0
            return

        next_item = self.shopping_list[0]
        dept = next_item["dept"]

        if self.world and hasattr(self.world, 'shop_departments'):
            dept_coords = self.world.shop_departments.get(dept)
            if dept_coords:
                shelf_pos = random.choice(dept_coords)
                start_pos = (self.x + self.width/2, self.y + self.height)
                self.path = astar_search(self.world, start_pos, shelf_pos)
                if self.path:
                    self.target_x, self.target_y = self.path.pop(0)
                    self.target_x -= self.width / 2
                    self.target_y -= self.height
                else:
                    # Если путь не найден, просто скипаем предмет
                    self.shopping_list.pop(0)
                    self._goto_next_shelf()
            else:
                self.shopping_list.pop(0)
                self._goto_next_shelf()

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

        # Рисуем пакет с едой в руках
        if self.has_groceries:
            bag_w = 6
            bag_h = 8
            # Рисуем сбоку (справа)
            bag_x = sx + body_w
            bag_y = sy + head_h + body_h // 2
            # Коричневый бумажный пакет
            pygame.draw.rect(surface, (139, 69, 19), (bag_x, bag_y, bag_w, bag_h))
            # Маленький "продукт" (зеленый листик) торчит из пакета
            pygame.draw.rect(surface, (50, 200, 50), (bag_x + 1, bag_y - 2, 4, 2))

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
