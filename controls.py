import pygame
import json
import os

CONTROLS_FILE = "controls.json"

DEFAULT_CONTROLS = {
    "move_left": [pygame.K_LEFT, pygame.K_a],
    "move_right": [pygame.K_RIGHT, pygame.K_d],
    "move_up": [pygame.K_UP, pygame.K_w],
    "move_down": [pygame.K_DOWN, pygame.K_s],
    "interact": [pygame.K_SPACE],
    "chop": [pygame.K_e],
    "throw": [pygame.K_f],
    "pause": [pygame.K_ESCAPE, pygame.K_x]
}

class Controls:
    def __init__(self):
        self.actions = DEFAULT_CONTROLS.copy()
        self.load()

    def load(self):
        if os.path.exists(CONTROLS_FILE):
            try:
                with open(CONTROLS_FILE, 'r') as f:
                    data = json.load(f)
                    # Merge loaded data with defaults to ensure all keys exist
                    for key, val in data.items():
                        if key in self.actions:
                            self.actions[key] = val
            except Exception as e:
                print(f"Error loading controls: {e}")

    def save(self):
        try:
            with open(CONTROLS_FILE, 'w') as f:
                json.dump(self.actions, f, indent=4)
        except Exception as e:
            print(f"Error saving controls: {e}")

    def is_active(self, action, pressed_keys):
        """Returns True if any key bound to 'action' is in 'pressed_keys'."""
        if action not in self.actions:
            return False
            
        for key_code in self.actions[action]:
            if pressed_keys[key_code]:
                return True
        return False

    def get_keys(self, action):
        return self.actions.get(action, [])

    def set_key(self, action, key_code, index=0):
        """Sets the key at 'index' for 'action'."""
        if action in self.actions:
            if index < len(self.actions[action]):
                self.actions[action][index] = key_code
            else:
                # If we are setting a key input that doesn't exist (e.g. secondary when only primary exists)
                # Just append it
                self.actions[action].append(key_code)
            self.save()

    def reset_to_defaults(self):
        self.actions = DEFAULT_CONTROLS.copy()
        self.save()

# Global instance
manager = Controls()
