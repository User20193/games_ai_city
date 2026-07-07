import math
import heapq

def astar_search(world, start_world_pos, target_world_pos):
    """
    Алгоритм A* для поиска пути по тайловой сетке.
    Возвращает список мировых координат (x, y) - точек маршрута.
    Если путь не найден, возвращает пустой список.
    """
    tile_size = world.TILE_SIZE

    # Переводим мировые координаты в тайловые
    start_tx = int(start_world_pos[0] // tile_size)
    start_ty = int(start_world_pos[1] // tile_size)
    target_tx = int(target_world_pos[0] // tile_size)
    target_ty = int(target_world_pos[1] // tile_size)

    start_node = (start_tx, start_ty)
    target_node = (target_tx, target_ty)

    # Если мы уже стоим на нужной клетке
    if start_node == target_node:
        return [target_world_pos]

    def heuristic(node_a, node_b):
        # Манхэттенское расстояние
        return abs(node_a[0] - node_b[0]) + abs(node_a[1] - node_b[1])

    def is_walkable(tx, ty):
        # Проверяем, не выходит ли за границы карты
        if tx < 0 or ty < 0 or tx >= world.WORLD_WIDTH * world.CHUNK_SIZE or ty >= world.WORLD_HEIGHT * world.CHUNK_SIZE:
            return False

        tile_idx = world.get_tile_index(tx * tile_size, ty * tile_size)
        if tile_idx is not None:
            tile = world.tile_registry.get_tile(tile_idx)
            if tile and tile.is_solid:
                return False
        return True

    # Очередь с приоритетом для открытых узлов: (f_score, node)
    open_set = []
    heapq.heappush(open_set, (0, start_node))

    # Словари для хранения путей и стоимости
    came_from = {}
    g_score = {start_node: 0}

    # Ограничение по итерациям, чтобы игра не зависла при поиске слишком сложного пути
    max_iterations = 1000
    iterations = 0

    while open_set and iterations < max_iterations:
        iterations += 1
        _, current = heapq.heappop(open_set)

        if current == target_node:
            # Путь найден, восстанавливаем его
            path = []
            while current in came_from:
                # Добавляем центр тайла как мировую координату
                world_x = current[0] * tile_size + tile_size / 2
                world_y = current[1] * tile_size + tile_size / 2
                path.append((world_x, world_y))
                current = came_from[current]
            path.reverse()
            # Последняя точка должна быть точной (координаты двери, а не просто центр тайла)
            path[-1] = target_world_pos
            return path

        cx, cy = current
        # Соседи (вверх, вниз, влево, вправо)
        neighbors = [(cx, cy-1), (cx, cy+1), (cx-1, cy), (cx+1, cy)]

        for neighbor in neighbors:
            if not is_walkable(neighbor[0], neighbor[1]):
                continue

            tentative_g_score = g_score[current] + 1

            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score = tentative_g_score + heuristic(neighbor, target_node)
                heapq.heappush(open_set, (f_score, neighbor))

    # Путь не найден
    return []
