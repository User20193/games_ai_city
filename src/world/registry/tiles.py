class Tile:
    def __init__(self, id, name, color, is_solid=False, texture_name=None):
        self.id = id
        self.name = name
        self.color = color
        self.is_solid = is_solid
        self.texture_name = texture_name

class TileRegistry:
    def __init__(self):
        self.tiles = {}
        self._register_default_tiles()

    def register(self, tile):
        self.tiles[tile.id] = tile

    def get_tile(self, id):
        # Возвращаем Tile. Если ID нет или он None, возвращаем "Воздух"
        if id is None or id not in self.tiles:
            return Tile(-1, "Air", (0, 0, 0), is_solid=False)
        return self.tiles[id]

    def _register_default_tiles(self):
        # 0: Чистая трава (Светло-зеленый)
        self.register(Tile(0, "Grass", (124, 204, 31)))
        # 1-3 зарезервированы (ранее шум)

        # 4: Дорога/Тротуар (Светло-серый)
        self.register(Tile(4, "Sidewalk", (180, 180, 180)))

        # Здания (стены непроходимы)
        self.register(Tile(5, "Wall", (240, 230, 210), is_solid=True))
        # Крыша проходима для логики (она на другом слое)
        self.register(Tile(6, "Roof", (178, 34, 34), is_solid=True))

        # Двери, пол
        self.register(Tile(7, "Door", (139, 69, 19)))
        self.register(Tile(8, "WoodFloor", (205, 170, 125)))

        # Мебель (непроходимая)
        self.register(Tile(9, "Desk", (101, 67, 33), is_solid=True))
        self.register(Tile(10, "Bed", (65, 105, 225), is_solid=True))
        self.register(Tile(11, "Chair", (210, 105, 30), is_solid=True))
        self.register(Tile(12, "Asphalt", (60, 60, 65)))
        self.register(Tile(13, "AsphaltLine", (220, 220, 220)))
        self.register(Tile(14, "ShopFloor", (210, 210, 225)))
        self.register(Tile(15, "Shelf", (80, 150, 100), is_solid=True))
        self.register(Tile(16, "CashRegister", (50, 50, 60), is_solid=True))

        # Meat Shelf (17-20)
        self.register(Tile(17, "MeatShelf_TopLeft", (200, 200, 220), is_solid=True, texture_name="MeatShelf_TopLeft"))
        self.register(Tile(18, "MeatShelf_TopRight", (200, 200, 220), is_solid=True, texture_name="MeatShelf_TopRight"))
        self.register(Tile(19, "MeatShelf_BotLeft", (200, 200, 220), is_solid=True, texture_name="MeatShelf_BotLeft"))
        self.register(Tile(20, "MeatShelf_BotRight", (200, 200, 220), is_solid=True, texture_name="MeatShelf_BotRight"))

        # Fruit Shelf (21-24)
        self.register(Tile(21, "FruitShelf_TopLeft", (50, 120, 50), is_solid=True, texture_name="FruitShelf_TopLeft"))
        self.register(Tile(22, "FruitShelf_TopRight", (50, 120, 50), is_solid=True, texture_name="FruitShelf_TopRight"))
        self.register(Tile(23, "FruitShelf_BotLeft", (50, 120, 50), is_solid=True, texture_name="FruitShelf_BotLeft"))
        self.register(Tile(24, "FruitShelf_BotRight", (50, 120, 50), is_solid=True, texture_name="FruitShelf_BotRight"))

        # Dairy Shelf (25-28)
        self.register(Tile(25, "DairyShelf_TopLeft", (240, 240, 255), is_solid=True, texture_name="DairyShelf_TopLeft"))
        self.register(Tile(26, "DairyShelf_TopRight", (240, 240, 255), is_solid=True, texture_name="DairyShelf_TopRight"))
        self.register(Tile(27, "DairyShelf_BotLeft", (240, 240, 255), is_solid=True, texture_name="DairyShelf_BotLeft"))
        self.register(Tile(28, "DairyShelf_BotRight", (240, 240, 255), is_solid=True, texture_name="DairyShelf_BotRight"))

        # Grocery Shelf (29-32)
        self.register(Tile(29, "GroceryShelf_TopLeft", (139, 69, 19), is_solid=True, texture_name="GroceryShelf_TopLeft"))
        self.register(Tile(30, "GroceryShelf_TopRight", (139, 69, 19), is_solid=True, texture_name="GroceryShelf_TopRight"))
        self.register(Tile(31, "GroceryShelf_BotLeft", (139, 69, 19), is_solid=True, texture_name="GroceryShelf_BotLeft"))
        self.register(Tile(32, "GroceryShelf_BotRight", (139, 69, 19), is_solid=True, texture_name="GroceryShelf_BotRight"))
