import pygame
import sys
import subprocess # Needed for safe Tkinter launching
from menu import Menu
from game import Game
from map_editor import MapEditor

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 750 

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Undercooked Launcher")
    
    # Initial State
    current_state = "MENU"
    current_level_path = None

    while True:
        # --- STATE: MAIN MENU ---
        if current_state == "MENU":
            menu = Menu(screen)
            action, data = menu.run()
            
            if action == "PLAY":
                current_state = "GAME"
                current_level_path = data
            elif action == "MAP_EDITOR":
                current_state = "MAP_EDITOR"
            elif action == "LEVEL_EDITOR":
                current_state = "LEVEL_EDITOR"
            elif action == "QUIT":
                break

        # --- STATE: GAME ---
        elif current_state == "GAME":
            if current_level_path:
                # Reset screen to standard game size if needed
                game = Game(current_level_path)
                game.run() 
            # When game.run() returns (user pressed ESC), go back to menu
            current_state = "MENU"

        # --- STATE: MAP EDITOR (Pygame) ---
        elif current_state == "MAP_EDITOR":
            # Map Editor is Pygame-based, so we can run it directly in this process
            # for a perfectly seamless transition.
            editor = MapEditor()
            editor.run()
            
            # Re-init display surface when returning, just in case
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            current_state = "MENU"

        # --- STATE: LEVEL EDITOR (Tkinter) ---
        elif current_state == "LEVEL_EDITOR":
            # Tkinter hates running inside a Pygame loop. 
            # We close the Pygame window, run Tkinter as a subprocess, then reopen Pygame.
            pygame.display.quit()
            
            try:
                # Runs level_editor.py as a separate safe process
                subprocess.run([sys.executable, "level_editor.py"])
            except Exception as e:
                print(f"Error launching Level Editor: {e}")
            
            # Restart Pygame window seamlessly
            pygame.display.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            current_state = "MENU"

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
