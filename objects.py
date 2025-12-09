import pygame
import json
import os

# --- Load Data ---
GAME_DATA = {}
if os.path.exists('gamedata.json'):
    try:
        with open('gamedata.json', 'r') as f:
            GAME_DATA = json.load(f)
    except:
        print("Error loading JSON")

class Ingredient(pygame.sprite.Sprite):
    def __init__(self, name, x, y):
        super().__init__()
        self.name = name
        
        data = GAME_DATA.get("ingredients", {}).get(name, {})
        
        self.colors = {
            "raw": tuple(data.get("color_raw", (255, 165, 0))),
            "chopped": tuple(data.get("color_chopped", (200, 200, 200))),
            "cooked": tuple(data.get("color_cooked", (150, 100, 50))),
            "burnt": tuple(data.get("color_burnt", (0, 0, 0)))
        }
        self.prepare_time = data.get("prepare_time", 100)
        self.cook_time = data.get("cook_time", 100)
        self.burn_time = data.get("burn_time", 100)

        self.state = "raw"
        self.progress = 0
        
        self.image = pygame.Surface((20, 20))
        self.image.fill(self.colors["raw"])
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.velocity = pygame.math.Vector2(0, 0)
        self.physics_state = "IDLE" 

    def update(self, walls):
        if self.physics_state == "FLYING":
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            hits = pygame.sprite.spritecollide(self, walls, False)
            if hits:
                target = hits[0]
                if target.held_item is None:
                    self.snap_to_counter(target)

    def snap_to_counter(self, counter):
        self.physics_state = "IDLE"
        self.velocity = pygame.math.Vector2(0, 0)
        self.rect.center = counter.rect.center
        counter.held_item = self

    def chop_tick(self):
        if self.state == "raw":
            self.progress += 1
            if self.progress % 10 == 0:
                print(f"DEBUG: Chopping... {self.progress}/{self.prepare_time}")
            
            if self.progress >= self.prepare_time:
                self.state = "chopped"
                self.progress = 0
                self.image.fill(self.colors["chopped"])
                pygame.draw.line(self.image, (255, 255, 255), (10, 0), (10, 20), 2)
        else:
            # DEBUG: Use this to see if the item is already chopped
            print(f"DEBUG: Cannot chop! Item state is: {self.state}")

    def cook_tick(self):
        if self.state == "chopped":
            self.progress += 1
            if self.progress >= self.cook_time:
                self.state = "cooked"
                self.progress = 0 
                self.image.fill(self.colors["cooked"])
        elif self.state == "cooked":
            self.progress += 1
            if self.progress >= self.burn_time:
                self.state = "burnt"
                self.image.fill(self.colors["burnt"])

class Counter(pygame.sprite.Sprite):
    def __init__(self, x, y, width=40, height=40):
        super().__init__()
        self.held_item = None
        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill((139, 69, 19)) 
        pygame.draw.rect(self.image_normal, (100, 50, 10), (0, 0, width, height), 2)
        
        self.image_highlight = pygame.Surface((width, height))
        self.image_highlight.fill((180, 110, 60))
        pygame.draw.rect(self.image_highlight, (255, 255, 100), (0, 0, width, height), 2)

        self.image = self.image_normal
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def highlight(self):
        self.image = self.image_highlight
    def reset(self):
        self.image = self.image_normal
    def update(self):
        pass 

class CuttingBoard(Counter):
    def __init__(self, x, y):
        super().__init__(x, y)
        pygame.draw.rect(self.image_normal, (240, 240, 240), (5, 5, 30, 30))
        pygame.draw.rect(self.image_highlight, (255, 255, 255), (5, 5, 30, 30))
        self.image = self.image_normal

    def interact_hold(self):
        if self.held_item:
            self.held_item.chop_tick()
        else:
            print("DEBUG: Board is empty, nothing to chop.")

    def draw_progress_bar(self, screen):
        if self.held_item and self.held_item.state == "raw":
            pct = self.held_item.progress / self.held_item.prepare_time
            if pct > 1: pct = 1
            pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
            pygame.draw.rect(screen, (0, 100, 255), (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))

class Stove(Counter):
    def __init__(self, x, y):
        super().__init__(x, y)
        pygame.draw.circle(self.image_normal, (20, 20, 20), (20, 20), 15)
        pygame.draw.circle(self.image_highlight, (50, 50, 50), (20, 20), 15)
        self.image = self.image_normal

    def update(self):
        if self.held_item:
            self.held_item.cook_tick()

    def draw_progress_bar(self, screen):
        if self.held_item and self.held_item.state in ["chopped", "cooked"]:
            item = self.held_item
            if item.state == "chopped":
                max_time = item.cook_time
                bar_color = (0, 255, 0)
            else: 
                max_time = item.burn_time
                bar_color = (255, 0, 0)
            
            pct = item.progress / max_time
            if pct > 1: pct = 1
            pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
            pygame.draw.rect(screen, bar_color, (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))
