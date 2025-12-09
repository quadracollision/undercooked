import pygame
import json
import os

# --- Load Data from JSON ---
GAME_DATA = {}
if os.path.exists('gamedata.json'):
    try:
        with open('gamedata.json', 'r') as f:
            GAME_DATA = json.load(f)
    except:
        print("Error loading JSON")

# --- BASE CLASSES ---

class PhysicsEntity(pygame.sprite.Sprite):
    """Base class for anything that can be carried (Ingredients, Pots, Plates)"""
    def __init__(self, x, y):
        super().__init__()
        self.physics_state = "IDLE" # IDLE, HELD, FLYING
        self.velocity = pygame.math.Vector2(0, 0)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def snap_to_counter(self, counter):
        """Helper to snap this object to a counter's center"""
        self.physics_state = "IDLE"
        self.velocity = pygame.math.Vector2(0, 0)
        self.rect.center = counter.rect.center
        counter.held_item = self

    def update(self, walls):
        """Physics logic for flying items"""
        if self.physics_state == "FLYING":
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            
            # Check for collisions with counters while flying
            hits = pygame.sprite.spritecollide(self, walls, False)
            if hits:
                target = hits[0]
                # Only land if counter is empty
                if target.held_item is None:
                    self.snap_to_counter(target)

class Ingredient(PhysicsEntity):
    def __init__(self, name, x, y):
        self.name = name
        
        # Load stats
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
        
        # Init physics
        super().__init__(x, y)

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
            # print(f"DEBUG: Cannot chop! Item state is: {self.state}")
            pass

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

    def update(self, walls):
        """
        Custom update for Ingredients to handle 'Pot Shots'
        """
        if self.physics_state == "FLYING":
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            
            # 1. Check Collision with Walls (Counters)
            hits = pygame.sprite.spritecollide(self, walls, False)
            if hits:
                target_counter = hits[0]
                
                # SPECIAL CHECK: Is there a CONTAINER (Pot/Pan) on this counter?
                if target_counter.held_item and hasattr(target_counter.held_item, "add_ingredient"):
                    container = target_counter.held_item
                    # Try to add myself to the container
                    if container.add_ingredient(self):
                        print(f"DEBUG: KOBE! Threw {self.name} into container!")
                        self.kill() # Delete the flying sprite
                        return # Stop processing

                # Normal Landing (if counter is empty)
                elif target_counter.held_item is None:
                    self.snap_to_counter(target_counter)

# --- CONTAINERS (Pots/Pans/Plates) ---

class Container(PhysicsEntity):
    def __init__(self, name, x, y):
        self.name = name
        self.contents = [] # List of strings (ingredient names)
        super().__init__(x, y)
        
        # Shared Stats
        self.cooking_progress = 0
        self.cook_time_req = 100
        self.is_cooking = False
        self.food_ready = False
        self.burn_progress = 0
        self.burn_limit = 600
        self.is_burnt = False

class Pot(Container):
    def __init__(self, x, y):
        self.image = pygame.Surface((30, 30))
        self.image.fill((50, 50, 50)) # Dark Grey
        pygame.draw.rect(self.image, (30,30,30), (0, 10, 30, 10)) 
        
        super().__init__("pot", x, y)
        self.cook_time_req = 500

    def add_ingredient(self, ingredient):
        if self.is_burnt: return False

        # --- VALIDATION: Check if this item belongs in a POT ---
        ing_data = GAME_DATA.get("ingredients", {}).get(ingredient.name, {})
        allowed_container = ing_data.get("container_type", "pot") 
        if allowed_container != "pot":
            print(f"DEBUG: {ingredient.name} belongs in a {allowed_container}, not a Pot!")
            return False

        if ingredient.state == "chopped":
            current_count = len(self.contents)
            
            # Weighted Average Logic:
            # If pot is hot, adding a raw item cools it down proportionally
            if current_count > 0 and self.cooking_progress > 0:
                total_heat = self.cooking_progress * current_count
                self.cooking_progress = int(total_heat / (current_count + 1))
                
                # If we dropped below threshold, we are no longer ready
                if self.food_ready:
                    print("DEBUG: Pot rescued from burning!")
                    self.food_ready = False
                    self.burn_progress = 0 # Reset burn meter
                    self.image.fill((50, 50, 50)) # Visual reset

            self.contents.append(ingredient.name)
            print(f"DEBUG: Added {ingredient.name} to Pot. Total: {len(self.contents)}")
            return True
        else:
            print("DEBUG: Must chop ingredient first!")
            return False

    def cook_tick(self):
        if self.is_burnt: return

        # 1. Cook if ANY items are inside
        if len(self.contents) > 0 and not self.food_ready:
            self.is_cooking = True
            self.cooking_progress += 1
            
            if self.cooking_progress >= self.cook_time_req:
                if len(self.contents) >= 3:
                    self.food_ready = True
                    self.is_cooking = False
                    self.image.fill((160, 82, 45)) # Soup Color
                    print("DEBUG: SOUP IS READY!")
                else:
                    self.cooking_progress = self.cook_time_req

        # 2. Burn if left too long
        elif self.food_ready:
            self.burn_progress += 1
            if self.burn_progress >= self.burn_limit:
                self.is_burnt = True
                self.food_ready = False
                self.contents = ["burnt_sludge"]
                self.image.fill((20, 20, 20)) 
                print("DEBUG: POT BURNED!")

        elif len(self.contents) == 0:
             self.is_cooking = False
             self.cooking_progress = 0

