import pygame
import sys
import json
import os
from player import Player
from level import Level
from objects import Counter, CuttingBoard, Stove, Ingredient, Pot, Pan, Plate, PhysicsEntity, Crate, Container, ServingCounter, Sink
from orders import OrderManager
from ui import UIManager

# --- VIEWPORT CONSTANTS ---
GAME_WIDTH = 800
GAME_HEIGHT = 600
UI_HEIGHT = 120 

class Game:
    def __init__(self, level_path):
        pygame.init()
        
        # Store the path passed from the menu
        self.level_path = level_path
        
        # 1. WINDOW SIZE (Game + Top Bar)
        self.screen_width = GAME_WIDTH
        self.screen_height = GAME_HEIGHT + UI_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        
        # Set Title based on filename
        level_name = os.path.basename(level_path).split('.')[0]
        pygame.display.set_caption(f"Overcooked Clone - {level_name}")
        
        # 2. VIRTUAL CANVAS (The "Camera" looking at the kitchen)
        self.game_canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize Level with GAME dimensions
        self.level = Level(GAME_WIDTH, GAME_HEIGHT)
        
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        
        # Start a New Game
        self.new()

    def new(self):
        self.selected_object = None
        player_spawn_pos = (100, 300)
        level_recipes_data = {} # Default empty dict for recipes
        
        # --- LEVEL LOADER ---
        if os.path.exists(self.level_path):
            print(f"Loading map from {self.level_path}...")
            try:
                with open(self.level_path, 'r') as f:
                    data = json.load(f)
                
                # Detect Format: List (Old) vs Dict (New)
                if isinstance(data, list):
                    object_list = data
                else:
                    object_list = data.get("objects", [])
                    # Load the recipe config dictionary {name: [min, max]}
                    level_recipes_data = data.get("recipes", {})
                
                # --- FACTORY: Create Objects ---
                for item in object_list:
                    x, y = item["x"], item["y"]
                    obj_type = item["type"]
                    
                    if obj_type == "counter":
                        obj = Counter(x, y)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    elif obj_type == "cutting_board":
                        obj = CuttingBoard(x, y)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    elif obj_type == "stove":
                        obj = Stove(x, y)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    elif obj_type == "serving_counter":
                        obj = ServingCounter(x, y)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    elif obj_type == "sink":
                        obj = Sink(x, y)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    elif obj_type == "crate":
                        ing_name = item.get("args", "onion")
                        obj = Crate(x, y, ing_name)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    
                    elif obj_type == "spawn_point":
                        player_spawn_pos = (x, y)

                    elif obj_type in ["pot", "pan", "plate"]:
                        if obj_type == "pot": obj = Pot(0, 0)
                        elif obj_type == "pan": obj = Pan(0, 0)
                        elif obj_type == "plate": obj = Plate(0, 0)
                        
                        # Logic to snap to the counter underneath, or place on floor
                        dummy = pygame.sprite.Sprite()
                        dummy.rect = pygame.Rect(x, y, 40, 40)
                        hits = pygame.sprite.spritecollide(dummy, self.walls, False)
                        
                        if hits:
                            obj.snap_to_counter(hits[0])
                        else:
                            obj.rect.topleft = (x, y) # Floor placement
                        
                        self.items.add(obj)
                        self.all_sprites.add(obj)

            except json.JSONDecodeError:
                print(f"ERROR: {self.level_path} is corrupted or empty.")
        else:
            print(f"WARNING: {self.level_path} not found!")

        # Create Player
        self.player = Player(player_spawn_pos[0], player_spawn_pos[1])
        self.all_sprites.add(self.player)
        
        # --- INITIALIZE MANAGERS ---
        # Pass the recipe configuration to the order manager
        self.order_manager = OrderManager(level_recipes_data)
        self.ui_manager = UIManager(self.order_manager)

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                # Close Game Shortcut
                if event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
                    self.running = False
                    # Note: In a full game, this should return to Menu, not sys.exit()
                    # But for now, closing the window is fine.
                    return 

                if event.key == pygame.K_f:
                    self.player.throw()
                
                if event.key == pygame.K_SPACE:
                    held_item = self.player.inventory
                    target = self.selected_object
                    
                    # If looking at a counter with an item, interact with the ITEM, not the counter
                    real_target = target
                    if isinstance(target, Counter) and target.held_item:
                        real_target = target.held_item

                    # --- INTERACTION MATRIX ---

                    # 0. SPAWN FROM CRATE (Empty Hand -> Click Crate)
                    if held_item is None and isinstance(target, Crate):
                        new_item = Ingredient(target.ingredient_name, 0, 0)
                        self.items.add(new_item)
                        self.all_sprites.add(new_item)
                        self.player.pickup(new_item)
                        return

                    # 1. ADD INGREDIENT TO CONTAINER (Pot OR Pan)
                    if isinstance(held_item, Ingredient) and isinstance(real_target, Container):
                        if real_target.add_ingredient(held_item):
                            held_item.kill() # Remove from world
                            self.player.inventory = None
                            return

                    # 2. SERVE FOOD (Plate -> Container)
                    elif isinstance(held_item, Plate) and isinstance(real_target, Container):
                        if real_target.food_ready:
                            held_item.add_food(real_target.contents)
                            
                            # Reset Container
                            real_target.contents = [] 
                            real_target.food_ready = False
                            real_target.cooking_progress = 0
                            
                            # Visual Reset
                            if isinstance(real_target, Pot): 
                                real_target.image.fill((50,50,50))
                            elif isinstance(real_target, Pan):
                                real_target.image.fill((20,20,20))
                                pygame.draw.line(real_target.image, (60, 60, 60), (15, 30), (15, 0), 4)
                            return
                    
                    # 3. POUR FOOD (Container -> Plate)
                    elif isinstance(held_item, Container) and isinstance(real_target, Plate):
                        if held_item.food_ready and len(real_target.contents) == 0:
                            real_target.add_food(held_item.contents)
                            
                            # Reset Container
                            held_item.contents = []
                            held_item.food_ready = False
                            held_item.cooking_progress = 0
                            
                            # Visual Reset
                            if isinstance(held_item, Pot): 
                                held_item.image.fill((50,50,50))
                            elif isinstance(held_item, Pan):
                                held_item.image.fill((20,20,20))
                                pygame.draw.line(held_item.image, (60, 60, 60), (15, 30), (15, 0), 4)
                            return

                    # 4. SERVE PLATE (Serving Counter)
                    elif isinstance(held_item, Plate) and isinstance(target, ServingCounter):
                        if len(held_item.contents) > 0:
                            # Validates order and adds score
                            self.order_manager.check_delivery(held_item.contents)
                            
                            held_item.kill()
                            self.player.inventory = None
                            target.serve_plate() # Queues dirty plate return
                            return

                    # 5. PLATE STACKING (Plate -> Plate)
                    elif isinstance(held_item, Plate) and isinstance(real_target, Plate):
                        if held_item.is_dirty == real_target.is_dirty and \
                           len(held_item.contents) == 0 and len(real_target.contents) == 0:
                            real_target.stack_count += held_item.stack_count
                            real_target.redraw_plate()
                            held_item.kill()
                            self.player.inventory = None
                            return

                    # 6. STANDARD PICKUP / DROP (With Stack Splitting)
                    if held_item:
                        if isinstance(target, Counter) and target.held_item is None:
                            held_item.snap_to_counter(target)
                            self.player.inventory = None
                        elif target is None:
                            self.player.drop()
                    else:
                        if isinstance(target, Counter) and target.held_item:
                            item = target.held_item
                            
                            # Split Stack Logic
                            if isinstance(item, Plate) and item.stack_count > 1:
                                item.stack_count -= 1
                                item.redraw_plate()
                                new_plate = Plate(0, 0)
                                if item.is_dirty: new_plate.make_dirty()
                                self.items.add(new_plate)
                                self.all_sprites.add(new_plate)
                                self.player.pickup(new_plate)
                            else:
                                self.player.pickup(item)
                                target.held_item = None
                        elif isinstance(target, PhysicsEntity):
                            self.player.pickup(target)

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.walls)
        self.items.update(self.walls)
        
        # Update Managers
        self.order_manager.update()
        
        for wall in self.walls:
            # Pass groups so serving counter can spawn plates
            if isinstance(wall, ServingCounter):
                wall.update(self.items, self.all_sprites)
            else:
                wall.update()

        if self.selected_object:
            if isinstance(self.selected_object, Counter):
                self.selected_object.reset()
            self.selected_object = None

        hitbox = self.player.get_interaction_hitbox()
        temp_sprite = pygame.sprite.Sprite()
        temp_sprite.rect = hitbox
        
        # Priority 1: Walls
        hits = pygame.sprite.spritecollide(temp_sprite, self.walls, False)
        if hits:
            self.selected_object = hits[0]
            self.selected_object.highlight()
        else:
            # Priority 2: Items
            hits = pygame.sprite.spritecollide(temp_sprite, self.items, False)
            for item in hits:
                if hasattr(item, 'physics_state') and item.physics_state == "IDLE":
                    self.selected_object = item
                    break

        # [E] Key for Active Interactions (Chopping / Washing)
        if keys[pygame.K_e]:
            if self.selected_object:
                if isinstance(self.selected_object, CuttingBoard):
                    self.selected_object.interact_hold()
                elif isinstance(self.selected_object, Sink):
                    result = self.selected_object.interact_hold()
                    if result == "WASHED_STACK":
                        if self.player.inventory is None:
                            clean_plate = Plate(0, 0)
                            self.items.add(clean_plate)
                            self.all_sprites.add(clean_plate)
                            self.player.pickup(clean_plate)

    def draw(self):
        # 1. Render GAME WORLD to virtual canvas
        self.level.draw(self.game_canvas)
        self.all_sprites.draw(self.game_canvas)
        
        for wall in self.walls:
            if isinstance(wall, Stove) or isinstance(wall, CuttingBoard) or isinstance(wall, Sink):
                wall.draw_progress_bar(self.game_canvas)
        
        # 2. Render Background for UI Area
        self.screen.fill((30, 30, 30))
        
        # 3. Draw UI Bar at Top (Corrected: No extra arguments)
        self.ui_manager.draw(self.screen)
        
        # 4. Paste Game Canvas below UI
        self.screen.blit(self.game_canvas, (0, UI_HEIGHT))
        
        # 5. Draw Tooltip (Selected Object Info) floating on top
        if self.selected_object:
            self.ui_manager.draw_selection_info(self.screen, self.selected_object, self.screen_height)
        
        pygame.display.flip()
