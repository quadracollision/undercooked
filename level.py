import pygame

class Level:
    def __init__(self, width, height, tile_size=40):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # Create a floor tile texture (Checkered pattern)
        self.floor_image = pygame.Surface((tile_size, tile_size))
        self.floor_image.fill((220, 220, 220)) # Light Grey
        pygame.draw.rect(self.floor_image, (200, 200, 200), (0, 0, tile_size, tile_size), 1) # Border

    def draw(self, surface):
        # Fill background first to prevent trails
        surface.fill((0, 0, 0)) 
        
        # Draw Floor Tiles
        for y in range(0, self.height, self.tile_size):
            for x in range(0, self.width, self.tile_size):
                surface.blit(self.floor_image, (x, y))
                
        # Draw Grid Lines (Optional, helps with placement)
        for x in range(0, self.width, self.tile_size):
            pygame.draw.line(surface, (180, 180, 180), (x, 0), (x, self.height))
        for y in range(0, self.height, self.tile_size):
            pygame.draw.line(surface, (180, 180, 180), (0, y), (self.width, y))