class Pan(Container):
    def __init__(self, x, y):
        self.image = pygame.Surface((30, 30))
        self.image.fill((20, 20, 20)) # Black Pan
        pygame.draw.line(self.image, (60, 60, 60), (15, 30), (15, 0), 4) 
        super().__init__("pan", x, y)
        self.cook_time_req = 300 

    def add_ingredient(self, ingredient):
        if self.is_burnt: return False
        if len(self.contents) >= 1: 
            print("DEBUG: Pan is full!")
            return False

        # --- VALIDATION: Check if this item belongs in a PAN ---
        ing_data = GAME_DATA.get("ingredients", {}).get(ingredient.name, {})
        allowed_container = ing_data.get("container_type", "pot") 
        if allowed_container != "pan":
            print(f"DEBUG: {ingredient.name} belongs in a {allowed_container}, not a Pan!")
            return False

        if ingredient.state == "chopped":
            self.contents.append(ingredient.name)
            return True
        else:
            print("DEBUG: Must chop ingredient first!")
            return False

    def cook_tick(self):
        if self.is_burnt: return

        # 1. Cooking
        if len(self.contents) == 1 and not self.food_ready:
            self.is_cooking = True
            self.cooking_progress += 1
            
            if self.cooking_progress >= self.cook_time_req:
                self.food_ready = True
                self.is_cooking = False
                # Visual change
                pygame.draw.circle(self.image, (139, 69, 19), (15, 15), 10)
        
        # 2. Burning
        elif self.food_ready:
            self.burn_progress += 1
            if self.burn_progress >= self.burn_limit:
                self.is_burnt = True
                self.food_ready = False
                self.contents = ["burnt_sludge"]
                self.image.fill((0, 0, 0)) # Charred

        elif len(self.contents) == 0:
            self.is_cooking = False
            self.cooking_progress = 0
            # Reset visual
            self.image.fill((20, 20, 20)) 
            pygame.draw.line(self.image, (60, 60, 60), (15, 30), (15, 0), 4)

class Plate(Container):
    def __init__(self, x, y):
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 255, 255)) # White
        pygame.draw.circle(self.image, (200, 200, 200), (15, 15), 12, 1)
        
        super().__init__("plate", x, y)

    def add_food(self, food_name):
        self.contents.append(food_name)
        # Visual change
        pygame.draw.circle(self.image, (160, 82, 45), (15, 15), 8)

# --- STATION OBJECTS ---

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
        if self.held_item and isinstance(self.held_item, Ingredient):
            self.held_item.chop_tick()

    def draw_progress_bar(self, screen):
        if self.held_item and isinstance(self.held_item, Ingredient) and self.held_item.state == "raw":
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
        # Duck Typing: Cook whatever is on top
        if self.held_item and hasattr(self.held_item, "cook_tick"):
            self.held_item.cook_tick()

    def draw_progress_bar(self, screen):
        # Works for both Pots and Pans
        if self.held_item and isinstance(self.held_item, Container):
            container = self.held_item
            
            # Draw Green Cooking Bar
            if container.is_cooking or (container.cooking_progress > 0 and not container.food_ready):
                pct = container.cooking_progress / container.cook_time_req
                if pct > 1: pct = 1
                pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
                pygame.draw.rect(screen, (0, 255, 0), (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))
            
            # Draw Red Burning Bar
            elif container.food_ready and not container.is_burnt:
                pct = container.burn_progress / container.burn_limit
                if pct > 1: pct = 1
                color = (255, 0, 0)
                if (pygame.time.get_ticks() // 200) % 2 == 0: 
                    color = (255, 100, 100)
                pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
                pygame.draw.rect(screen, color, (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))

# --- GENERIC CRATE CLASS ---
class Crate(Counter):
    def __init__(self, x, y, ingredient_name):
        super().__init__(x, y)
        self.ingredient_name = ingredient_name
        data = GAME_DATA.get("ingredients", {}).get(ingredient_name, {})
        base_color = tuple(data.get("crate_color", (100, 100, 100))) 
        
        self.image_normal = pygame.Surface((40, 40))
        self.image_normal.fill(base_color)
        border_col = (50, 30, 10)
        pygame.draw.rect(self.image_normal, border_col, (0, 0, 40, 40), 4)
        pygame.draw.line(self.image_normal, border_col, (0, 10), (40, 10), 2)
        pygame.draw.line(self.image_normal, border_col, (0, 20), (40, 20), 2)
        pygame.draw.line(self.image_normal, border_col, (0, 30), (40, 30), 2)
        
        icon_color = tuple(data.get("color_raw", (255, 255, 255)))
        pygame.draw.rect(self.image_normal, icon_color, (15, 15, 10, 10))

        self.image_highlight = self.image_normal.copy()
        pygame.draw.rect(self.image_highlight, (255, 255, 100), (0, 0, 40, 40), 2)
        self.image = self.image_normal
