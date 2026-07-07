import random

class MarketSystem:
    def __init__(self):
        # Базовая цена продуктовой корзины
        self.base_basket_price = 100
        # Динамическая цена (зависит от спроса)
        self.current_price = self.base_basket_price

        # Индикатор спроса (падает каждый тик, растет при покупке)
        self.demand = 0.0

    def update(self, dt):
        # Спрос медленно падает
        if self.demand > 0:
            self.demand -= dt * 0.5
            if self.demand < 0:
                self.demand = 0

        # Обновляем текущую цену на основе спроса
        # Например: каждые 10 единиц спроса увеличивают цену на 10%
        demand_modifier = 1.0 + (self.demand / 100.0)

        # Плавно двигаем цену
        target_price = self.base_basket_price * demand_modifier
        # Чуть-чуть рандома для эффекта "живого рынка"
        target_price += random.uniform(-2, 2)

        self.current_price += (target_price - self.current_price) * dt * 0.1

        # Защита от отрицательных цен
        if self.current_price < 50:
            self.current_price = 50

    def get_price(self):
        return int(self.current_price)

    def buy_goods(self):
        """Вызывается, когда кто-то совершает покупку. Возвращает цену и поднимает спрос."""
        price = self.get_price()
        self.demand += 15.0 # Спрос резко скачет вверх
        return price
