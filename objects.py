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

    def chop_tick(self, amount=1):
        if self.state == "raw":
            self.progress += amount
            if self.progress >= self.prepare_time:
                self.state = "chopped"
                self.progress = 0
                self.redraw()

    def cook_tick(self, amount=1):
        if self.state == "chopped":
            self.progress += amount
            if self.progress >= self.cook_time:
                self.state = "cooked"
                self.progress = 0 
                self.redraw()
        elif self.state == "cooked":
            self.progress += amount
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

from cooking import CookingManager

class CookingContainer(Container):
    def __init__(self, name, x, y):
        # 1. Load Data (for visual type only, logic is in manager)
        data = GAME_DATA.get("containers", {}).get(name, {})
        self.visual_type = data.get("visual_type", name)
        
        self.image = pygame.Surface((30, 30))
        
        # 2. Init Manager
        self.manager = CookingManager(name, GAME_DATA)
        
        # 3. Init Parent
        super().__init__(name, x, y)
        
        # 4. Draw
        self.redraw()

    @property
    def contents(self):
        return self.manager.contents
    
    @contents.setter
    def contents(self, value):
        # Allow external sets if necessary, but manager tracks it. 
        # For compatibility with some hacks, we might need to sync.
        # But generally, we should avoid setting this directly.
        self.manager.contents = value

    # Compatibility properties for Stove and other systems
    @property
    def is_cooking(self):
        return self.manager.state == "COOKING"
    
    @is_cooking.setter
    def is_cooking(self, value):
        # Allow setting to False to stop cooking (force IDLE or just stop progress?)
        # For init, if False, do nothing.
        if not value and self.manager.state == "COOKING":
             self.manager.state = "IDLE"

    @property
    def food_ready(self):
        return self.manager.state == "COOKED"
    
    @food_ready.setter
    def food_ready(self, value):
        if value: self.manager.state = "COOKED"
        elif self.manager.state == "COOKED": 
             # If setting False from True, maybe reset?
             # But init sets False.
             if self.manager.state != "COOKED": pass # Ignore init
             else: self.manager.state = "IDLE"

    @property
    def is_burnt(self):
        return self.manager.state == "BURNT"
    
    @is_burnt.setter
    def is_burnt(self, value):
        if value: self.manager.state = "BURNT"
        elif self.manager.state == "BURNT":
            # Resetting burnt?
            self.manager.state = "IDLE"
            self.manager.contents = [] # Clear sludge?
    
    @property
    def cooking_progress(self):
        return self.manager.current_progress
    
    @cooking_progress.setter
    def cooking_progress(self, value):
        self.manager.current_progress = value

    @property
    def cook_time_req(self):
        # Avoid division by zero
        return self.manager.target_progress if self.manager.target_progress > 0 else 100
    
    @cook_time_req.setter
    def cook_time_req(self, value):
        self.manager.target_progress = value

    @property
    def burn_progress(self):
        return self.manager.burn_progress
    
    @burn_progress.setter
    def burn_progress(self, value):
        self.manager.burn_progress = value

    @property
    def burn_limit(self):
        return self.manager.burn_limit if self.manager.burn_limit > 0 else 100
    
    @burn_limit.setter
    def burn_limit(self, value):
        self.manager.burn_limit = value

    def redraw(self):
        # Generic background
        if self.visual_type == "pot":
            self.image.fill((50, 50, 50)) 
            pygame.draw.rect(self.image, (30,30,30), (0, 10, 30, 10))
            # ONLY show soup if full
            is_full = len(self.manager.contents) >= self.manager.min_items
            if self.food_ready and is_full:
                self.image.fill((160, 82, 45)) # Soup Color
        elif self.visual_type == "pan":
            self.image.fill((20, 20, 20)) 
            pygame.draw.line(self.image, (60, 60, 60), (15, 30), (15, 0), 4)
            # Pan usually 1 item, so min_items is 1.
            is_full = len(self.manager.contents) >= self.manager.min_items
            if self.food_ready and is_full:
                pygame.draw.circle(self.image, (139, 69, 19), (15, 15), 10)
        else:
            self.image.fill((100, 100, 100)) # Default/Wok?
            
        if self.is_burnt:
             self.image.fill((0, 0, 0))

    def add_ingredient(self, ingredient):
        # Delegate to manager
        if self.manager.add_ingredient(ingredient.name):
             self.redraw()
             return True
        return False

    def get_cook_requirements(self):
        # Deprecated logic, but keeping empty or delegating if something calls it.
        # It was internal.
        return None

    def cook_tick(self, amount=1.0):
        self.manager.tick(amount)
        if self.manager.state in ["COOKED", "BURNT", "COOKING"]:
             self.redraw()


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
        if self.is_dirty:
            return False
        
        # Check for stack limit if it's a stack of plates
        if self.stack_count > 1:
            return False

        # Allow adding if empty OR if we are building a recipe on a single plate
        # We generally allow adding if it's not full? 
        # For this game, plates usually hold one completed meal or partials.
        # Let's assume infinite capacity for simplicity or check order match later.
        # But UI might look weird. For now, just append.
        
        # Handle State Suffixes
        name_to_add = ingredient.name
        if ingredient.state == "chopped":
            name_to_add += "_chopped"
        elif ingredient.state == "cooked":
             # Optional: name_to_add += "_cooked" 
             # But legacy recipes just use "onion" for cooked onion soup usually?
             # Let's check: onion_soup uses "onion". Stove cooks it. 
             # Does stove change name in contents? 
             # Stove -> CookingManager -> matches recipe -> produces output? 
             # Actually, soup is liquid. 
             # Burgers: Cooked patty on plate.
             # If we put cooked item, we probably want just the name if that's what recipes use.
             # Standardizing on existing behavior for cooked items.
             pass
        elif ingredient.state == "burnt":
             return False # Don't plate burnt stuff usually? Or maybe allow it for failure.

        self.contents.append(name_to_add)
        self.redraw()
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

