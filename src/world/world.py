import pygame
import random
from src.world.registry.tiles import TileRegistry
from src.systems.asset_manager import AssetManager
from src.world.generation.prefabs import get_city_hall_prefab, get_mayor_house_prefab, get_apartment_building_prefab, get_supermarket_prefab, get_bus_stop_prefab, apply_prefab
from src.core import config

class World:
    def __init__(self, screen_width, screen_height):
        self.TILE_SIZE = config.TILE_SIZE

        self.chunks_ground = {}
        self.chunks_roof = {}

        self.chunk_surfaces_ground = {}
        self.chunk_surfaces_roof = {}

        self.dirty_ground = set()
        self.dirty_roof = set()

        self.CHUNK_SIZE = config.CHUNK_SIZE

        self.WORLD_WIDTH = config.WORLD_WIDTH
        self.WORLD_HEIGHT = config.WORLD_HEIGHT

        self.tile_registry = TileRegistry()

        self._temp_surf_ground = None
        self._temp_surf_roof = None

        self.building_doors = {}

        self.shop_cashier_pos = None
        self.lights = [] # Координаты фонарей для освещения
        self.shop_departments = {
            "Крупы и бакалея": [],
            "Овощи": [],
            "Молочные продукты": [],
            "Фрукты": [],
            "Мясо и рыба": []
        }

        # Очередь покупателей (каждый элемент - ссылка на объект Citizen)
        self.shop_queue = []
        # Физические точки слотов очереди (мировые координаты)
        self.shop_queue_slots = []

        self.build_city_center()

    def get_tile_index(self, world_x, world_y, layer="ground"):
        tile_x = int(world_x // self.TILE_SIZE)
        tile_y = int(world_y // self.TILE_SIZE)

        chunk_x = tile_x // self.CHUNK_SIZE
        chunk_y = tile_y // self.CHUNK_SIZE

        ground_chunk, roof_chunk = self.get_chunk(chunk_x, chunk_y)
        if ground_chunk and roof_chunk:
            local_x = tile_x % self.CHUNK_SIZE
            local_y = tile_y % self.CHUNK_SIZE
            if layer == "ground":
                return ground_chunk[local_y][local_x]
            elif layer == "roof":
                return roof_chunk[local_y][local_x]
        return None

    def get_chunk(self, chunk_x, chunk_y):
        if chunk_x < 0 or chunk_x >= self.WORLD_WIDTH or chunk_y < 0 or chunk_y >= self.WORLD_HEIGHT:
            return None, None

        chunk_pos = (chunk_x, chunk_y)
        if chunk_pos not in self.chunks_ground:
            ground_data = [[0 for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]
            roof_data = [[None for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]

            self.chunks_ground[chunk_pos] = ground_data
            self.chunks_roof[chunk_pos] = roof_data
            self.render_chunk_surface(chunk_x, chunk_y)

        return self.chunks_ground[chunk_pos], self.chunks_roof[chunk_pos]

    def render_chunk_surface(self, chunk_x, chunk_y):
        ground_chunk = self.chunks_ground.get((chunk_x, chunk_y))
        roof_chunk = self.chunks_roof.get((chunk_x, chunk_y))
        if not ground_chunk or not roof_chunk: return

        pixel_size = self.CHUNK_SIZE * self.TILE_SIZE

        key = (chunk_x, chunk_y)
        if key not in self.chunk_surfaces_ground:
            self.chunk_surfaces_ground[key] = pygame.Surface((pixel_size, pixel_size))

        surf_ground = self.chunk_surfaces_ground[key]
        surf_ground.fill((0, 0, 0))

        for ty in range(self.CHUNK_SIZE):
            for tx in range(self.CHUNK_SIZE):
                color_idx = ground_chunk[ty][tx]
                if color_idx is not None:
                    tile = self.tile_registry.get_tile(color_idx)
                    rect = pygame.Rect(tx * self.TILE_SIZE, ty * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE)

                    drawn = False
                    if hasattr(tile, 'texture_name') and tile.texture_name:
                        try:
                            from src.systems.asset_manager import AssetManager
                            am = AssetManager()
                            tex = am.get_tile_texture(tile.texture_name)
                            if tex:
                                surf_ground.blit(tex, rect)
                                drawn = True
                        except Exception as e:
                            pass

                    if not drawn:
                        pygame.draw.rect(surf_ground, tile.color, rect)

        if key not in self.chunk_surfaces_roof:
            self.chunk_surfaces_roof[key] = pygame.Surface((pixel_size, pixel_size), pygame.SRCALPHA)

        surf_roof = self.chunk_surfaces_roof[key]
        surf_roof.fill((0, 0, 0, 0))

        for ty in range(self.CHUNK_SIZE):
            for tx in range(self.CHUNK_SIZE):
                color_idx = roof_chunk[ty][tx]
                if color_idx is not None:
                    tile = self.tile_registry.get_tile(color_idx)
                    rect = pygame.Rect(tx * self.TILE_SIZE, ty * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE)
                    pygame.draw.rect(surf_roof, tile.color, rect)

    def set_tile_by_index(self, tile_x, tile_y, color_idx, layer="ground"):
        chunk_x = tile_x // self.CHUNK_SIZE
        chunk_y = tile_y // self.CHUNK_SIZE

        ground_chunk, roof_chunk = self.get_chunk(chunk_x, chunk_y)
        if ground_chunk and roof_chunk:
            local_x = tile_x % self.CHUNK_SIZE
            local_y = tile_y % self.CHUNK_SIZE
            if layer == "ground":
                ground_chunk[local_y][local_x] = color_idx
                self.dirty_ground.add((chunk_x, chunk_y))
            elif layer == "roof":
                roof_chunk[local_y][local_x] = color_idx
                self.dirty_roof.add((chunk_x, chunk_y))

    def update_dirty_chunks(self):
        chunks_to_render = self.dirty_ground.union(self.dirty_roof)
        for chunk_x, chunk_y in chunks_to_render:
            self.render_chunk_surface(chunk_x, chunk_y)

        self.dirty_ground.clear()
        self.dirty_roof.clear()

    def build_city_center(self):
        import random
        for cy in range(self.WORLD_HEIGHT):
            for cx in range(self.WORLD_WIDTH):
                self.get_chunk(cx, cy)

        max_tx = self.WORLD_WIDTH * self.CHUNK_SIZE
        max_ty = self.WORLD_HEIGHT * self.CHUNK_SIZE

        center_tx = max_tx // 2
        center_ty = max_ty // 2

        # === 1. ДОРОЖНАЯ СЕТЬ (КРЕСТОВИНА) ===
        hw_y = center_ty
        hw_x = center_tx - 15 # Вертикальная дорога немного смещена

        def draw_road_h(y_start):
            for x in range(max_tx):
                self.set_tile_by_index(x, y_start - 2, 4, layer="ground")
                self.set_tile_by_index(x, y_start - 1, 12, layer="ground")
                self.set_tile_by_index(x, y_start, 13 if x % 4 < 2 else 12, layer="ground")
                self.set_tile_by_index(x, y_start + 1, 12, layer="ground")
                self.set_tile_by_index(x, y_start + 2, 4, layer="ground")

                if x % 15 == 0 and x > 5 and x < max_tx - 5:
                    self.set_tile_by_index(x, y_start - 3, 33, layer="ground")
                    self.lights.append((x * self.TILE_SIZE + self.TILE_SIZE/2, (y_start - 3) * self.TILE_SIZE, 80, (255, 255, 150, 80)))
                    self.set_tile_by_index(x+7, y_start + 3, 33, layer="ground")
                    self.lights.append(((x+7) * self.TILE_SIZE + self.TILE_SIZE/2, (y_start + 3) * self.TILE_SIZE, 80, (255, 255, 150, 80)))

        def draw_road_v(x_start):
            for y in range(max_ty):
                self.set_tile_by_index(x_start - 2, y, 4, layer="ground")
                self.set_tile_by_index(x_start - 1, y, 12, layer="ground")
                self.set_tile_by_index(x_start, y, 13 if y % 4 < 2 else 12, layer="ground")
                self.set_tile_by_index(x_start + 1, y, 12, layer="ground")
                self.set_tile_by_index(x_start + 2, y, 4, layer="ground")

                if y % 15 == 0 and y > 5 and y < max_ty - 5:
                    # Фонари вдоль вертикальной дороги (чтобы не перекрывали центр, ставим чуть в стороне)
                    if abs(y - hw_y) > 5:
                        self.set_tile_by_index(x_start - 3, y, 33, layer="ground")
                        self.lights.append(((x_start - 3) * self.TILE_SIZE + self.TILE_SIZE/2, y * self.TILE_SIZE, 80, (255, 255, 150, 80)))

        draw_road_h(hw_y)
        draw_road_v(hw_x)

        # Перекресток (заливаем асфальтом без разметки внутри креста)
        for y in range(hw_y - 1, hw_y + 2):
            for x in range(hw_x - 1, hw_x + 2):
                self.set_tile_by_index(x, y, 12, layer="ground")

        # === 2. РЕКА И МОСТ (Правый край) ===
        river_x = max_tx - 25
        for y in range(max_ty):
            for dx in range(8):
                self.set_tile_by_index(river_x + dx, y, 34, layer="ground") # Water

        # Мост через реку по главной дороге
        for y in range(hw_y - 2, hw_y + 3):
            for dx in range(8):
                self.set_tile_by_index(river_x + dx, y, 35, layer="ground") # Bridge

        # === 3. ДАУНТАУН (Левый верхний квадрат) ===
        city_hall = get_city_hall_prefab()
        ch_x = hw_x - city_hall.width - 6
        ch_y = hw_y - city_hall.height - 6
        apply_prefab(self, ch_x, ch_y, city_hall)
        self.city_hall_desk_pos = ((ch_x + 7.5) * self.TILE_SIZE, (ch_y + 3.5) * self.TILE_SIZE)

        # Тротуар к Мэрии
        for x in range(ch_x + 6, hw_x - 2):
            self.set_tile_by_index(x, ch_y + city_hall.height, 4, layer="ground")
            self.set_tile_by_index(x, ch_y + city_hall.height + 1, 4, layer="ground")

        self.building_doors["Мэрия"] = ((ch_x + 6) * self.TILE_SIZE, (ch_y + city_hall.height) * self.TILE_SIZE + self.TILE_SIZE)

        mayor_house = get_mayor_house_prefab()
        mh_x = 5
        mh_y = hw_y - mayor_house.height - 6
        apply_prefab(self, mh_x, mh_y, mayor_house)
        self.building_doors["Дом Мэра"] = ((mh_x + 4) * self.TILE_SIZE + self.TILE_SIZE/2, mh_y * self.TILE_SIZE - self.TILE_SIZE)

        # === 4. КОММЕРЦИЯ И ПАРК (Левый нижний квадрат) ===
        shop_prefab = get_supermarket_prefab()
        shop_x = hw_x - shop_prefab.width - 6
        shop_y = hw_y + 6
        apply_prefab(self, shop_x, shop_y, shop_prefab)

        shop_door_x = shop_x + 8
        shop_door_y = shop_y + shop_prefab.height - 1
        for y in range(hw_y + 3, shop_door_y):
            self.set_tile_by_index(shop_door_x, y, 4, layer="ground")
            self.set_tile_by_index(shop_door_x - 1, y, 4, layer="ground")
        self.building_doors["Супермаркет"] = (shop_door_x * self.TILE_SIZE, shop_door_y * self.TILE_SIZE + self.TILE_SIZE)
        self.shop_cashier_pos = ((shop_x + 4.5) * self.TILE_SIZE, (shop_y + 21.5) * self.TILE_SIZE)

        self.shop_queue_slots = []
        for dy in range(1, 6):
            self.shop_queue_slots.append(((shop_x + 5.5) * self.TILE_SIZE, (shop_y + 20.5 - dy) * self.TILE_SIZE))

        self.shop_departments["Крупы и бакалея"].append(((shop_x + 6.5) * self.TILE_SIZE, (shop_y + 6.5) * self.TILE_SIZE))
        self.shop_departments["Овощи"].append(((shop_x + 6.5) * self.TILE_SIZE, (shop_y + 14.5) * self.TILE_SIZE))
        self.shop_departments["Молочные продукты"].append(((shop_x + 9.5) * self.TILE_SIZE, (shop_y + 6.5) * self.TILE_SIZE))
        self.shop_departments["Фрукты"].append(((shop_x + 9.5) * self.TILE_SIZE, (shop_y + 14.5) * self.TILE_SIZE))
        self.shop_departments["Мясо и рыба"].append(((shop_x + 8.0) * self.TILE_SIZE, (shop_y + 4.0) * self.TILE_SIZE))
        self.shop_departments["Мясо и рыба"].append(((shop_x + 8.0) * self.TILE_SIZE, (shop_y + 17.0) * self.TILE_SIZE))

        # Городской парк (левее магазина)
        park_x = 5
        park_y = hw_y + 6
        park_w = 12
        park_h = 15

        self.park_benches = []
        for py in range(park_h):
            for px in range(park_w):
                tx = park_x + px
                ty = park_y + py

                # Травяная подложка
                self.set_tile_by_index(tx, ty, 0, layer="ground")

                # Деревья по краям
                if px == 0 or py == 0 or px == park_w - 1 or py == park_h - 1:
                    if random.random() > 0.3:
                        self.set_tile_by_index(tx, ty, 36, layer="ground")
                # Дорожка крестом
                elif px == park_w // 2 or py == park_h // 2:
                    self.set_tile_by_index(tx, ty, 37, layer="ground")
                # Скамейки
                elif (px == 2 and py == 2) or (px == park_w - 3 and py == park_h - 3):
                    self.set_tile_by_index(tx, ty, 11, layer="ground")
                    self.park_benches.append(((tx + 0.5) * self.TILE_SIZE, (ty + 0.5) * self.TILE_SIZE))

        # === 5. СПАЛЬНЫЙ РАЙОН (Правый верхний квадрат) ===
        apt_prefab = get_apartment_building_prefab()
        apt_y = hw_y - apt_prefab.height - 8

        apt1_x = hw_x + 6
        apply_prefab(self, apt1_x, apt_y, apt_prefab)
        a1_door_x = apt1_x + 6
        for y in range(apt_y + apt_prefab.height, hw_y - 2):
            self.set_tile_by_index(a1_door_x, y, 4, layer="ground")
            self.set_tile_by_index(a1_door_x - 1, y, 4, layer="ground")
        self.building_doors["Многоэтажка 1"] = (a1_door_x * self.TILE_SIZE, apt_y * self.TILE_SIZE - self.TILE_SIZE)

        apt2_x = hw_x + 6 + apt_prefab.width + 2
        apply_prefab(self, apt2_x, apt_y, apt_prefab)
        a2_door_x = apt2_x + 6
        for y in range(apt_y + apt_prefab.height, hw_y - 2):
            self.set_tile_by_index(a2_door_x, y, 4, layer="ground")
            self.set_tile_by_index(a2_door_x - 1, y, 4, layer="ground")
        self.building_doors["Многоэтажка 2"] = (a2_door_x * self.TILE_SIZE, apt_y * self.TILE_SIZE - self.TILE_SIZE)

        # Автобусная остановка в спальном районе
        bus_stop = get_bus_stop_prefab()
        bs_x = hw_x + 8
        bs_y = hw_y - 2 - bus_stop.height
        apply_prefab(self, bs_x, bs_y, bus_stop)

        self.update_dirty_chunks()

    def _render_layer(self, surface, camera, chunk_surfaces_dict, is_roof=False):
        visible_width = camera.width / camera.zoom
        visible_height = camera.height / camera.zoom

        center_world_x = camera.x + camera.width / 2
        center_world_y = camera.y + camera.height / 2

        start_world_x = center_world_x - visible_width / 2
        start_world_y = center_world_y - visible_height / 2

        chunk_pixel_size = self.CHUNK_SIZE * self.TILE_SIZE

        start_tile_x = int(start_world_x // self.TILE_SIZE)
        start_tile_y = int(start_world_y // self.TILE_SIZE)
        end_tile_x = int((start_world_x + visible_width) // self.TILE_SIZE) + 1
        end_tile_y = int((start_world_y + visible_height) // self.TILE_SIZE) + 1

        start_chunk_x = start_tile_x // self.CHUNK_SIZE
        start_chunk_y = start_tile_y // self.CHUNK_SIZE
        end_chunk_x = end_tile_x // self.CHUNK_SIZE
        end_chunk_y = end_tile_y // self.CHUNK_SIZE

        is_alpha = (chunk_surfaces_dict is self.chunk_surfaces_roof)

        surf_w = int((end_chunk_x - start_chunk_x + 1) * chunk_pixel_size)
        surf_h = int((end_chunk_y - start_chunk_y + 1) * chunk_pixel_size)

        if surf_w <= 0 or surf_h <= 0:
            return

        if is_alpha:
            if self._temp_surf_roof is None or self._temp_surf_roof.get_size() != (surf_w, surf_h):
                self._temp_surf_roof = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            temp_surface = self._temp_surf_roof
            temp_surface.fill((0,0,0,0))
        else:
            if self._temp_surf_ground is None or self._temp_surf_ground.get_size() != (surf_w, surf_h):
                self._temp_surf_ground = pygame.Surface((surf_w, surf_h))
            temp_surface = self._temp_surf_ground
            temp_surface.fill((0,0,0))

        base_x = start_chunk_x * chunk_pixel_size
        base_y = start_chunk_y * chunk_pixel_size

        for cy in range(start_chunk_y, end_chunk_y + 1):
            for cx in range(start_chunk_x, end_chunk_x + 1):
                self.get_chunk(cx, cy)

                chunk_surf = chunk_surfaces_dict.get((cx, cy))
                if chunk_surf:
                    px = cx * chunk_pixel_size - base_x
                    py = cy * chunk_pixel_size - base_y
                    temp_surface.blit(chunk_surf, (px, py))

        offset_x = start_world_x - base_x
        offset_y = start_world_y - base_y

        visible_rect = pygame.Rect(offset_x, offset_y, visible_width, visible_height)
        visible_rect = visible_rect.clip(temp_surface.get_rect())

        if visible_rect.width <= 0 or visible_rect.height <= 0:
            return

        sub_surface = temp_surface.subsurface(visible_rect)

        target_size = (int(visible_rect.width * camera.zoom) + 1, int(visible_rect.height * camera.zoom) + 1)
        scaled_surf = pygame.transform.scale(sub_surface, target_size)

        screen_x = (visible_rect.x - offset_x) * camera.zoom
        screen_y = (visible_rect.y - offset_y) * camera.zoom

        if is_roof:
            # 2.5D Фасады
            wall_surf = scaled_surf.copy()
            wall_surf.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)

            # Рисуем несколько слоев вниз для имитации 3D стены
            for i in reversed(range(1, 40, 2)):
                wall_y = screen_y - int(i * camera.zoom)
                surface.blit(wall_surf, (screen_x, wall_y))

            # Рисуем саму крышу сверху
            roof_y = screen_y - int(40 * camera.zoom)
            surface.blit(scaled_surf, (screen_x, roof_y))
        else:
            surface.blit(scaled_surf, (screen_x, screen_y))

    def render_ground(self, surface, camera):
        self._render_layer(surface, camera, self.chunk_surfaces_ground)

    def render_roof(self, surface, camera):
        self._render_layer(surface, camera, self.chunk_surfaces_roof, is_roof=True)
