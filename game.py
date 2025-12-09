import pygame
import sys
from player import Player
from level import Level
from objects import Counter, CuttingBoard, Stove, Ingredient, Pot, Plate, PhysicsEntity, Crate

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
        self.new()

    def new(self):
        # Island Counters
        for x in range(300, 500, 40):
            c = Counter(x, 200)
            self.walls.add(c)
            self.all_sprites.add(c)
        
        # Stations
        self.board = CuttingBoard(40, 40)
        self.walls.add(self.board)
        self.all_sprites.add(self.board)
        self.stove = Stove(120, 40)
        self.walls.add(self.stove)
        self.all_sprites.add(self.stove)

        # --- SPAWN CRATES ---
        onion_crate = Crate(40, 200, "onion")
        self.walls.add(onion_crate)
        self.all_sprites.add(onion_crate)

        tomato_crate = Crate(40, 240, "tomato")
        self.walls.add(tomato_crate)
        self.all_sprites.add(tomato_crate)

        # Player
        self.player = Player(100, 300)
        self.all_sprites.add(self.player)
        
        # Pot & Plate
        pot = Pot(0, 0)
        pot.snap_to_counter(self.stove)
        self.items.add(pot)
        self.all_sprites.add(pot)

        plate = Plate(0, 0)
        plate.snap_to_counter(self.walls.sprites()[1])
        self.items.add(plate)
        self.all_sprites.add(plate)

        self.selected_object = None

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
                # CLOSE GAME SHORTCUT
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

                    # 0. SPAWN FROM CRATE (Empty Hand -> Click Crate)
                    if held_item is None and isinstance(target, Crate):
                        new_item = Ingredient(target.ingredient_name, 0, 0)
                        self.items.add(new_item)
                        self.all_sprites.add(new_item)
                        self.player.pickup(new_item)
                        return

                    # 1. ADD INGREDIENT TO POT
                    if isinstance(held_item, Ingredient) and isinstance(real_target, Pot):
                        if real_target.add_ingredient(held_item):
                            held_item.kill()
                            self.player.inventory = None
                            return

                    # 2. SERVE SOUP (Plate -> Pot)
                    elif isinstance(held_item, Plate) and isinstance(real_target, Pot):
                        if real_target.soup_ready:
                            held_item.serve_soup()
                            real_target.contents = [] 
                            real_target.soup_ready = False
                            real_target.cooking_progress = 0
                            real_target.image.fill((50,50,50)) 
                            return
                    
                    # 3. POUR SOUP (Pot -> Plate)
                    elif isinstance(held_item, Pot) and isinstance(real_target, Plate):
                        if held_item.soup_ready and len(real_target.contents) == 0:
                            real_target.serve_soup()
                            held_item.contents = []
                            held_item.soup_ready = False
                            held_item.cooking_progress = 0
                            held_item.image.fill((50,50,50))
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
