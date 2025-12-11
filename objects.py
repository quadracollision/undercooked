import pygame
import json
import os
import random

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
                if target.held_item is None:
                    self.snap_to_counter(target)

    # --- VISUAL METHODS ---
    def highlight(self):
        pygame.draw.rect(self.image, (255, 255, 100), (0, 0, self.rect.width, self.rect.height), 2)

    def reset(self):
        self.redraw()

    def redraw(self):
        pass

class Ingredient(PhysicsEntity):
    def __init__(self, name, x, y):
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
        
        # Init physics
        super().__init__(x, y)
        self.redraw() # Draw AFTER init

    def redraw(self):
        color = self.colors.get(self.state, (255, 255, 255))
        self.image.fill(color)
        
        if self.state == "chopped":
            pygame.draw.line(self.image, (255, 255, 255), (10, 0), (10, 20), 2)

    def chop_tick(self):
        if self.state == "raw":
            self.progress += 1
            if self.progress >= self.prepare_time:
                self.state = "chopped"
                self.progress = 0
                self.redraw()

    def cook_tick(self):
        if self.state == "chopped":
            self.progress += 1
            if self.progress >= self.cook_time:
                self.state = "cooked"
                self.progress = 0 
                self.redraw()
        elif self.state == "cooked":
            self.progress += 1
            if self.progress >= self.burn_time:
                self.state = "burnt"
                self.redraw()

    def update(self, walls):
        super().update(walls)
        if self.physics_state == "FLYING":
            hits = pygame.sprite.spritecollide(self, walls, False)
            if hits:
                target_counter = hits[0]
                if target_counter.held_item and hasattr(target_counter.held_item, "add_ingredient"):
                    container = target_counter.held_item
                    if container.add_ingredient(self):
                        self.kill() 
                        return 

# --- CONTAINERS ---

class Container(PhysicsEntity):
    def __init__(self, name, x, y):
        self.name = name
        self.contents = [] 
        super().__init__(x, y)
        
        # Variables used by redraw()
        self.cooking_progress = 0
        self.cook_time_req = 100
        self.is_cooking = False
        self.food_ready = False
        self.burn_progress = 0
        self.burn_limit = 600
        self.is_burnt = False

