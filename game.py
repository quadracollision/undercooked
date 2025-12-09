import pygame
import sys
import json
import os
from player import Player
from level import Level
from objects import Counter, CuttingBoard, Stove, Ingredient, Pot, Pan, Plate, PhysicsEntity, Crate, Container

class Game:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Overcooked Clone")
        self.clock = pygame.time.Clock()
        self.running = True
        self.level = Level(self.screen_width, self.screen_height)
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        
        # Start a New Game
        self.new()

    def new(self):
        self.selected_object = None
        
        # Default spawn if none found in map
        player_spawn_pos = (100, 300)

        # --- LEVEL LOADER ---
        if os.path.exists("level1.json"):
            print("Loading map from level1.json...")
            try:
                with open("level1.json", 'r') as f:
                    level_data = json.load(f)
                
                for item in level_data:
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
                    elif obj_type == "crate":
                        ing_name = item.get("args", "onion")
                        obj = Crate(x, y, ing_name)
                        self.walls.add(obj)
                        self.all_sprites.add(obj)
                    
                    # --- SPAWN POINT ---
                    elif obj_type == "spawn_point":
                        player_spawn_pos = (x, y)
                        print(f"Player spawn set to {x}, {y}")

                    # --- CONTAINERS ---
                    elif obj_type in ["pot", "pan", "plate"]:
                        if obj_type == "pot": obj = Pot(0, 0)
                        elif obj_type == "pan": obj = Pan(0, 0)
                        elif obj_type == "plate": obj = Plate(0, 0)
                        
                        dummy = pygame.sprite.Sprite()
                        dummy.rect = pygame.Rect(x, y, 40, 40)
                        hits = pygame.sprite.spritecollide(dummy, self.walls, False)
                        
                        if hits:
                            obj.snap_to_counter(hits[0])
                        else:
                            obj.rect.topleft = (x, y)
                        
                        self.items.add(obj)
                        self.all_sprites.add(obj)

            except json.JSONDecodeError:
                print("ERROR: level1.json is corrupted or empty.")
        else:
            print("WARNING: level1.json not found! Run map_editor.py")

        # Create Player at the discovered spawn location
        self.player = Player(player_spawn_pos[0], player_spawn_pos[1])
        self.all_sprites.add(self.player)

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
                if event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
                    self.running = False
                    sys.exit()

                if event.key == pygame.K_f:
                    self.player.throw()
                
                if event.key == pygame.K_SPACE:
                    held_item = self.player.inventory
                    target = self.selected_object
                    
                    real_target = target
                    if isinstance(target, Counter) and target.held_item:
                        real_target = target.held_item

                    # --- INTERACTION MATRIX ---

                    # 0. SPAWN FROM CRATE
                    if held_item is None and isinstance(target, Crate):
                        new_item = Ingredient(target.ingredient_name, 0, 0)
                        self.items.add(new_item)
                        self.all_sprites.add(new_item)
                        self.player.pickup(new_item)
                        return

                    # 1. ADD INGREDIENT TO CONTAINER
                    if isinstance(held_item, Ingredient) and isinstance(real_target, Container):
                        if real_target.add_ingredient(held_item):
                            held_item.kill()
                            self.player.inventory = None
                            return

                    # 2. SERVE FOOD
                    elif isinstance(held_item, Plate) and isinstance(real_target, Container):
                        if real_target.food_ready:
                            held_item.add_food("cooked_dish")
                            real_target.contents = [] 
                            real_target.food_ready = False
                            real_target.cooking_progress = 0
                            if isinstance(real_target, Pot): 
                                real_target.image.fill((50,50,50))
                            elif isinstance(real_target, Pan):
                                real_target.image.fill((20,20,20))
                                pygame.draw.line(real_target.image, (60, 60, 60), (15, 30), (15, 0), 4)
                            return
                    
                    # 3. POUR FOOD
                    elif isinstance(held_item, Container) and isinstance(real_target, Plate):
                        if held_item.food_ready and len(real_target.contents) == 0:
                            real_target.add_food("cooked_dish")
                            held_item.contents = []
                            held_item.food_ready = False
                            held_item.cooking_progress = 0
                            if isinstance(held_item, Pot): 
                                held_item.image.fill((50,50,50))
                            elif isinstance(held_item, Pan):
                                held_item.image.fill((20,20,20))
                                pygame.draw.line(held_item.image, (60, 60, 60), (15, 30), (15, 0), 4)
                            return

                    # 4. STANDARD PICKUP / DROP
                    if held_item:
                        if isinstance(target, Counter) and target.held_item is None:
                            held_item.snap_to_counter(target)
                            self.player.inventory = None
                        elif target is None:
                            self.player.drop()
                    else:
                        if isinstance(target, Counter) and target.held_item:
                            self.player.pickup(target.held_item)
                            target.held_item = None
                        elif isinstance(target, PhysicsEntity):
                            self.player.pickup(target)

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.walls)
        self.items.update(self.walls)
        for wall in self.walls:
            wall.update()

        if self.selected_object:
            if isinstance(self.selected_object, Counter):
                self.selected_object.reset()
            self.selected_object = None

        hitbox = self.player.get_interaction_hitbox()
        temp_sprite = pygame.sprite.Sprite()
        temp_sprite.rect = hitbox
        
        hits = pygame.sprite.spritecollide(temp_sprite, self.walls, False)
        if hits:
            self.selected_object = hits[0]
            self.selected_object.highlight()
        else:
            hits = pygame.sprite.spritecollide(temp_sprite, self.items, False)
            for item in hits:
                if hasattr(item, 'physics_state') and item.physics_state == "IDLE":
                    self.selected_object = item
                    break

        if keys[pygame.K_e]:
            if self.selected_object:
                if isinstance(self.selected_object, CuttingBoard):
                    self.selected_object.interact_hold()

    def draw(self):
        self.level.draw(self.screen)
        self.all_sprites.draw(self.screen)
        for wall in self.walls:
            if isinstance(wall, Stove) or isinstance(wall, CuttingBoard):
                wall.draw_progress_bar(self.screen)
        pygame.display.flip()
