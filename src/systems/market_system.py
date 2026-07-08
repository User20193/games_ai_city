import random

class MarketSystem:
    def __init__(self):
        # Базовая цена продуктовой корзины (оставлено для совместимости, но теперь мы используем отдельные продукты)
        self.base_basket_price = 100
        self.current_price = self.base_basket_price
        self.demand = 0.0

        # Каталог продуктов по отделам
        self.catalog = {
            "Крупы и бакалея": {
                "Мука": 10, "Сахар": 12, "Рис": 15, "Гречка": 15, "Макароны": 12, "Хлеб": 8
            },
            "Овощи": {
                "Картофель": 8, "Морковь": 6, "Лук": 5, "Чеснок": 7, "Капуста": 10, "Огурцы": 12, "Помидоры": 15
            },
            "Молочные продукты": {
                "Молоко": 15, "Яйца": 18, "Йогурт": 20, "Творог": 25, "Сыр": 35, "Масло сливочное": 30
            },
            "Фрукты": {
                "Бананы": 15, "Яблоки": 18, "Груши": 20, "Апельсины": 22, "Лимоны": 12, "Виноград": 40
            },
            "Мясо и рыба": {
                "Куриное филе": 45, "Свинина": 55, "Говядина": 70, "Рыба": 80, "Креветки": 90
            }
        }

        # Плоский список для удобного поиска цен
        self.flat_prices = {}
        for dept, items in self.catalog.items():
            for item, price in items.items():
                self.flat_prices[item] = price

    def update(self, dt):
        # Оставляем логику базовой инфляции для отображения общего индекса рынка
        if self.demand > 0:
            self.demand -= dt * 0.5
            if self.demand < 0:
                self.demand = 0

        demand_modifier = 1.0 + (self.demand / 100.0)
        target_price = self.base_basket_price * demand_modifier
        target_price += random.uniform(-2, 2)

        self.current_price += (target_price - self.current_price) * dt * 0.1
        if self.current_price < 50:
            self.current_price = 50

    def get_price(self):
        return int(self.current_price)

    def get_item_price(self, item_name):
        base_item_price = self.flat_prices.get(item_name, 10)
        # Применяем глобальный модификатор спроса на отдельные товары
        demand_modifier = 1.0 + (self.demand / 200.0) # Меньше влияет на дешевые товары
        return int(base_item_price * demand_modifier)

    def buy_goods(self):
        # Старая функция для совместимости
        price = self.get_price()
        self.demand += 15.0
        return price

    def buy_cart(self, shopping_cart):
        total_price = 0
        for item in shopping_cart:
            total_price += self.get_item_price(item)

        # Увеличиваем спрос в зависимости от размера корзины
        self.demand += 2.0 * len(shopping_cart)
        return total_price
