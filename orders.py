import pygame
import random
import json
import os

# Load Data
GAME_DATA = {}
if os.path.exists('gamedata.json'):
    try:
        with open('gamedata.json', 'r') as f:
            GAME_DATA = json.load(f)
    except:
        print("Error loading JSON in orders.py")

class Order:
    def __init__(self, recipe_name, duration):
        self.recipe_name = recipe_name
        self.data = GAME_DATA.get("recipes", {}).get(recipe_name, {})
        self.ingredients = self.data.get("ingredients", [])
        
        self.total_time = duration
        self.time_left = duration
        
        # Calculate max score (50 pts per ingredient)
        self.max_score = len(self.ingredients) * 50

    def update(self):
        self.time_left -= 1
        return self.time_left > 0 

class OrderManager:
    def __init__(self, level_config_recipes=None):
        self.orders = []
        self.score = 0
        self.spawn_timer = 0
        self.spawn_interval = 600 # 10 seconds
        
        # 1. Get all valid recipes from Global Data
        all_possible = list(GAME_DATA.get("recipes", {}).keys())
        
        self.active_config = {}
        
        # 2. Parse Level Config (Handle both Dict and List for backward compatibility)
        if level_config_recipes and isinstance(level_config_recipes, dict):
            # NEW FORMAT: { "soup": [1800, 3600], ... }
            for name, rng in level_config_recipes.items():
                if name in all_possible:
                    self.active_config[name] = rng
        
        elif level_config_recipes and isinstance(level_config_recipes, list):
            # OLD FORMAT: ["soup", "steak"]
            for name in level_config_recipes:
                if name in all_possible:
                    self.active_config[name] = [1800, 2400] # Default range
        else:
            # FALLBACK: Enable everything
            for name in all_possible:
                self.active_config[name] = [1800, 2400]
            
        self.available_recipes = list(self.active_config.keys())
        print(f"DEBUG: Active Recipes: {self.available_recipes}")

    def update(self):
        # Update existing orders
        for order in self.orders[:]:
            if not order.update():
                self.orders.remove(order)
                self.score -= 50
                print("Order Expired! -50 pts")

        # Spawn new orders
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if len(self.orders) < 5: 
                self.spawn_new_order()

    def spawn_new_order(self):
        if not self.available_recipes: return
        
        name = random.choice(self.available_recipes)
        
        # LOOK UP RANGE AND RANDOMIZE DURATION
        time_range = self.active_config.get(name, [1800, 1800])
        duration = random.randint(time_range[0], time_range[1])
        
        new_order = Order(name, duration=duration)
        self.orders.append(new_order)
        print(f"New Order: {name} (Time: {duration})")

    def check_delivery(self, plate_contents):
        """
        Checks if the list of ingredients on the plate matches any active order.
        """
        plate_sorted = sorted(plate_contents)

        for order in self.orders:
            recipe_sorted = sorted(order.ingredients)
            
            if plate_sorted == recipe_sorted:
                # MATCH FOUND!
                # Calculate Tip based on speed
                percentage = order.time_left / order.total_time
                tip = int(percentage * 20)
                points = order.max_score + tip
                
                self.score += points
                self.orders.remove(order)
                print(f"Order Complete! +{points} pts")
                return True 
        
        # No match found
        print("Wrong Order! -10 pts")
        self.score -= 10
        return False
