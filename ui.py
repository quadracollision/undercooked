import pygame
import json
import os

GAME_DATA = {}
if os.path.exists('gamedata.json'):
    try:
        with open('gamedata.json', 'r') as f:
            GAME_DATA = json.load(f)
    except:
        pass

class UIManager:
    def __init__(self, order_manager):
        self.order_manager = order_manager
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.info_font = pygame.font.SysFont("Arial", 18)
        
        # UI Area Height (Must match game.py)
        self.height = 120 

    def draw(self, screen):
        # Draw Background Panel for Top Bar
        pygame.draw.rect(screen, (40, 40, 40), (0, 0, screen.get_width(), self.height))
        pygame.draw.line(screen, (255, 255, 255), (0, self.height - 2), (screen.get_width(), self.height - 2), 2)
        
        self.draw_score(screen)
        self.draw_tickets(screen)

    def draw_selection_info(self, screen, obj, screen_h):
        # Determine name logic
        target = obj
        if hasattr(obj, "held_item") and obj.held_item:
            target = obj.held_item

        name = "Unknown"
        details = ""
        
        if hasattr(target, "ingredient_name"): name = target.ingredient_name.capitalize()
        elif hasattr(target, "type_id"): name = target.type_id.replace("_", " ").title()
        elif hasattr(target, "name"): name = target.name.capitalize()
        elif hasattr(target, "image_normal"): name = type(target).__name__

        # Show contents for containers
        if hasattr(target, "contents") and len(target.contents) > 0:
            # Clean up list strings
            clean_contents = [c.replace("_", " ").capitalize() for c in target.contents]
            # Truncate if too long
            details_str = ", ".join(clean_contents)
            if len(details_str) > 20: details_str = details_str[:20] + "..."
            details = f" ({details_str})"
        
        # Show stack count
        if hasattr(target, "stack_count") and target.stack_count > 1:
            details += f" x{target.stack_count}"

        text = f"Selected: {name}{details}"
        
        # Draw at BOTTOM of the ACTUAL screen (overlaying the game)
        text_surf = self.info_font.render(text, True, (255, 255, 255))
        rect = text_surf.get_rect(center=(screen.get_width() // 2, screen_h - 40))
        
        bg_rect = rect.inflate(20, 10)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2)
        
        screen.blit(text_surf, rect)

    def draw_score(self, screen):
        score_text = f"Score: {self.order_manager.score}"
        text_surf = self.font.render(score_text, True, (255, 255, 255))
        
        x_pos = screen.get_width() - 150
        y_pos = 40
        
        pygame.draw.rect(screen, (0,0,0), (x_pos, y_pos, 130, 40))
        pygame.draw.rect(screen, (255, 255, 255), (x_pos, y_pos, 130, 40), 2)
        screen.blit(text_surf, (x_pos + 10, y_pos + 8))

    def draw_tickets(self, screen):
        start_x = 20
        start_y = 10
        ticket_w = 90
        ticket_h = 90 
        padding = 10

        for order in self.order_manager.orders:
            rect = pygame.Rect(start_x, start_y, ticket_w, ticket_h)
            
            # Ticket Background
            pygame.draw.rect(screen, (240, 240, 220), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)

            # Name
            name_text = self.small_font.render(order.recipe_name[:12], True, (0,0,0))
            screen.blit(name_text, (start_x + 5, start_y + 5))

            # Icons
            icon_y = start_y + 25
            icon_x = start_x + 5
            for ing in order.ingredients:
                ing_data = GAME_DATA.get("ingredients", {}).get(ing, {})
                color = tuple(ing_data.get("color_raw", (100, 100, 100)))
                pygame.draw.circle(screen, color, (icon_x + 10, icon_y + 10), 8)
                pygame.draw.circle(screen, (0,0,0), (icon_x + 10, icon_y + 10), 8, 1)
                
                icon_x += 20
                if icon_x > start_x + ticket_w - 20:
                    icon_x = start_x + 5
                    icon_y += 20

            # Time Bar
            bar_h = 8
            bar_y = start_y + ticket_h - 12
            pct = order.time_left / order.total_time
            if pct < 0: pct = 0
            
            bar_color = (0, 255, 0)
            if pct < 0.5: bar_color = (255, 255, 0)
            if pct < 0.2: bar_color = (255, 0, 0)

            pygame.draw.rect(screen, (50,50,50), (start_x + 5, bar_y, ticket_w - 10, bar_h))
            pygame.draw.rect(screen, bar_color, (start_x + 5, bar_y, (ticket_w - 10) * pct, bar_h))

            start_x += ticket_w + padding