# Removed legacy CuttingBoard class as it is now a Processor alias


class Processor(Counter):
    def __init__(self, x, y, type_id="stove"):
        super().__init__(x, y)
        self.type_id = type_id
        self.data = GAME_DATA.get("processors", {}).get(type_id, {})
        
        # 1. Visuals
        color = tuple(self.data.get("color", (50, 50, 50)))
        
        # Override image_normal from Counter
        self.image_normal = pygame.Surface((40, 40))
        self.image_normal.fill(color) 
        # Add a generic visual detail (circle)
        pygame.draw.circle(self.image_normal, (20, 20, 20), (20, 20), 12)
        pygame.draw.rect(self.image_normal, (30, 30, 30), (0, 0, 40, 40), 2)

        self.image_highlight = self.image_normal.copy()
        pygame.draw.rect(self.image_highlight, (255, 255, 100), (0, 0, 40, 40), 2)
        
        self.image = self.image_normal
        
        # 2. Logic Params
        self.process_method = self.data.get("process_method", "cook_tick")
        self.progress_bar_color = tuple(self.data.get("progress_bar_color", (0, 255, 0)))
        self.processing_speed = self.data.get("processing_speed", 1.0)
        self.requires_interaction = self.data.get("requires_interaction", False)

    def update(self):
        # Automatic processing only if interaction NOT required
        if not self.requires_interaction:
            if self.held_item and hasattr(self.held_item, self.process_method):
                try:
                    getattr(self.held_item, self.process_method)(amount=self.processing_speed)
                except TypeError:
                    getattr(self.held_item, self.process_method)()

    def interact_hold(self):
        # Manual processing only if interaction IS required
        if self.requires_interaction:
             if self.held_item and hasattr(self.held_item, self.process_method):
                try:
                    getattr(self.held_item, self.process_method)(amount=self.processing_speed)
                except TypeError:
                    getattr(self.held_item, self.process_method)()

    def draw_progress_bar(self, screen):
        if not self.held_item: return
        
        item = self.held_item
        current = 0
        target = 100
        is_active = False
        is_ready = False
        is_burnt = False
        
        # Try to detect progress (Generic or Specific)
        if hasattr(item, "is_cooking"): # specialized for CookingContainer
             is_active = item.is_cooking
             if hasattr(item, "cooking_progress"): current = item.cooking_progress
             if hasattr(item, "cook_time_req"): target = item.cook_time_req
             if hasattr(item, "food_ready"): is_ready = item.food_ready
             if hasattr(item, "is_burnt"): is_burnt = item.is_burnt
        elif hasattr(item, "progress") and hasattr(item, "prepare_time"): # Ingredient/Generic
             current = item.progress
             target = item.prepare_time
             if current > 0: is_active = True # Assume active if progress > 0
        
        # Draw Bar
        if is_active or (current > 0 and not is_ready):
            if target == 0: target = 100
            pct = current / target
            if pct > 1: pct = 1
            
            # Double bar style (from original Stove) ??
            # Original Stove drew current/target.
            pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
            pygame.draw.rect(screen, self.progress_bar_color, (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))
            
        elif is_ready and not is_burnt:
             # Burning Phase (specific to CookingContainer mostly)
             if hasattr(item, "burn_progress") and hasattr(item, "burn_limit"):
                 pct = item.burn_progress / item.burn_limit
                 if pct > 1: pct = 1
                 color = (255, 0, 0)
                 if (pygame.time.get_ticks() // 200) % 2 == 0: color = (255, 100, 100)
                 pygame.draw.rect(screen, (0,0,0), (self.rect.x + 5, self.rect.y - 10, 30, 5))
                 pygame.draw.rect(screen, color, (self.rect.x + 5, self.rect.y - 10, 30 * pct, 5))

class Stove(Processor):
    def __init__(self, x, y):
        super().__init__(x, y, "stove")

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
