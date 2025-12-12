import pygame
import os
import sys
import controls

# Constants
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (50, 150, 255)
LEVELS_DIR = "levels"

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 28)
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.state = "MAIN" 
        self.selected_index = 0
        
        self.main_options = ["Play Game", "Editors", "Settings", "Quit"]
        self.editor_options = ["Map Editor (Layout)", "Level Editor (Rules)", "Back"]
        
        self.packs = []
        self.levels = []
        self.current_pack_name = None
        self.rebinding_action = None

    def get_packs(self):
        if not os.path.exists(LEVELS_DIR): os.makedirs(LEVELS_DIR)
        return [d for d in os.listdir(LEVELS_DIR) if os.path.isdir(os.path.join(LEVELS_DIR, d))]

    def get_levels(self, pack_name):
        path = os.path.join(LEVELS_DIR, pack_name)
        return [f for f in os.listdir(path) if f.endswith(".json")]

    def run(self):
        # Reset selection when entering menu
        self.selected_index = 0
        self.state = "MAIN"
        
        while True:
            self.screen.fill(BG_COLOR)
            
            if self.state == "MAIN":
                self.draw_menu("Main Menu", self.main_options)
            elif self.state == "EDITORS":
                self.draw_menu("Editors", self.editor_options)
            elif self.state == "PACK_SELECT":
                self.draw_menu("Select Level Pack", self.packs if self.packs else ["No Packs Found (Create in Editor)"])
            elif self.state == "LEVEL_SELECT":
                self.draw_menu(f"Pack: {self.current_pack_name}", self.levels if self.levels else ["No Levels Found"])
            elif self.state == "SETTINGS":
                self.draw_settings()
            elif self.state == "REBIND":
                self.draw_settings()
                # Overlay
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0,0))
                msg = self.font.render(f"Press new key for {self.rebinding_action}...", True, (255, 255, 255))
                rect = msg.get_rect(center=(self.width//2, self.height//2))
                self.screen.blit(msg, rect)

            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT", None

                if self.state == "REBIND":
                    if event.type == pygame.KEYDOWN:
                        controls.manager.set_key(self.rebinding_action, event.key)
                        self.rebinding_action = None
                        self.state = "SETTINGS"
                    continue
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_index = max(0, self.selected_index - 1)
                    elif event.key == pygame.K_DOWN:
                        limit = 0
                        if self.state == "MAIN": limit = len(self.main_options)
                        elif self.state == "EDITORS": limit = len(self.editor_options)
                        elif self.state == "PACK_SELECT": limit = len(self.packs)
                        elif self.state == "LEVEL_SELECT": limit = len(self.levels)
                        elif self.state == "SETTINGS": limit = len(controls.manager.actions) + 1 # +1 for Back
                        if limit > 0: self.selected_index = min(limit - 1, self.selected_index + 1)
                    
                    elif event.key == pygame.K_RETURN:
                        result = self.handle_enter()
                        if result: return result # Exit menu loop, return to Main
                    
                    elif event.key == pygame.K_ESCAPE:
                        self.go_back()

            self.clock.tick(60)

    def handle_enter(self):
        if self.state == "MAIN":
            choice = self.main_options[self.selected_index]
            if choice == "Play Game":
                self.packs = self.get_packs()
                self.state = "PACK_SELECT"
                self.selected_index = 0
            elif choice == "Editors":
                self.state = "EDITORS"
                self.selected_index = 0
            elif choice == "Settings":
                self.state = "SETTINGS"
                self.selected_index = 0
            elif choice == "Quit":
                return "QUIT", None

        elif self.state == "EDITORS":
            choice = self.editor_options[self.selected_index]
            if choice == "Map Editor (Layout)":
                return "MAP_EDITOR", None
            elif choice == "Level Editor (Rules)":
                return "LEVEL_EDITOR", None
            elif choice == "Back":
                self.go_back()

        elif self.state == "PACK_SELECT":
            if not self.packs: return
            self.current_pack_name = self.packs[self.selected_index]
            self.levels = self.get_levels(self.current_pack_name)
            self.state = "LEVEL_SELECT"
            self.selected_index = 0
            
        elif self.state == "LEVEL_SELECT":
            if not self.levels: return
            level_name = self.levels[self.selected_index]
            full_path = os.path.join(LEVELS_DIR, self.current_pack_name, level_name)
            return "PLAY", full_path

        elif self.state == "SETTINGS":
            actions = list(controls.manager.actions.keys())
            if self.selected_index < len(actions):
                self.rebinding_action = actions[self.selected_index]
                self.state = "REBIND"
            else:
                self.go_back()

    def go_back(self):
        if self.state == "LEVEL_SELECT":
            self.state = "PACK_SELECT"
            self.selected_index = 0
        elif self.state == "PACK_SELECT":
            self.state = "MAIN"
            self.selected_index = 0
        elif self.state == "EDITORS":
            self.state = "MAIN"
            self.selected_index = 1
        elif self.state == "SETTINGS":
            self.state = "MAIN"
            self.selected_index = 2

    def draw_menu(self, title, items):
        title_surf = self.font.render(title, True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title_surf, title_rect)
        
        start_y = 200
        for i, item in enumerate(items):
            color = HIGHLIGHT_COLOR if i == self.selected_index else (100, 100, 100)
            text = self.small_font.render(item, True, color)
            rect = text.get_rect(center=(self.width // 2, start_y + (i * 60)))
            self.screen.blit(text, rect)
            
            if i == self.selected_index:
                pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect.inflate(40, 20), 2, border_radius=10)

    def draw_settings(self):
        title_surf = self.font.render("Settings - Controls", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title_surf, title_rect)
        
        start_y = 150
        actions = list(controls.manager.actions.items())
        
        # Draw actions
        for i, (action, keys) in enumerate(actions):
            color = HIGHLIGHT_COLOR if i == self.selected_index else (100, 100, 100)
            
            key_name = pygame.key.name(keys[0]) if keys else "None"
            # If multiple keys, show first
            
            action_text = self.small_font.render(f"{action}: {key_name}", True, color)
            rect = action_text.get_rect(center=(self.width // 2, start_y + (i * 40)))
            self.screen.blit(action_text, rect)
            
            if i == self.selected_index:
                pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect.inflate(20, 10), 2, border_radius=5)
        
        # Draw Back button
        back_idx = len(actions)
        color = HIGHLIGHT_COLOR if back_idx == self.selected_index else (100, 100, 100)
        text = self.small_font.render("Back", True, color)
        rect = text.get_rect(center=(self.width // 2, start_y + (back_idx * 40) + 20))
        self.screen.blit(text, rect)
        
        if back_idx == self.selected_index:
            pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect.inflate(40, 10), 2, border_radius=5)
