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
        for cy in range(self.WORLD_HEIGHT):
            for cx in range(self.WORLD_WIDTH):
                self.get_chunk(cx, cy)

        center_tx = (self.WORLD_WIDTH * self.CHUNK_SIZE) // 2
        center_ty = (self.WORLD_HEIGHT * self.CHUNK_SIZE) // 2

        max_tx = self.WORLD_WIDTH * self.CHUNK_SIZE

        # === 1. ГЛАВНОЕ ШОССЕ ===
        highway_y = center_ty
        for x in range(max_tx):
            self.set_tile_by_index(x, highway_y - 2, 4, layer="ground")
            self.set_tile_by_index(x, highway_y - 1, 12, layer="ground")
            if x % 4 < 2:
                self.set_tile_by_index(x, highway_y, 13, layer="ground")
            else:
                self.set_tile_by_index(x, highway_y, 12, layer="ground")
            self.set_tile_by_index(x, highway_y + 1, 12, layer="ground")
            self.set_tile_by_index(x, highway_y + 2, 4, layer="ground")

            # Фонари
            if x % 15 == 0 and x > 10 and x < max_tx - 10:
                self.set_tile_by_index(x, highway_y - 3, 33, layer="ground") # Фонарь сверху дороги
                self.lights.append((x * self.TILE_SIZE + self.TILE_SIZE/2, (highway_y - 3) * self.TILE_SIZE, 80, (255, 255, 100, 60)))
                self.set_tile_by_index(x+7, highway_y + 3, 33, layer="ground") # Фонарь снизу дороги со смещением
                self.lights.append(((x+7) * self.TILE_SIZE + self.TILE_SIZE/2, (highway_y + 3) * self.TILE_SIZE, 80, (255, 255, 100, 60)))

        # === 2. МЭРИЯ ===
        city_hall = get_city_hall_prefab()
        ch_x = center_tx - city_hall.width // 2
        ch_y = highway_y - 2 - city_hall.height - 4
        apply_prefab(self, ch_x, ch_y, city_hall)

        self.city_hall_desk_pos = ((ch_x + 7.5) * self.TILE_SIZE, (ch_y + 3.5) * self.TILE_SIZE)

        for y in range(ch_y + city_hall.height, highway_y - 2):
            self.set_tile_by_index(center_tx, y, 4, layer="ground")
            self.set_tile_by_index(center_tx - 1, y, 4, layer="ground")

        # === 3. ДОМ МЭРА ===
        mayor_house = get_mayor_house_prefab()
        mh_x = center_tx + city_hall.width + 10
        mh_y = highway_y + 3 + 4
        apply_prefab(self, mh_x, mh_y, mayor_house)

        mh_door_x = mh_x + 4
        for y in range(highway_y + 3, mh_y):
            self.set_tile_by_index(mh_door_x, y, 4, layer="ground")

        self.building_doors["Дом Мэра"] = (mh_door_x * self.TILE_SIZE + self.TILE_SIZE/2, mh_y * self.TILE_SIZE - self.TILE_SIZE)

        # === 4. МНОГОЭТАЖКИ ===
        apt_prefab = get_apartment_building_prefab()
        apt_y = highway_y + 3 + 4

        # Квартира 1
        apt1_x = ch_x - 10
        apply_prefab(self, apt1_x, apt_y, apt_prefab)
        a1_door_x = apt1_x + 6
        for y in range(highway_y + 3, apt_y):
            self.set_tile_by_index(a1_door_x, y, 4, layer="ground")
            self.set_tile_by_index(a1_door_x - 1, y, 4, layer="ground")

        self.building_doors["Многоэтажка 1"] = (a1_door_x * self.TILE_SIZE, apt_y * self.TILE_SIZE - self.TILE_SIZE)

        # Квартира 2
        apt2_x = ch_x + 6
        apply_prefab(self, apt2_x, apt_y, apt_prefab)
        a2_door_x = apt2_x + 6
        for y in range(highway_y + 3, apt_y):
            self.set_tile_by_index(a2_door_x, y, 4, layer="ground")
            self.set_tile_by_index(a2_door_x - 1, y, 4, layer="ground")

        self.building_doors["Многоэтажка 2"] = (a2_door_x * self.TILE_SIZE, apt_y * self.TILE_SIZE - self.TILE_SIZE)

        # === 5. СУПЕРМАРКЕТ ===
        shop_prefab = get_supermarket_prefab()
        shop_x = ch_x - shop_prefab.width - 10
        shop_y = highway_y - 2 - shop_prefab.height - 4
        apply_prefab(self, shop_x, shop_y, shop_prefab)

        # Дверь в префабе уже на южной стене (x=8, y=23)
        shop_door_x = shop_x + 8
        shop_door_y = shop_y + 23

        # Дорожка к двери
        for y in range(shop_door_y + 1, highway_y - 2):
            self.set_tile_by_index(shop_door_x, y, 4, layer="ground")
            self.set_tile_by_index(shop_door_x - 1, y, 4, layer="ground")

        self.building_doors["Супермаркет"] = (shop_door_x * self.TILE_SIZE, shop_door_y * self.TILE_SIZE + self.TILE_SIZE)

        # Точки интереса: касса (x=3, y=20)
        # Место кассира: y=21
        self.shop_cashier_pos = ((shop_x + 4.5) * self.TILE_SIZE, (shop_y + 21.5) * self.TILE_SIZE)

        # Слоты для очереди перед кассой (выстраиваются вверх от кассы, так как дверь снизу)
        # Касса на y=20, очередь идет: y=19, 18, 17, 16...
        self.shop_queue_slots = []
        for dy in range(1, 6): # 5 мест в очереди
            self.shop_queue_slots.append(((shop_x + 5.5) * self.TILE_SIZE, (shop_y + 20.5 - dy) * self.TILE_SIZE))

        # Точки интереса: отделы
        # Левые полки (x=2..4, y=3..18). Место для покупателя: справа (x=6)
        self.shop_departments["Крупы и бакалея"].append(((shop_x + 6.5) * self.TILE_SIZE, (shop_y + 6.5) * self.TILE_SIZE))
        self.shop_departments["Овощи"].append(((shop_x + 6.5) * self.TILE_SIZE, (shop_y + 14.5) * self.TILE_SIZE))

        # Правые полки (x=11..13, y=3..18). Покупатель: слева (x=9)
        self.shop_departments["Молочные продукты"].append(((shop_x + 9.5) * self.TILE_SIZE, (shop_y + 6.5) * self.TILE_SIZE))
        self.shop_departments["Фрукты"].append(((shop_x + 9.5) * self.TILE_SIZE, (shop_y + 14.5) * self.TILE_SIZE))

        # Центральные островки
        self.shop_departments["Мясо и рыба"].append(((shop_x + 8.0) * self.TILE_SIZE, (shop_y + 4.0) * self.TILE_SIZE))
        self.shop_departments["Мясо и рыба"].append(((shop_x + 8.0) * self.TILE_SIZE, (shop_y + 17.0) * self.TILE_SIZE))


        # === 6. АВТОБУСНАЯ ОСТАНОВКА ===
        bus_stop = get_bus_stop_prefab()
        bs_x = center_tx + 3
        bs_y = highway_y - 2 - bus_stop.height
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
