import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((38, 38))
        self.image.fill((50, 150, 255))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.speed = 5
        self.facing = pygame.math.Vector2(0, 1) 
        self.inventory = None 

    def update(self, keys, obstacles):
        move_x = 0
        move_y = 0
        
        # --- Movement Logic ---
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -self.speed
            self.facing = pygame.math.Vector2(-1, 0)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = self.speed
            self.facing = pygame.math.Vector2(1, 0)
            
        self.rect.x += move_x
        hits = pygame.sprite.spritecollide(self, obstacles, False)
        for wall in hits:
            if move_x > 0: self.rect.right = wall.rect.left
            elif move_x < 0: self.rect.left = wall.rect.right

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -self.speed
            self.facing = pygame.math.Vector2(0, -1)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = self.speed
            self.facing = pygame.math.Vector2(0, 1)
            
        self.rect.y += move_y
        hits = pygame.sprite.spritecollide(self, obstacles, False)
        for wall in hits:
            if move_y > 0: self.rect.bottom = wall.rect.top
            elif move_y < 0: self.rect.top = wall.rect.bottom
            
        # --- Carry Logic ---
        if self.inventory:
            offset_dist = 30
            target_x = self.rect.centerx + (self.facing.x * offset_dist)
            target_y = self.rect.centery + (self.facing.y * offset_dist)
            self.inventory.rect.center = (target_x, target_y)

    def get_interaction_hitbox(self):
        interaction_dist = 40
        hitbox = self.rect.copy()
        hitbox.x += self.facing.x * interaction_dist
        hitbox.y += self.facing.y * interaction_dist
        return hitbox

    def pickup(self, item):
        self.inventory = item
        # FIX: Update physics_state, NOT state (which is for cooking)
        item.physics_state = "HELD"

    def drop(self):
        if self.inventory:
            item = self.inventory
            # FIX: Update physics_state
            item.physics_state = "IDLE"
            
            drop_zone = self.get_interaction_hitbox()
            item.rect.center = drop_zone.center
            self.inventory = None

    def throw(self):
        if self.inventory:
            item = self.inventory
            throw_speed = 10
            item.velocity = self.facing * throw_speed
            # FIX: Update physics_state
            item.physics_state = "FLYING"
            self.inventory = None