class CookingContainer(Container):
    def __init__(self, name, x, y):
        # 1. Load Data
        data = GAME_DATA.get("containers", {}).get(name, {})
        self.min_items = data.get("min_items", 1)
        self.max_items = data.get("max_items", 3)
        self.visual_type = data.get("visual_type", name)
        
        self.image = pygame.Surface((30, 30))
        
        # 2. Init Parent
        super().__init__(name, x, y)
        
        # 3. Draw
        self.redraw()

    def redraw(self):
        # Generic background
        if self.visual_type == "pot":
            self.image.fill((50, 50, 50)) 
            pygame.draw.rect(self.image, (30,30,30), (0, 10, 30, 10))
            if self.food_ready:
                self.image.fill((160, 82, 45)) # Soup Color
        elif self.visual_type == "pan":
            self.image.fill((20, 20, 20)) 
            pygame.draw.line(self.image, (60, 60, 60), (15, 30), (15, 0), 4)
            if self.food_ready:
                pygame.draw.circle(self.image, (139, 69, 19), (15, 15), 10)
        else:
            self.image.fill((100, 100, 100)) # Default/Wok?
            
        if self.is_burnt:
             self.image.fill((0, 0, 0))

    def add_ingredient(self, ingredient):
        if self.is_burnt: return False
        
        # Check if ingredient allows this container
        ing_data = GAME_DATA.get("ingredients", {}).get(ingredient.name, {})
        allowed = ing_data.get("container_type", "pot")
        # For compatibility: if visual_type matches the allowed type 
        # (e.g. visual_type "pot" accepts things marked for "pot")
        # Custom Fix: Allow generic "container" to hold anything
        if allowed != self.visual_type and self.visual_type != "container": return False

        if ingredient.state == "chopped":
            if len(self.contents) < self.max_items:
                # Reset if we add stuff while cooking (basic logic)
                if self.cooking_progress > 0:
                     self.cooking_progress = 0
                     self.is_cooking = False
                
                self.contents.append(ingredient.name)
                return True
        return False

    def get_cook_requirements(self):
        """
        Returns (time_req, burn_req, is_complete)
        """
        current_content_sorted = sorted(self.contents)
        
        # 1. Check Recipes (including partials)
        best_match = None
        
        for r_name, r_data in GAME_DATA.get("recipes", {}).items():
            req_ings = sorted(r_data.get("ingredients", []))
            req_cont = r_data.get("container", "pot")
            
            # Must match container type
            if req_cont == self.visual_type or self.visual_type == "container":
                # Check for Exact Match
                if current_content_sorted == req_ings:
                    return r_data.get("cook_time", 500), 600, True
                
                # Check for Partial Match (Subset)
                # Naive subset check for lists with duplicates
                # We need to check if current_content is a subset of req_ings
                # E.g. [onion, onion] is subset of [onion, onion, onion]
                temp_req = req_ings.copy()
                is_subset = True
                for item in current_content_sorted:
                    if item in temp_req:
                        temp_req.remove(item)
                    else:
                        is_subset = False
                        break
                
                if is_subset and len(self.contents) > 0:
                    # Found a potential recipe we are working towards
                    # Use this recipe's times
                    best_match = (r_data.get("cook_time", 500), 600, False)
        
        if best_match:
            return best_match

        # 2. Check Single Ingredients (e.g. Hamburger in Pan)
        if len(self.contents) == 1:
            ing_name = self.contents[0]
            ing_data = GAME_DATA.get("ingredients", {}).get(ing_name, {})
            # Default to "pot" if undefined, handling the old onion case if needed
            req_cont = ing_data.get("container_type", "pot")
            
            if req_cont == self.visual_type or self.visual_type == "container":
                 return ing_data.get("cook_time", 200), ing_data.get("burn_time", 300), True
                 
        return None, None, False

    def cook_tick(self):
        if self.is_burnt: return
        
        cook_time, burn_time, is_complete = self.get_cook_requirements()
        
        if cook_time:
            # Cook if we have valid contents (even partial)
            if not self.food_ready:
                self.is_cooking = True
                self.cooking_progress += 1
                self.cook_time_req = cook_time 
                
                if self.cooking_progress >= cook_time:
                    if is_complete and len(self.contents) >= self.min_items:
                        self.food_ready = True
                        self.is_cooking = False
                        self.burn_limit = burn_time
                        self.redraw()
                    else:
                        # Cap progress if not complete
                        self.cooking_progress = cook_time
            else:
                 # Burn logic
                 self.burn_progress += 1
                 if self.burn_progress >= self.burn_limit:
                     self.is_burnt = True
                     self.food_ready = False
                     self.contents = ["burnt_sludge"]
                     self.redraw()
        else:
            self.is_cooking = False
            self.cooking_progress = 0

