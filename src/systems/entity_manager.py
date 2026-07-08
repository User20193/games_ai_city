class EntityManager:
    def __init__(self):
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def update(self, dt):
        for entity in self.entities:
            entity.update(dt)

    def render(self, surface, camera):
        # Y-сортировка: первыми рисуются сущности, которые выше (y меньше)
        # Таким образом те, кто ниже, будут перекрывать тех, кто выше, создавая иллюзию глубины (2.5D)
        self.entities.sort(key=lambda e: e.y + e.height)

        # Сначала рисуем тела всех сущностей
        for entity in self.entities:
            entity.render(surface, camera)

        # Затем вторым проходом рисуем UI (мысли), чтобы они всегда были поверх всех голов
        for entity in self.entities:
            if hasattr(entity, 'render_ui'):
                entity.render_ui(surface, camera)
