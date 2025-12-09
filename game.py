import pygame
import sys
from player import Player
from level import Level
from objects import Counter, CuttingBoard, Stove, Ingredient

class Game:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Overcooked Clone - Manager")
        self.clock = pygame.time.Clock()
        self.running = True

        # Load the Level
        self.level = Level(self.screen_width, self.screen_height)
        
        # Create Groups
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        
        # Start a New Game
        self.new()

    def new(self):
        """Initialize variables for a new round"""
        # 1. Create Map
        for x in range(300, 500, 40):
            c = Counter(x, 200)
            self.walls.add(c)
            self.all_sprites.add(c)
        
        # Cutting Board (White)
        self.board = CuttingBoard(40, 40)
        self.walls.add(self.board)
        self.all_sprites.add(self.board)
        
        # Stove (Black Circle)
        self.stove = Stove(120, 40)
        self.walls.add(self.stove)
        self.all_sprites.add(self.stove)

        # 2. Create Player
        self.player = Player(100, 300)
        self.all_sprites.add(self.player)
        
        # 3. Spawn Ingredient
        onion = Ingredient("onion", 300, 200)
        # Snap to the first counter we made
        first_counter = self.walls.sprites()[0]
        onion.snap_to_counter(first_counter)
        
        self.items.add(onion)
        self.all_sprites.add(onion)

        self.selected_object = None

    def run(self):
        """The Game Loop"""
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def events(self):
        """Handle Inputs (Single Key Presses)"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    self.player.throw()
                
                # SPACE - Pickup/Drop Logic
                if event.key == pygame.K_SPACE:
                    if self.player.inventory:
                        # Case 1: Drop/Place
                        if isinstance(self.selected_object, Counter) and self.selected_object.held_item is None:
                            self.player.inventory.snap_to_counter(self.selected_object)
                            self.player.inventory = None
                        elif self.selected_object is None:
                            self.player.drop()
                    else:
                        # Case 2: Pickup
                        if isinstance(self.selected_object, Counter) and self.selected_object.held_item:
                            item = self.selected_object.held_item
                            self.player.pickup(item)
                            self.selected_object.held_item = None
                        elif isinstance(self.selected_object, Ingredient):
                            self.player.pickup(self.selected_object)

    def update(self):
        """Game Logic (Continuous)"""
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.walls)
        self.items.update(self.walls)
        
        for wall in self.walls:
            wall.update()

        # --- Raycast / Selection Logic ---
        # 1. Reset old selection
        if self.selected_object:
            if isinstance(self.selected_object, Counter):
                self.selected_object.reset()
            self.selected_object = None

        # 2. Check what is in front of player
        hitbox = self.player.get_interaction_hitbox()
        temp_sprite = pygame.sprite.Sprite()
        temp_sprite.rect = hitbox
        
        # Check Walls First
        hits = pygame.sprite.spritecollide(temp_sprite, self.walls, False)
        if hits:
            self.selected_object = hits[0]
            self.selected_object.highlight()
        else:
            # Check Items Second
            hits = pygame.sprite.spritecollide(temp_sprite, self.items, False)
            for item in hits:
                if item.physics_state == "IDLE":
                    self.selected_object = item
                    break

        # --- Active Interaction (E Key) ---
        if keys[pygame.K_e]:
            if self.selected_object:
                # DEBUG: Verify what we are interacting with
                if isinstance(self.selected_object, CuttingBoard):
                    self.selected_object.interact_hold()
                else:
                    # If you see this, you are facing the wrong thing
                    pass
                    # print(f"DEBUG: Holding E on {type(self.selected_object).__name__} (Not a Board)")

    def draw(self):
        """Render Screen"""
        self.level.draw(self.screen)
        self.all_sprites.draw(self.screen)
        
        # Draw Progress Bars
        for wall in self.walls:
            if isinstance(wall, Stove) or isinstance(wall, CuttingBoard):
                wall.draw_progress_bar(self.screen)

        pygame.display.flip()
