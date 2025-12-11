import json
import os

class CookingManager:
    """
    Manages the cooking state of a container.
    Data-driven by gamedata.json.
    """
    def __init__(self, container_name, game_data=None):
        self.container_name = container_name
        
        # Load data if not provided
        if game_data is None:
            self.game_data = self._load_data()
        else:
            self.game_data = game_data

        self.contents = [] # List of ingredient names
        self.state = "IDLE" # IDLE, COOKING, COOKED, BURNT
        
        # Progress Tracking
        self.current_progress = 0
        self.target_progress = 0 # Calculated total cook time
        
        self.burn_progress = 0
        self.burn_limit = 0 # Calculated burn time

        # Cache container stats
        c_data = self.game_data.get("containers", {}).get(container_name, {})
        self.min_items = c_data.get("min_items", 1)
        self.max_items = c_data.get("max_items", 3)
        self.visual_type = c_data.get("visual_type", container_name)

    def _load_data(self):
        if os.path.exists('gamedata.json'):
            with open('gamedata.json', 'r') as f:
                return json.load(f)
        return {"ingredients": {}, "containers": {}, "recipes": {}}

    def can_add(self, ingredient_name):
        """Check if ingredient can be added to this container."""
        if self.state == "BURNT":
            return False
        
        if len(self.contents) >= self.max_items:
            return False

        # Check compatibility
        ing_data = self.game_data.get("ingredients", {}).get(ingredient_name, {})
        # If specific container required, strict check. 
        # Otherwise default to 'pot' or generic behavior.
        # User Logic: "ingredients should tell which containers they can be cooked in"
        req_cont = ing_data.get("container_type", "pot")
        
        # Logic from previous objects.py (simplified and corrected):
        # If container is generic "container", it accepts everything (debug/map editor feature maybe?)
        # Otherwise, must match visual_type or name.
        if self.visual_type == "container":
            return True
            
        if req_cont != self.visual_type:
            return False
            
        return True

    def add_ingredient(self, ingredient_name):
        if not self.can_add(ingredient_name):
            return False

        self.contents.append(ingredient_name)
        
        self._recalculate_requirements()

        
        if self.state == "COOKED":
            self.state = "COOKING"
        
        return True

    def _recalculate_requirements(self):
        """
        Calculate total cook time and burn time based on contents.
        Rule: Sum of all ingredients' cook times (or max? Sum makes sense for 'work').
        """
        total_cook = 0
        total_burn = 0 # Maybe min burn time? Chain is as weak as weakest link.
        
        # If empty, 0
        if not self.contents:
            self.target_progress = 0
            self.burn_limit = 0
            return

        # Strategy: 
        # Cook Time: Sum of ingredients? Or Max?
        # User didn't specify exact math, but "reducing progress bar" implies new target is larger or current is smaller.
        # Summing is a safe bet for physics.
        # Burn Time: The item that burns fastest dictates the burn? Or sum?
        # Usually in games, if one thing burns, it ruins the dish. So MIN burn time.
        
        found_burn_times = []
        
        for item in self.contents:
            data = self.game_data.get("ingredients", {}).get(item, {})
            total_cook += data.get("cook_time", 100) # Default 100
            found_burn_times.append(data.get("burn_time", 100))
            
        self.target_progress = total_cook
        if found_burn_times:
            self.burn_limit = min(found_burn_times) # Burn as soon as the most delicate item burns
        else:
            self.burn_limit = 100

    def tick(self, amount=1.0):
        """
        Advance cooking state by 'amount' ticks.
        """
        if not self.contents:
            self.state = "IDLE"
            self.current_progress = 0
            return

        # If we are IDLE but have contents, -> COOKING
        if self.state == "IDLE":
             self.state = "COOKING"

        if self.state == "COOKING":
            self.current_progress += amount
            if self.current_progress >= self.target_progress:
                self.state = "COOKED"
                self.current_progress = self.target_progress # Cap it
                self.burn_progress = 0 # Start burn timer
        
        elif self.state == "COOKED":
            self.burn_progress += amount
            if self.burn_progress >= self.burn_limit:
                self.state = "BURNT"
                self.contents = ["burnt_sludge"] # Ruin food

    def get_progress_percent(self):
        if self.state == "COOKING":
            if self.target_progress == 0: return 0
            return min(1.0, self.current_progress / self.target_progress)
        elif self.state == "COOKED":
             # Maybe show burn progress?
             return 1.0
        return 0.0

    def get_burn_percent(self):
        if self.state == "COOKED":
            if self.burn_limit == 0: return 0
            return min(1.0, self.burn_progress / self.burn_limit)
        return 0.0
