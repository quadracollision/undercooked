import pygame
import sys
import json
import os
from player import Player
from level import Level
from objects import Counter, Stove, Ingredient, CookingContainer, Plate, PhysicsEntity, Crate, Container, ServingCounter, Sink, Processor
from orders import OrderManager
from ui import UIManager

# --- VIEWPORT CONSTANTS ---
GAME_WIDTH = 800
GAME_HEIGHT = 600
UI_HEIGHT = 120 

class Game:
    def __init__(self, level_path):
        pygame.init()
        self.level_path = level_path
        self.screen_width = GAME_WIDTH
        self.screen_height = GAME_HEIGHT + UI_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        level_name = os.path.basename(level_path).split('.')[0]
        pygame.display.set_caption(f"Overcooked Clone - {level_name}")
        self.game_canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.level = Level(GAME_WIDTH, GAME_HEIGHT)
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.new()

    def new(self):
        self.selected_object = None
        player_spawn_pos = (100, 300)
        level_recipes_data = {} 
        if os.path.exists(self.level_path):
            print(f"Loading map from {self.level_path}...")
            try:
                with open(self.level_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    object_list = data
                else:
                    object_list = data.get("objects", [])
                    level_recipes_data = data.get("recipes", {})
                # Load Game Data for Dynamic Containers
                valid_containers = ["plate"]
                if os.path.exists('gamedata.json'):
                    try:
                        with open('gamedata.json', 'r') as gf:
                            gdata = json.load(gf)
                            valid_containers.extend(gdata.get("containers", {}).keys())
                    except:
                        pass
                
                for item in object_list:
                    x, y = item["x"], item["y"]
                    obj_type = item["type"]
                    
                    if obj_type == "counter":
                        obj = Counter(x, y); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "cutting_board":
                        obj = Processor(x, y, "cutting_board"); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "stove":
                        obj = Stove(x, y); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "processor":
                        p_type = item.get("args", "stove")
                        obj = Processor(x, y, p_type); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "serving_counter":
                        obj = ServingCounter(x, y); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "sink":
                        obj = Sink(x, y); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "crate":
                        ing = item.get("args", "onion"); obj = Crate(x, y, ing); self.walls.add(obj); self.all_sprites.add(obj)
                    elif obj_type == "spawn_point":
                        player_spawn_pos = (x, y)
                    elif obj_type in valid_containers or obj_type == "container":
                        if obj_type == "plate": obj = Plate(0, 0)
                        else: obj = CookingContainer(obj_type, 0, 0)
                        
                        d = pygame.sprite.Sprite(); d.rect = pygame.Rect(x, y, 40, 40)
                        h = pygame.sprite.spritecollide(d, self.walls, False)
                        if h: obj.snap_to_counter(h[0])
                        else: obj.rect.topleft = (x, y)
                        self.items.add(obj); self.all_sprites.add(obj)
            except json.JSONDecodeError: print(f"ERROR: {self.level_path} is corrupted.")
        else: print(f"WARNING: {self.level_path} not found!")
        self.player = Player(player_spawn_pos[0], player_spawn_pos[1])
        self.all_sprites.add(self.player)
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
            if event.type == pygame.QUIT: self.running = False; sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x or event.key == pygame.K_ESCAPE: self.running = False; return 
                if event.key == pygame.K_f: self.player.throw()
                if event.key == pygame.K_SPACE:
                    held_item = self.player.inventory
                    target = self.selected_object
                    real_target = target
                    if isinstance(target, Counter) and target.held_item: real_target = target.held_item
                    
                    if held_item is None and isinstance(target, Crate):
                        new_item = Ingredient(target.ingredient_name, 0, 0)
                        self.items.add(new_item); self.all_sprites.add(new_item); self.player.pickup(new_item); return
                    if isinstance(held_item, Ingredient) and isinstance(real_target, Container):
                        if real_target.add_ingredient(held_item): held_item.kill(); self.player.inventory = None; return
                    if isinstance(held_item, Plate) and isinstance(real_target, Container):
                        if real_target.food_ready:
                            held_item.add_food(real_target.contents)
                            real_target.contents = []; real_target.food_ready = False; real_target.cooking_progress = 0
                            if isinstance(real_target, CookingContainer): real_target.redraw()
                            return
                    if isinstance(held_item, Container) and isinstance(real_target, Plate):
                        if held_item.food_ready and len(real_target.contents) == 0:
                            real_target.add_food(held_item.contents)
                            held_item.contents = []; held_item.food_ready = False; held_item.cooking_progress = 0
                            if isinstance(held_item, CookingContainer): held_item.redraw()
                            return
                    if isinstance(held_item, Plate) and isinstance(target, ServingCounter):
                        if len(held_item.contents) > 0:
                            self.order_manager.check_delivery(held_item.contents)
                            held_item.kill(); self.player.inventory = None; target.serve_plate(); return
                    if isinstance(held_item, Plate) and isinstance(real_target, Plate):
                        if held_item.is_dirty == real_target.is_dirty and len(held_item.contents) == 0 and len(real_target.contents) == 0:
                            real_target.stack_count += held_item.stack_count
                            real_target.redraw_plate()
                            held_item.kill(); self.player.inventory = None; return
                    if held_item:
                        if isinstance(target, Counter) and target.held_item is None: held_item.snap_to_counter(target); self.player.inventory = None
                        elif target is None: self.player.drop()
                    else:
                        if isinstance(target, Counter) and target.held_item:
                            item = target.held_item
                            if isinstance(item, Plate) and item.stack_count > 1:
                                item.stack_count -= 1; item.redraw_plate()
                                new_plate = Plate(0, 0); 
                                if item.is_dirty: new_plate.make_dirty()
                                self.items.add(new_plate); self.all_sprites.add(new_plate); self.player.pickup(new_plate)
                            else: self.player.pickup(item); target.held_item = None
                        elif isinstance(target, PhysicsEntity): self.player.pickup(target)

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.walls)
        self.items.update(self.walls)
        self.order_manager.update()
        for wall in self.walls:
            if isinstance(wall, ServingCounter): wall.update(self.items, self.all_sprites)
            else: wall.update()

        # --- SELECTION & RESET LOGIC ---
        if self.selected_object:
            # RESET EVERYTHING, NOT JUST COUNTERS
            self.selected_object.reset()
            self.selected_object = None

        hitbox = self.player.get_interaction_hitbox()
        temp_sprite = pygame.sprite.Sprite()
        temp_sprite.rect = hitbox
        
        wall_hits = pygame.sprite.spritecollide(temp_sprite, self.walls, False)
        item_hits = pygame.sprite.spritecollide(temp_sprite, self.items, False)
        all_hits = wall_hits + item_hits
        
        if all_hits:
            interaction_point = pygame.math.Vector2(hitbox.center)
            def get_distance(obj): return interaction_point.distance_to(obj.rect.center)
            closest_obj = min(all_hits, key=get_distance)
            
            # Filter flying items
            if isinstance(closest_obj, PhysicsEntity) and getattr(closest_obj, 'physics_state', '') != "IDLE":
                pass
            else:
                self.selected_object = closest_obj
                self.selected_object.highlight()

        if keys[pygame.K_e]:
            if self.selected_object:
                if isinstance(self.selected_object, Processor) and self.selected_object.requires_interaction:
                    self.selected_object.interact_hold()
                elif isinstance(self.selected_object, Sink):
                    result = self.selected_object.interact_hold()
                    if result == "WASHED_STACK":
                        if self.player.inventory is None:
                            clean_plate = Plate(0, 0); self.items.add(clean_plate); self.all_sprites.add(clean_plate); self.player.pickup(clean_plate)

    def draw(self):
        self.level.draw(self.game_canvas)
        self.all_sprites.draw(self.game_canvas)
        for wall in self.walls:
            if hasattr(wall, "draw_progress_bar"): wall.draw_progress_bar(self.game_canvas)
        self.screen.fill((30, 30, 30))
        self.ui_manager.draw(self.screen)
        self.screen.blit(self.game_canvas, (0, UI_HEIGHT))
        if self.selected_object:
            self.ui_manager.draw_selection_info(self.screen, self.selected_object, self.screen_height)
        pygame.display.flip()
