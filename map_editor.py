import pygame
import json
import os
import tkinter as tk
from tkinter import simpledialog

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 40
OUTPUT_FILE = "level1.json"
DATA_FILE = "gamedata.json"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
BLUE = (50, 50, 200)
POPUP_BG = (50, 50, 50)
POPUP_BORDER = (255, 255, 255)

# --- Object Definitions ---
OBJECT_TYPES = [
    {"name": "Counter", "color": (139, 69, 19), "type_id": "counter", "layer": 0},
    {"name": "CutBoard", "color": (240, 240, 240), "type_id": "cutting_board", "layer": 0},
    {"name": "Stove", "color": (50, 50, 50), "type_id": "stove", "layer": 0},
    {"name": "Crate", "color": (150, 150, 100), "type_id": "crate", "layer": 0}, 
    {"name": "Plate", "color": (255, 255, 255), "type_id": "plate", "layer": 1},
    {"name": "Pot", "color": (80, 80, 80), "type_id": "pot", "layer": 1},
    {"name": "Pan", "color": (20, 20, 20), "type_id": "pan", "layer": 1},
    # --- NEW: PLAYER SPAWN ---
    {"name": "Spawn", "color": (0, 255, 0), "type_id": "spawn_point", "layer": 1}, 
]

def load_ingredient_list():
    if not os.path.exists(DATA_FILE):
        return ["onion", "tomato"]
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return list(data.get("ingredients", {}).keys())
    except:
        return ["onion", "tomato"]

class MapEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Level Editor - Layered")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.large_font = pygame.font.SysFont("Arial", 24)
        
        self.current_idx = 0
        
        self.furniture_layer = {} # Layer 0
        self.item_layer = {}      # Layer 1
        
        self.running = True
        self.available_ingredients = load_ingredient_list()

        # Popup State
        self.show_popup = False
        self.popup_target_pos = None 
        self.popup_rect = pygame.Rect(200, 100, 400, 400)
        self.option_rects = [] 

    def save_map(self):
        export_list = []
        
        # 1. Save Furniture
        for loc, obj in self.furniture_layer.items():
            item = { "type": obj["type_id"], "x": loc[0], "y": loc[1] }
            if "args" in obj: item["args"] = obj["args"]
            export_list.append(item)
            
        # 2. Save Items (Includes Spawn Point now)
        for loc, obj in self.item_layer.items():
            item = { "type": obj["type_id"], "x": loc[0], "y": loc[1] }
            export_list.append(item)
            
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(export_list, f, indent=4)
        print(f"Map saved to {OUTPUT_FILE}")

    def load_map(self):
        if not os.path.exists(OUTPUT_FILE):
            return

        with open(OUTPUT_FILE, 'r') as f:
            data = json.load(f)
            
        self.furniture_layer = {}
        self.item_layer = {}
        
        for item in data:
            x, y = item["x"], item["y"]
            
            base_obj = None
            for ref in OBJECT_TYPES:
                if ref["type_id"] == item["type"]:
                    base_obj = ref.copy()
                    break
            
            if base_obj:
                if "args" in item:
                    base_obj["args"] = item["args"]
                
                if base_obj.get("layer", 0) == 0:
                    self.furniture_layer[(x, y)] = base_obj
                else:
                    self.item_layer[(x, y)] = base_obj
                    
        print(f"Map loaded from {OUTPUT_FILE}")

    def run(self):
        while self.running:
            if self.show_popup:
                self.handle_popup_events()
            else:
                self.handle_editor_events()
            self.draw()
            self.clock.tick(60)

    def handle_editor_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s: self.save_map()
                if event.key == pygame.K_l: self.load_map()
                
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(OBJECT_TYPES):
                        self.current_idx = idx

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
                        else:
                            self.furniture_layer[(grid_x, grid_y)] = template.copy()
                            
                    elif layer == 1:
                        self.item_layer[(grid_x, grid_y)] = template.copy()

                elif mouse_buttons[2]: 
                    if (grid_x, grid_y) in self.item_layer:
                        del self.item_layer[(grid_x, grid_y)]
                    elif (grid_x, grid_y) in self.furniture_layer:
                        del self.furniture_layer[(grid_x, grid_y)]

    def handle_popup_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_popup = False 
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mx, my):
                        choice = self.available_ingredients[i]
                        template = OBJECT_TYPES[self.current_idx] 
                        new_obj = template.copy()
                        new_obj["args"] = choice
                        self.furniture_layer[self.popup_target_pos] = new_obj
                        self.show_popup = False
                        return

                if not self.popup_rect.collidepoint(mx, my):
                    self.show_popup = False

    def draw(self):
        self.screen.fill(GREY)
        
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, WHITE, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, WHITE, (0, y), (SCREEN_WIDTH, y))

        # Layer 0
        for loc, obj in self.furniture_layer.items():
            rect = pygame.Rect(loc[0], loc[1], GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, obj["color"], rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
            
            if "args" in obj:
                text = self.font.render(obj["args"][:3].upper(), True, BLACK)
                self.screen.blit(text, (loc[0]+5, loc[1]+10))

        # Layer 1
        for loc, obj in self.item_layer.items():
            rect = pygame.Rect(loc[0] + 5, loc[1] + 5, GRID_SIZE - 10, GRID_SIZE - 10)
            
            # Special Draw for Spawn Point to make it look distinct (Green Outline)
            if obj["type_id"] == "spawn_point":
                pygame.draw.rect(self.screen, obj["color"], rect, 4)
                text = self.font.render("P", True, obj["color"])
                self.screen.blit(text, (rect.centerx - 5, rect.centery - 10))
            else:
                pygame.draw.rect(self.screen, obj["color"], rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)

        # UI
        current_obj = OBJECT_TYPES[self.current_idx]
        ui_text = f"Tool: {current_obj['name']} | [S]ave [L]oad"
        pygame.draw.rect(self.screen, BLACK, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
        text_surf = self.font.render(ui_text, True, WHITE)
        self.screen.blit(text_surf, (10, SCREEN_HEIGHT - 25))
        
        if not self.show_popup:
            mx, my = pygame.mouse.get_pos()
            snap_x = (mx // GRID_SIZE) * GRID_SIZE
            snap_y = (my // GRID_SIZE) * GRID_SIZE
            pygame.draw.rect(self.screen, current_obj["color"], (snap_x, snap_y, GRID_SIZE, GRID_SIZE), 3)

        if self.show_popup:
            self.draw_popup()

        pygame.display.flip()

    def draw_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0,0,0))
        self.screen.blit(overlay, (0,0))

        pygame.draw.rect(self.screen, POPUP_BG, self.popup_rect)
        pygame.draw.rect(self.screen, POPUP_BORDER, self.popup_rect, 3)
        
        title = self.large_font.render("Select Ingredient", True, WHITE)
        self.screen.blit(title, (self.popup_rect.x + 20, self.popup_rect.y + 20))

        self.option_rects = []
        start_y = self.popup_rect.y + 70
        
        for i, ing in enumerate(self.available_ingredients):
            item_rect = pygame.Rect(self.popup_rect.x + 20, start_y + (i * 40), 360, 30)
            self.option_rects.append(item_rect)
            
            mx, my = pygame.mouse.get_pos()
            color = BLUE if item_rect.collidepoint(mx, my) else (80, 80, 80)
            
            pygame.draw.rect(self.screen, color, item_rect)
            pygame.draw.rect(self.screen, WHITE, item_rect, 1)
            
            text = self.font.render(ing.capitalize(), True, WHITE)
            self.screen.blit(text, (item_rect.x + 10, item_rect.y + 5))

if __name__ == "__main__":
    editor = MapEditor()
    editor.run()