class Plate(Container):
    def __init__(self, x, y):
        self.image = pygame.Surface((30, 30))
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        
        # 1. Initialize Parent FIRST
        super().__init__("plate", x, y)
        
        # 2. Plate Stats
        self.is_dirty = False
        self.stack_count = 1
        
        # 3. Draw
        self.redraw()

    def redraw(self):
        self.image.fill((255, 255, 255)) 
        pygame.draw.circle(self.image, (200, 200, 200), (15, 15), 12, 1)
        
        if self.is_dirty:
            pygame.draw.circle(self.image, (100, 150, 100), (15, 15), 10)
        elif len(self.contents) > 0:
            pygame.draw.circle(self.image, (160, 82, 45), (15, 15), 8)

        if self.stack_count > 1:
            pygame.draw.circle(self.image, (255, 0, 0), (22, 8), 8)
            text = self.font.render(str(self.stack_count), True, (255, 255, 255))
            self.image.blit(text, (18, 0))

    def add_food(self, content_data):
        if self.is_dirty or self.stack_count > 1: return
        if isinstance(content_data, list): self.contents.extend(content_data)
        else: self.contents.append(content_data)
        self.redraw()

    def add_ingredient(self, ingredient):
        if self.is_dirty or self.stack_count > 1 or len(self.contents) > 0:
            return False
        self.make_dirty()
        return True

    def make_dirty(self):
        self.is_dirty = True
        self.contents = []
        self.redraw()

    def clean(self):
        self.is_dirty = False
        self.contents = []
        self.redraw()

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
        if self.held_item and hasattr(self.held_item, "cook_tick"):
            # print(f"DEBUG: Stove cooking {self.held_item.name}...") 
            self.held_item.cook_tick()

    def draw_progress_bar(self, screen):
        if self.held_item and isinstance(self.held_item, Container):
            container = self.held_item
            # print(f"DEBUG: Stove Drawing PB for {container.name}. Cooking: {container.is_cooking}, Prog: {container.cooking_progress}")
            if container.is_cooking or (container.cooking_progress > 0 and not container.food_ready):
                pct = container.cooking_progress / container.cook_time_req
                if pct > 1: pct = 1
                pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
                pygame.draw.rect(screen, (0, 255, 0), (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))
                pct = container.cooking_progress / container.cook_time_req
                if pct > 1: pct = 1
                pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
                pygame.draw.rect(screen, (0, 255, 0), (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))
            elif container.food_ready and not container.is_burnt:
                pct = container.burn_progress / container.burn_limit
                if pct > 1: pct = 1
                color = (255, 0, 0)
                if (pygame.time.get_ticks() // 200) % 2 == 0: 
                    color = (255, 100, 100)
                pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
                pygame.draw.rect(screen, color, (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))

class ServingCounter(Counter):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image_normal.fill((50, 50, 50)) 
        pygame.draw.rect(self.image_normal, (200, 200, 200), (0, 0, 20, 20))
        pygame.draw.rect(self.image_normal, (200, 200, 200), (20, 20, 20, 20))
        self.image_highlight = self.image_normal.copy()
        pygame.draw.rect(self.image_highlight, (255, 255, 100), (0, 0, 40, 40), 2)
        self.image = self.image_normal
        self.pending_returns = []

    def serve_plate(self):
        return_time = random.randint(300, 600) 
        self.pending_returns.append(return_time)
        print(f"DEBUG: Plate served! Returns in {return_time} frames.")

    def update(self, items_group=None, all_sprites=None):
        if items_group is None: return
        for i in range(len(self.pending_returns) - 1, -1, -1):
            self.pending_returns[i] -= 1
            if self.pending_returns[i] <= 0:
                if self.held_item is None:
                    self.pending_returns.pop(i)
                    plate = Plate(0, 0)
                    plate.make_dirty()
                    plate.snap_to_counter(self)
                    items_group.add(plate)
                    all_sprites.add(plate)
                    print("DEBUG: Dirty plate returned!")

class Sink(Counter):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image_normal.fill((100, 100, 100)) # Metal
        pygame.draw.rect(self.image_normal, (50, 150, 255), (5, 5, 30, 30)) # Water
        self.image_highlight = self.image_normal.copy()
        pygame.draw.rect(self.image_highlight, (255, 255, 100), (0, 0, 40, 40), 2)
        self.image = self.image_normal
        self.wash_progress = 0
        self.wash_time_req = 150 

    def interact_hold(self):
        if self.held_item and isinstance(self.held_item, Plate):
            plate = self.held_item
            if plate.is_dirty:
                self.wash_progress += 1
                if self.wash_progress >= self.wash_time_req:
                    self.wash_progress = 0
                    if plate.stack_count > 1:
                        plate.stack_count -= 1
                        plate.redraw_plate()
                        return "WASHED_STACK"
                    else:
                        plate.clean()
                        return "CLEANED_SINGLE"
        return None

    def draw_progress_bar(self, screen):
        if self.held_item and isinstance(self.held_item, Plate) and self.held_item.is_dirty:
            pct = self.wash_progress / self.wash_time_req
            if pct > 1: pct = 1
            pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
            pygame.draw.rect(screen, (0, 200, 255), (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))

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
