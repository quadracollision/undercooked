import pygame
import json
import os
import tkinter as tk
from tkinter import filedialog

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 40
DATA_FILE = "gamedata.json"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
BLUE = (50, 50, 200)
POPUP_BG = (50, 50, 50)
POPUP_BORDER = (255, 255, 255)

OBJECT_TYPES = [
    {"name": "Counter", "color": (139, 69, 19), "type_id": "counter", "layer": 0},

    {"name": "Processor", "color": (50, 50, 50), "type_id": "processor", "layer": 0},
    {"name": "Sink", "color": (50, 150, 255), "type_id": "sink", "layer": 0},
    {"name": "Serving", "color": (100, 100, 100), "type_id": "serving_counter", "layer": 0},
    {"name": "Crate", "color": (150, 150, 100), "type_id": "crate", "layer": 0}, 
    {"name": "Plate", "color": (255, 255, 255), "type_id": "plate", "layer": 1},
    {"name": "Container", "color": (80, 80, 80), "type_id": "container", "layer": 1},
    {"name": "Spawn", "color": (0, 255, 0), "type_id": "spawn_point", "layer": 1}, 
]

def load_ingredient_list():
    if not os.path.exists(DATA_FILE): return ["onion", "tomato"]
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return list(data.get("ingredients", {}).keys())
    except: return ["onion", "tomato"]

def load_container_list():
    if not os.path.exists(DATA_FILE): return ["pot", "pan"]
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return list(data.get("containers", {}).keys())
    except: return ["pot", "pan"]

def load_processor_list():
    if not os.path.exists(DATA_FILE): return ["stove"]
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return list(data.get("processors", {}).keys())
    except: return ["stove"]

class MapEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Level Editor - [S]ave As | [L]oad")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.large_font = pygame.font.SysFont("Arial", 24)
        
        self.current_idx = 0
        self.furniture_layer = {} 
        self.item_layer = {}      
        self.available_ingredients = load_ingredient_list()
        self.container_types = load_container_list()
        self.processor_types = load_processor_list()

        self.show_popup = False
        self.popup_target_pos = None 
        self.popup_rect = pygame.Rect(200, 100, 400, 400)
        self.option_rects = []
        self.current_popup_items = []
        
        # Current file being edited (for display purposes)
        self.current_file = "Untitled"

    def save_map(self):
        # Open File Dialog
        root = tk.Tk()
        root.withdraw() # Hide the main window
        file_path = filedialog.asksaveasfilename(
            initialdir="levels",
            title="Save Level As",
            filetypes=[("JSON Files", "*.json")],
            defaultextension=".json"
        )
        root.destroy()

        if not file_path:
            return # User cancelled

        # 1. Load existing data to preserve recipes if overwriting
        existing_data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
            except: pass
        
        # 2. Build Objects List
        export_list = []
        for loc, obj in self.furniture_layer.items():
            item = { "type": obj["type_id"], "x": loc[0], "y": loc[1] }
            if "args" in obj: item["args"] = obj["args"]
            export_list.append(item)
        for loc, obj in self.item_layer.items():
            item = { "type": obj["type_id"], "x": loc[0], "y": loc[1] }
            export_list.append(item)
            
        # 3. Update structure
        if isinstance(existing_data, list): 
            # Convert legacy list to dict
            existing_data = {"objects": export_list}
        else: 
            existing_data["objects"] = export_list
            
        # 4. Save
        with open(file_path, 'w') as f:
            json.dump(existing_data, f, indent=4)
            
        print(f"Map saved to {file_path}")
        self.current_file = os.path.basename(file_path)
        pygame.display.set_caption(f"Level Editor - {self.current_file}")

    def load_map(self):
        # Open File Dialog
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            initialdir="levels",
            title="Load Level",
            filetypes=[("JSON Files", "*.json")]
        )
        root.destroy()

        if not file_path: return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle formats
            obj_list = data if isinstance(data, list) else data.get("objects", [])
            
            self.furniture_layer = {}
            self.item_layer = {}
            
            for item in obj_list:
                x, y = item["x"], item["y"]
                base_obj = None
                for ref in OBJECT_TYPES:
                    if ref["type_id"] == item["type"]:
                        base_obj = ref.copy()
                        break
                if base_obj:
                    if "args" in item: base_obj["args"] = item["args"]
                    if base_obj.get("layer", 0) == 0: self.furniture_layer[(x, y)] = base_obj
                    else: self.item_layer[(x, y)] = base_obj
            
            print(f"Map loaded from {file_path}")
            self.current_file = os.path.basename(file_path)
            pygame.display.set_caption(f"Level Editor - {self.current_file}")
            
        except Exception as e:
            print(f"Error loading map: {e}")

    def run(self):
        while True:
            if self.show_popup:
                # Popup Logic
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: return 
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.show_popup = False 
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = pygame.mouse.get_pos()
                        for i, rect in enumerate(self.option_rects):
                            if rect.collidepoint(mx, my):
                                choice = self.current_popup_items[i] 
                                template = OBJECT_TYPES[self.current_idx] 
                                new_obj = template.copy()
                                
                                if template["type_id"] == "crate":
                                    new_obj["args"] = choice
                                    self.furniture_layer[self.popup_target_pos] = new_obj
                                elif template["type_id"] == "processor":
                                    new_obj["args"] = choice
                                    self.furniture_layer[self.popup_target_pos] = new_obj
                                elif template["type_id"] == "container":
                                    new_obj["type_id"] = choice # Switch generic to specific
                                    # Update color based on selection for immediate feedback if we had that mapping
                                    if choice == "pan": new_obj["color"] = (20, 20, 20)
                                    else: new_obj["color"] = (80, 80, 80)
                                    self.item_layer[self.popup_target_pos] = new_obj

                                self.show_popup = False
                                break
                        if not self.popup_rect.collidepoint(mx, my): self.show_popup = False
            else:
                # Editor Logic
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: return 
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s: self.save_map()
                        if event.key == pygame.K_l: self.load_map()
                        if event.key == pygame.K_ESCAPE: return 
                        
                        if event.key >= pygame.K_0 and event.key <= pygame.K_9:
                            if event.key == pygame.K_0: idx = 9
                            else: idx = event.key - pygame.K_1
                            if idx < len(OBJECT_TYPES): self.current_idx = idx

                    mouse_buttons = pygame.mouse.get_pressed()
                    if mouse_buttons[0] or mouse_buttons[2]:
                        mx, my = pygame.mouse.get_pos()
                        grid_x = (mx // GRID_SIZE) * GRID_SIZE
                        grid_y = (my // GRID_SIZE) * GRID_SIZE
                        
                        if mouse_buttons[0]: 
                            template = OBJECT_TYPES[self.current_idx]
                            layer = template.get("layer", 0)
                            if layer == 0:
                                if template["type_id"] == "crate":
                                    existing = self.furniture_layer.get((grid_x, grid_y))
                                    if not existing or existing["type_id"] != "crate":
                                        self.show_popup = True
                                        self.popup_target_pos = (grid_x, grid_y)
                                        self.current_popup_items = self.available_ingredients
                                elif template["type_id"] == "processor":
                                    existing = self.furniture_layer.get((grid_x, grid_y))
                                    if not existing or existing["type_id"] != "processor":
                                        self.show_popup = True
                                        self.popup_target_pos = (grid_x, grid_y)
                                        self.current_popup_items = self.processor_types
                                else:
                                    self.furniture_layer[(grid_x, grid_y)] = template.copy()
                            elif layer == 1:
                                if template["type_id"] == "container":
                                    self.show_popup = True
                                    self.popup_target_pos = (grid_x, grid_y)
                                    self.current_popup_items = self.container_types
                                else:
                                    self.item_layer[(grid_x, grid_y)] = template.copy()

                        elif mouse_buttons[2]: 
                            if (grid_x, grid_y) in self.item_layer: del self.item_layer[(grid_x, grid_y)]
                            elif (grid_x, grid_y) in self.furniture_layer: del self.furniture_layer[(grid_x, grid_y)]

            self.draw()
            self.clock.tick(60)

    def draw(self):
        self.screen.fill(GREY)
        for x in range(0, SCREEN_WIDTH, GRID_SIZE): pygame.draw.line(self.screen, WHITE, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE): pygame.draw.line(self.screen, WHITE, (0, y), (SCREEN_WIDTH, y))

        for loc, obj in self.furniture_layer.items():
            rect = pygame.Rect(loc[0], loc[1], GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, obj["color"], rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
            if "args" in obj:
                text = self.font.render(obj["args"][:3].upper(), True, BLACK)
                self.screen.blit(text, (loc[0]+5, loc[1]+10))

        for loc, obj in self.item_layer.items():
            rect = pygame.Rect(loc[0] + 5, loc[1] + 5, GRID_SIZE - 10, GRID_SIZE - 10)
            if obj["type_id"] == "spawn_point":
                pygame.draw.rect(self.screen, obj["color"], rect, 4)
                text = self.font.render("P", True, obj["color"])
                self.screen.blit(text, (rect.centerx - 5, rect.centery - 10))
            else:
                pygame.draw.rect(self.screen, obj["color"], rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)

        current_obj = OBJECT_TYPES[self.current_idx]
        ui_text = f"Tool: {current_obj['name']} | [S]ave [L]oad | [ESC] Exit"
        pygame.draw.rect(self.screen, BLACK, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
        text_surf = self.font.render(ui_text, True, WHITE)
        self.screen.blit(text_surf, (10, SCREEN_HEIGHT - 25))
        
        if not self.show_popup:
            mx, my = pygame.mouse.get_pos()
            snap_x = (mx // GRID_SIZE) * GRID_SIZE
            snap_y = (my // GRID_SIZE) * GRID_SIZE
            pygame.draw.rect(self.screen, current_obj["color"], (snap_x, snap_y, GRID_SIZE, GRID_SIZE), 3)

        if self.show_popup: self.draw_popup()
        pygame.display.flip()

    def draw_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); overlay.set_alpha(128); overlay.fill((0,0,0)); self.screen.blit(overlay, (0,0))
        pygame.draw.rect(self.screen, POPUP_BG, self.popup_rect); pygame.draw.rect(self.screen, POPUP_BORDER, self.popup_rect, 3)
        title = self.large_font.render("Select Option", True, WHITE); self.screen.blit(title, (self.popup_rect.x + 20, self.popup_rect.y + 20))
        self.option_rects = []; start_y = self.popup_rect.y + 70
        for i, item in enumerate(self.current_popup_items):
            item_rect = pygame.Rect(self.popup_rect.x + 20, start_y + (i * 40), 360, 30); self.option_rects.append(item_rect)
            mx, my = pygame.mouse.get_pos(); color = BLUE if item_rect.collidepoint(mx, my) else (80, 80, 80)
            pygame.draw.rect(self.screen, color, item_rect); pygame.draw.rect(self.screen, WHITE, item_rect, 1)
            text = self.font.render(item.capitalize(), True, WHITE); self.screen.blit(text, (item_rect.x + 10, item_rect.y + 5))

if __name__ == "__main__":
    editor = MapEditor()
    editor.run()
