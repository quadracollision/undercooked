import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import os

DATA_FILE = 'gamedata.json'

class LevelEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Overcooked Clone - Content Manager")
        self.root.geometry("600x750")

        self.data = self.load_data()
        
        # Temp storage for colors
        self.current_ing_colors = {
            "color_raw": (255, 165, 0),
            "color_chopped": (200, 200, 200),
            "color_cooked": (150, 100, 50),
            "color_burnt": (50, 50, 50),
            "crate_color": (100, 100, 100)
        }

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.setup_ingredient_tab()
        self.setup_recipe_tab()
        self.refresh_all_lists()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {"ingredients": {}, "recipes": {}}
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"ingredients": {}, "recipes": {}}

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)
        messagebox.showinfo("Success", "Data saved to gamedata.json!")
        self.refresh_all_lists()

    def refresh_all_lists(self):
        # Update Ingredient Dropdown
        ing_list = list(self.data["ingredients"].keys())
        self.ing_dropdown['values'] = ing_list
        
        # Update Recipe Dropdown
        rec_list = list(self.data["recipes"].keys())
        self.rec_dropdown['values'] = rec_list
        
        # Update Available Ingredients Listbox in Recipe Tab
        self.list_avail.delete(0, tk.END)
        for ing in ing_list:
            self.list_avail.insert(tk.END, ing)

    # ==========================
    #   TAB 1: INGREDIENTS
    # ==========================
    def setup_ingredient_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ingredients")

        # --- EDIT SELECTOR ---
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(top_frame, text="Edit Existing:").pack(side="left")
        
        self.ing_select_var = tk.StringVar()
        self.ing_dropdown = ttk.Combobox(top_frame, textvariable=self.ing_select_var, state="readonly")
        self.ing_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        self.ing_dropdown.bind("<<ComboboxSelected>>", self.load_ingredient_to_ui)
        
        ttk.Button(top_frame, text="New / Clear", command=self.clear_ingredient_ui).pack(side="right")

        # --- FORM ---
        ttk.Label(frame, text="Ingredient Name:").pack(pady=5)
        self.ing_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ing_name_var).pack()

        ttk.Label(frame, text="Cook In:").pack(pady=5)
        self.container_var = tk.StringVar(value="pot")
        self.container_dd = ttk.Combobox(frame, textvariable=self.container_var, state="readonly")
        self.container_dd['values'] = ('pot', 'pan')
        self.container_dd.pack()

        # Colors
        color_frame = ttk.LabelFrame(frame, text="Colors")
        color_frame.pack(pady=10, fill="x", padx=10)

        self.color_buttons = {}
        color_labels = {
            "color_raw": "Raw Color",
            "color_chopped": "Chopped Color",
            "color_cooked": "Cooked Color",
            "color_burnt": "Burnt Color",
            "crate_color": "Crate Appearance"
        }

        for key, label in color_labels.items():
            row = ttk.Frame(color_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=15).pack(side="left")
            btn = tk.Button(row, text="Pick Color", width=20, 
                            command=lambda k=key: self.pick_color(k))
            btn.pack(side="left", padx=10)
            self.color_buttons[key] = btn
            self.update_color_button(key)

        # Timers
        time_frame = ttk.LabelFrame(frame, text="Timers (Frames)")
        time_frame.pack(pady=10, fill="x", padx=10)

        self.time_vars = {}
        for key, label in [("prepare_time", "Chop Time"), ("cook_time", "Cook Time"), ("burn_time", "Burn Time")]:
            row = ttk.Frame(time_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=15).pack(side="left")
            var = tk.IntVar(value=100)
            ttk.Entry(row, textvariable=var).pack(side="left")
            self.time_vars[key] = var

        ttk.Button(frame, text="Save Ingredient", command=self.save_ingredient).pack(pady=20)

    def load_ingredient_to_ui(self, event=None):
        name = self.ing_select_var.get()
        if name not in self.data["ingredients"]: return

        data = self.data["ingredients"][name]
        
        # Fill Fields
        self.ing_name_var.set(name)
        self.container_var.set(data.get("container_type", "pot"))
        
        # Fill Timers
        for k in self.time_vars:
            self.time_vars[k].set(data.get(k, 100))
            
        # Fill Colors
        for k in self.current_ing_colors:
            if k in data:
                self.current_ing_colors[k] = tuple(data[k])
                self.update_color_button(k)

    def clear_ingredient_ui(self):
        self.ing_select_var.set("")
        self.ing_name_var.set("")
        self.container_var.set("pot")
        for k in self.time_vars: self.time_vars[k].set(100)
        # Reset colors to default
        self.current_ing_colors["color_raw"] = (255, 165, 0)
        # ... (reset others if desired) ...
        for k in self.current_ing_colors: self.update_color_button(k)

    def pick_color(self, key):
        color = colorchooser.askcolor(title=f"Choose {key}", color=self.current_ing_colors[key])
        if color[0]:
            self.current_ing_colors[key] = [int(c) for c in color[0]]
            self.update_color_button(key)

    def update_color_button(self, key):
        rgb = self.current_ing_colors[key]
        hex_col = '#%02x%02x%02x' % tuple(rgb)
        self.color_buttons[key].config(bg=hex_col, text=str(rgb))

    def save_ingredient(self):
        name = self.ing_name_var.get().lower().strip()
        if not name: return

        ing_data = {
            "container_type": self.container_var.get(),
            "prepare_time": self.time_vars["prepare_time"].get(),
            "cook_time": self.time_vars["cook_time"].get(),
            "burn_time": self.time_vars["burn_time"].get()
        }
        for k, v in self.current_ing_colors.items():
            ing_data[k] = v

        self.data["ingredients"][name] = ing_data
        self.save_data()

    # ==========================
    #   TAB 2: RECIPES
    # ==========================
    def setup_recipe_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Recipes")

        # --- EDIT SELECTOR ---
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(top_frame, text="Edit Existing:").pack(side="left")
        
        self.rec_select_var = tk.StringVar()
        self.rec_dropdown = ttk.Combobox(top_frame, textvariable=self.rec_select_var, state="readonly")
        self.rec_dropdown.pack(side="left", fill="x", expand=True, padx=5)
        self.rec_dropdown.bind("<<ComboboxSelected>>", self.load_recipe_to_ui)
        
        ttk.Button(top_frame, text="New / Clear", command=self.clear_recipe_ui).pack(side="right")

        # --- FORM ---
        ttk.Label(frame, text="Recipe Name:").pack(pady=5)
        self.rec_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.rec_name_var).pack()

        # Ingredient Builder
        sel_frame = ttk.Frame(frame)
        sel_frame.pack(pady=10, expand=True, fill="both")

        left_col = ttk.Frame(sel_frame)
        left_col.pack(side="left", expand=True, fill="both", padx=5)
        ttk.Label(left_col, text="Available Ingredients").pack()
        self.list_avail = tk.Listbox(left_col)
        self.list_avail.pack(expand=True, fill="both")

        mid_col = ttk.Frame(sel_frame)
        mid_col.pack(side="left", padx=5)
        ttk.Button(mid_col, text="Add ->", command=self.add_to_recipe).pack(pady=5)
        ttk.Button(mid_col, text="<- Remove", command=self.remove_from_recipe).pack(pady=5)

        right_col = ttk.Frame(sel_frame)
        right_col.pack(side="left", expand=True, fill="both", padx=5)
        ttk.Label(right_col, text="Recipe Ingredients").pack()
        self.list_recipe = tk.Listbox(right_col)
        self.list_recipe.pack(expand=True, fill="both")

        ttk.Button(frame, text="Save Recipe", command=self.save_recipe).pack(pady=20)

    def load_recipe_to_ui(self, event=None):
        name = self.rec_select_var.get()
        if name not in self.data["recipes"]: return
        
        data = self.data["recipes"][name]
        
        self.rec_name_var.set(name)
        
        # Fill Listbox
        self.list_recipe.delete(0, tk.END)
        for ing in data.get("ingredients", []):
            self.list_recipe.insert(tk.END, ing)

    def clear_recipe_ui(self):
        self.rec_select_var.set("")
        self.rec_name_var.set("")
        self.list_recipe.delete(0, tk.END)

    def add_to_recipe(self):
        selection = self.list_avail.curselection()
        if selection:
            item = self.list_avail.get(selection[0])
            self.list_recipe.insert(tk.END, item)

    def remove_from_recipe(self):
        selection = self.list_recipe.curselection()
        if selection:
            self.list_recipe.delete(selection[0])

    def save_recipe(self):
        name = self.rec_name_var.get().lower().strip()
        ingredients = self.list_recipe.get(0, tk.END)
        
        if not name: return
        if not ingredients:
            messagebox.showerror("Error", "Recipe empty")
            return

        self.data["recipes"][name] = {
            "ingredients": list(ingredients)
        }
        self.save_data()

if __name__ == "__main__":
    root = tk.Tk()
    app = LevelEditorApp(root)
    root.mainloop()
