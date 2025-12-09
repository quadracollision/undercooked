import pygame

class Level:
    def __init__(self, screen_width, screen_height):
        # Create a surface for the background
        self.background = pygame.Surface((screen_width, screen_height))
        self.background.fill((230, 230, 230)) # Light Grey Floor
        
        # Draw grid lines (Visual guide for the 40x40 tiles)
        grid_color = (200, 200, 200)
        
        # Vertical lines
        for x in range(0, screen_width, 40):
            pygame.draw.line(self.background, grid_color, (x, 0), (x, screen_height))
            
        # Horizontal lines
        for y in range(0, screen_height, 40):
            pygame.draw.line(self.background, grid_color, (0, y), (screen_width, y))

    def draw(self, screen):
        # Blit the pre-drawn background onto the main screen
        screen.blit(self.background, (0, 0))
