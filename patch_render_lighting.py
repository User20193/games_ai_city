with open('src/states/play_state.py', 'r') as f:
    code = f.read()

code = code.replace("self.time_system.render_day_night_cycle(surface)", "self.time_system.render_day_night_cycle(surface, self.camera)")

with open('src/states/play_state.py', 'w') as f:
    f.write(code)
