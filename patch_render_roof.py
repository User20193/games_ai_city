with open('src/world/world.py', 'r') as f:
    code = f.read()

old_func = """    def _render_layer(self, surface, camera, chunk_surfaces_dict):"""
new_func = """    def _render_layer(self, surface, camera, chunk_surfaces_dict, is_roof=False):"""

code = code.replace(old_func, new_func)

with open('src/world/world.py', 'w') as f:
    f.write(code)
