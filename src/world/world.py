import pygame
import random
from src.world.registry.tiles import TileRegistry
from src.world.generation.prefabs import get_city_hall_prefab, get_mayor_house_prefab, get_apartment_building_prefab, apply_prefab
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

        # === 1. ГЛАВНОЕ ШОССЕ (Идет через весь мир по оси X) ===
        highway_y = center_ty

        for x in range(max_tx):
            self.set_tile_by_index(x, highway_y - 2, 4, layer="ground") # Верхний тротуар
            self.set_tile_by_index(x, highway_y - 1, 12, layer="ground") # Асфальт (верхняя полоса)

            # Разметка по центру (пунктир)
            if x % 4 < 2:
                self.set_tile_by_index(x, highway_y, 13, layer="ground") # Белая полоса
            else:
                self.set_tile_by_index(x, highway_y, 12, layer="ground") # Асфальт

            self.set_tile_by_index(x, highway_y + 1, 12, layer="ground") # Асфальт (нижняя полоса)
            self.set_tile_by_index(x, highway_y + 2, 4, layer="ground") # Нижний тротуар


        # === 2. МЭРИЯ (Отодвигаем вверх от дороги) ===
        city_hall = get_city_hall_prefab()
        ch_x = center_tx - city_hall.width // 2
        ch_y = highway_y - 2 - city_hall.height - 4 # Отступ 4 тайла от верхнего тротуара
        apply_prefab(self, ch_x, ch_y, city_hall)

        # Дорожка к дверям Мэрии (спускается к верхнему тротуару)
        door_x = center_tx
        door_y = ch_y + city_hall.height - 1

        for y in range(ch_y + city_hall.height, highway_y - 2):
            self.set_tile_by_index(center_tx, y, 4, layer="ground")
            self.set_tile_by_index(center_tx - 1, y, 4, layer="ground")


        # === 3. ДОМ МЭРА (Справа внизу от дороги) ===
        mayor_house = get_mayor_house_prefab()
        mh_x = center_tx + city_hall.width + 10
        mh_y = highway_y + 3 + 4 # Отступ 4 тайла от нижнего тротуара
        apply_prefab(self, mh_x, mh_y, mayor_house)

        # Дорожка к дому мэра (поднимается к нижнему тротуару)
        mh_door_x = mh_x + 4
        for y in range(highway_y + 3, mh_y):
            self.set_tile_by_index(mh_door_x, y, 4, layer="ground")


        # === 4. МНОГОЭТАЖКИ (Слева внизу от дороги) ===
        apt_prefab = get_apartment_building_prefab()
        apt_y = highway_y + 3 + 4 # На одном уровне с домом мэра

        # Квартира 1
        apt1_x = ch_x - 10
        apply_prefab(self, apt1_x, apt_y, apt_prefab)

        # Дорожка к Квартире 1
        a1_door_x = apt1_x + 6
        for y in range(highway_y + 3, apt_y):
            self.set_tile_by_index(a1_door_x, y, 4, layer="ground")
            self.set_tile_by_index(a1_door_x - 1, y, 4, layer="ground")

        # Квартира 2
        apt2_x = ch_x + 6
        apply_prefab(self, apt2_x, apt_y, apt_prefab)

        # Дорожка к Квартире 2
        a2_door_x = apt2_x + 6
        for y in range(highway_y + 3, apt_y):
            self.set_tile_by_index(a2_door_x, y, 4, layer="ground")
            self.set_tile_by_index(a2_door_x - 1, y, 4, layer="ground")

        self.update_dirty_chunks()

    def _render_layer(self, surface, camera, chunk_surfaces_dict):
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

        surface.blit(scaled_surf, (screen_x, screen_y))

    def render_ground(self, surface, camera):
        self._render_layer(surface, camera, self.chunk_surfaces_ground)

    def render_roof(self, surface, camera):
        self._render_layer(surface, camera, self.chunk_surfaces_roof)
