import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import os

# --- CONFIGURATION ---
DATA_FILE = 'gamedata.json'
LEVELS_DIR = 'levels'

# --- DARK THEME COLORS ---
BG_COLOR = "#2e2e2e"
FG_COLOR = "#ffffff"
ENTRY_BG = "#404040"
ACCENT_COLOR = "#4a90e2" # Soft Blue
SUCCESS_COLOR = "#28a745" # Green
WARNING_COLOR = "#ffc107" # Yellow/Orange

class DarkLevelEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Undercooked - Data Editor")
        self.root.geometry("900x750")
        self.root.configure(bg=BG_COLOR)
        
        # Apply Dark Theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure(".", background=BG_COLOR, foreground=FG_COLOR, fieldbackground=ENTRY_BG)
        self.style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Arial", 10))
        self.style.configure("TButton", background="#505050", foreground=FG_COLOR, borderwidth=1)
        self.style.map("TButton", background=[('active', ACCENT_COLOR)])
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#404040", foreground=FG_COLOR, padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[('selected', ACCENT_COLOR)])
        self.style.configure("TLabelframe", background=BG_COLOR, foreground=ACCENT_COLOR)
        self.style.configure("TLabelframe.Label", background=BG_COLOR, foreground=ACCENT_COLOR, font=("Arial", 10, "bold"))
        self.style.configure("TCheckbutton", background=BG_COLOR, foreground=FG_COLOR)
        self.style.configure("TCombobox", fieldbackground=ENTRY_BG, background=BG_COLOR, foreground=FG_COLOR)

        # 1. Load Global Data
        self.data = self.load_json(DATA_FILE, {"ingredients": {}, "recipes": {}})
        
        # 2. Scan Levels
        self.available_levels = self.scan_levels()
        self.current_level_path = self.available_levels[0] if self.available_levels else None
        
        # 3. Load Level Data (if exists)
        if self.current_level_path:
            self.level_data = self.load_json(self.current_level_path, {"objects": [], "recipes": {}})
        else:
            self.level_data = {"objects": [], "recipes": {}}

        # Fix legacy format
        if isinstance(self.level_data.get("recipes"), list):
            new_recs = {r: [1800, 3600] for r in self.level_data["recipes"]}
            self.level_data["recipes"] = new_recs

        # --- UI LAYOUT ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tabs
        self.setup_ingredient_tab()
        self.setup_recipe_tab()
        self.setup_container_tab()
        self.setup_level_tab()

        # Temporary Color Storage
        self.current_ing_colors = {
            "color_raw": (255, 165, 0), "color_chopped": (200, 200, 200),
            "color_cooked": (150, 100, 50), "color_burnt": (50, 50, 50),
            "crate_color": (100, 100, 100)
        }
        
        self.refresh_ui()

    def run(self):
        self.root.eval('tk::PlaceWindow . center')
        self.root.mainloop()

    # --- HELPERS ---
    def load_json(self, path, default):
        if not os.path.exists(path): return default
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return default

    def save_json(self, path, data):
        with open(path, 'w') as f: json.dump(data, f, indent=4)
        print(f"Saved {path}")

    def scan_levels(self):
        """Scans LEVELS_DIR and subfolders for .json files"""
        levels = []
        if not os.path.exists(LEVELS_DIR):
            os.makedirs(LEVELS_DIR)
            
        for root, dirs, files in os.walk(LEVELS_DIR):
            for file in files:
                if file.endswith(".json"):
                    # Keep full path relative to script
                    full_path = os.path.join(root, file)
                    levels.append(full_path)
        return levels

    # --- TAB 1: INGREDIENTS ---
    def setup_ingredient_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Ingredients  ")

        paned = ttk.PanedWindow(frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        side_frame = ttk.Frame(paned, width=200)
        lbl = ttk.Label(side_frame, text="Ingredients List", font=("Arial", 12, "bold"))
        lbl.pack(pady=5)
        
        list_frame = ttk.Frame(side_frame)
        list_frame.pack(fill="both", expand=True)
        
        self.ing_listbox = tk.Listbox(list_frame, bg=ENTRY_BG, fg=FG_COLOR, bd=0, highlightthickness=0, selectbackground=ACCENT_COLOR)
        self.ing_listbox.pack(side="left", fill="both", expand=True)
        self.ing_listbox.bind("<<ListboxSelect>>", self.on_ing_select)
        
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.ing_listbox.yview)
        scroll.pack(side="right", fill="y")
        self.ing_listbox.config(yscrollcommand=scroll.set)
        
        ttk.Button(side_frame, text="+ Create New", command=self.clear_ingredient_form).pack(fill="x", pady=5)
        paned.add(side_frame, weight=1)

        form_frame = ttk.Frame(paned)
        paned.add(form_frame, weight=3)

        self.lbl_ing_header = ttk.Label(form_frame, text="Creating New Ingredient", font=("Arial", 14, "bold"))
        self.lbl_ing_header.pack(pady=10)

        grid = ttk.Frame(form_frame)
        grid.pack(fill="x", padx=20)

        ttk.Label(grid, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.var_ing_name = tk.StringVar()
        ttk.Entry(grid, textvariable=self.var_ing_name).grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Label(grid, text="Container:").grid(row=1, column=0, sticky="w", pady=5)
        self.var_ing_cont = tk.StringVar(value="pot")
        cont_dd = ttk.Combobox(grid, textvariable=self.var_ing_cont, values=["pot", "pan"], state="readonly")
        cont_dd.grid(row=1, column=1, sticky="ew", padx=10)

        t_group = ttk.LabelFrame(form_frame, text="Timers (Frames)")
        t_group.pack(fill="x", padx=20, pady=10)
        
        self.vars_ing_timers = {}
        for i, label in enumerate(["Prepare Time", "Cook Time", "Burn Time"]):
            key = label.lower().replace(" ", "_")
            ttk.Label(t_group, text=label + ":").grid(row=0, column=i*2, padx=5, pady=10)
            var = tk.IntVar(value=100)
            ttk.Entry(t_group, textvariable=var, width=8).grid(row=0, column=i*2+1, padx=5)
            self.vars_ing_timers[key] = var

        c_group = ttk.LabelFrame(form_frame, text="Visuals")
        c_group.pack(fill="x", padx=20, pady=10)
        
        self.color_btns = {}
        labels = {"color_raw": "Raw", "color_chopped": "Chopped", "color_cooked": "Cooked", "color_burnt": "Burnt", "crate_color": "Crate"}
        
        for i, (key, text) in enumerate(labels.items()):
            f = ttk.Frame(c_group)
            f.pack(fill="x", pady=2, padx=5)
            ttk.Label(f, text=text, width=15).pack(side="left")
            btn = tk.Button(f, text="   ", width=10, bg="#ff0000", relief="flat", command=lambda k=key: self.pick_color(k))
            btn.pack(side="left")
            self.color_btns[key] = btn

        save_btn = tk.Button(form_frame, text="SAVE INGREDIENT", bg=ACCENT_COLOR, fg="white", font=("Arial", 10, "bold"), relief="flat", command=self.save_ingredient)
        save_btn.pack(pady=20, fill="x", padx=20)

    # --- TAB 2: RECIPES ---
    def setup_recipe_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Recipes  ")

        paned = ttk.PanedWindow(frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        side = ttk.Frame(paned, width=200)
        ttk.Label(side, text="Recipes List", font=("Arial", 12, "bold")).pack(pady=5)
        self.rec_listbox = tk.Listbox(side, bg=ENTRY_BG, fg=FG_COLOR, bd=0, highlightthickness=0, selectbackground=ACCENT_COLOR)
        self.rec_listbox.pack(fill="both", expand=True)
        self.rec_listbox.bind("<<ListboxSelect>>", self.on_rec_select)
        ttk.Button(side, text="+ Create New", command=self.clear_recipe_form).pack(fill="x", pady=5)
        paned.add(side, weight=1)

        content = ttk.Frame(paned)
        paned.add(content, weight=3)

        self.lbl_rec_header = ttk.Label(content, text="Creating New Recipe", font=("Arial", 14, "bold"))
        self.lbl_rec_header.pack(pady=10)

        h_frame = ttk.Frame(content)
        h_frame.pack(fill="x", padx=20)
        ttk.Label(h_frame, text="Recipe Name:").pack(side="left")
        self.var_rec_name = tk.StringVar()
        ttk.Entry(h_frame, textvariable=self.var_rec_name).pack(side="left", fill="x", expand=True, padx=10)

        builder = ttk.LabelFrame(content, text="Ingredients Builder")
        builder.pack(fill="both", expand=True, padx=20, pady=10)

        b_grid = ttk.Frame(builder)
        b_grid.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(b_grid, text="Available").grid(row=0, column=0)
        self.list_avail = tk.Listbox(b_grid, bg=ENTRY_BG, fg=FG_COLOR, height=15)
        self.list_avail.grid(row=1, column=0, sticky="nsew")

        btn_frame = ttk.Frame(b_grid)
        btn_grid = btn_frame.grid(row=1, column=1, padx=10)
        ttk.Button(btn_frame, text="Add ->", command=self.add_to_rec).pack(pady=5)
        ttk.Button(btn_frame, text="<- Rem", command=self.rem_from_rec).pack(pady=5)

        ttk.Label(b_grid, text="In Recipe").grid(row=0, column=2)
        self.list_in_rec = tk.Listbox(b_grid, bg=ENTRY_BG, fg=FG_COLOR, height=15)
        self.list_in_rec.grid(row=1, column=2, sticky="nsew")

        b_grid.columnconfigure(0, weight=1)
        b_grid.columnconfigure(2, weight=1)

        save_btn = tk.Button(content, text="SAVE RECIPE", bg=ACCENT_COLOR, fg="white", font=("Arial", 10, "bold"), relief="flat", command=self.save_recipe)
        save_btn.pack(pady=10, fill="x", padx=20)

    # --- TAB 3: CONTAINERS ---
    def setup_container_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Containers  ")
        
        paned = ttk.PanedWindow(frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Side List
        side = ttk.Frame(paned, width=200)
        ttk.Label(side, text="Containers", font=("Arial", 12, "bold")).pack(pady=5)
        self.cont_listbox = tk.Listbox(side, bg=ENTRY_BG, fg=FG_COLOR, bd=0, highlightthickness=0, selectbackground=ACCENT_COLOR)
        self.cont_listbox.pack(fill="both", expand=True)
        self.cont_listbox.bind("<<ListboxSelect>>", self.on_cont_select)
        ttk.Button(side, text="+ Create New", command=self.clear_container_form).pack(fill="x", pady=5)
        paned.add(side, weight=1)
        
        # Form
        content = ttk.Frame(paned)
        paned.add(content, weight=3)
        
        self.lbl_cont_header = ttk.Label(content, text="Creating New Container", font=("Arial", 14, "bold"))
        self.lbl_cont_header.pack(pady=10)
        
        grid = ttk.Frame(content)
        grid.pack(fill="x", padx=20)
        
        ttk.Label(grid, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.var_cont_name = tk.StringVar()
        ttk.Entry(grid, textvariable=self.var_cont_name).grid(row=0, column=1, sticky="ew", padx=10)
        
        ttk.Label(grid, text="Visual Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.var_cont_visual = tk.StringVar(value="pot")
        ttk.Combobox(grid, textvariable=self.var_cont_visual, values=["pot", "pan"], state="readonly").grid(row=1, column=1, sticky="ew", padx=10)
        
        ttk.Label(grid, text="Min Items:").grid(row=2, column=0, sticky="w", pady=5)
        self.var_cont_min = tk.IntVar(value=1)
        ttk.Entry(grid, textvariable=self.var_cont_min).grid(row=2, column=1, sticky="ew", padx=10)
        
        ttk.Label(grid, text="Max Items:").grid(row=3, column=0, sticky="w", pady=5)
        self.var_cont_max = tk.IntVar(value=3)
        ttk.Entry(grid, textvariable=self.var_cont_max).grid(row=3, column=1, sticky="ew", padx=10)
        
        save_btn = tk.Button(content, text="SAVE CONTAINER", bg=ACCENT_COLOR, fg="white", font=("Arial", 10, "bold"), relief="flat", command=self.save_container)
        save_btn.pack(pady=20, fill="x", padx=20)

    def on_cont_select(self, event):
        sel = self.cont_listbox.curselection()
        if not sel: return
        name = self.cont_listbox.get(sel[0])
        data = self.data.get("containers", {}).get(name, {})
        self.lbl_cont_header.config(text=f"Editing: {name}")
        self.var_cont_name.set(name)
        self.var_cont_visual.set(data.get("visual_type", "pot"))
        self.var_cont_min.set(data.get("min_items", 1))
        self.var_cont_max.set(data.get("max_items", 1))

    def clear_container_form(self):
        self.lbl_cont_header.config(text="Creating New Container")
        self.var_cont_name.set("")
        self.var_cont_visual.set("pot")
        self.var_cont_min.set(1)
        self.var_cont_max.set(3)
        self.cont_listbox.selection_clear(0, tk.END)

    def save_container(self):
        name = self.var_cont_name.get().strip().lower()
        if not name: return
        
        if "containers" not in self.data: self.data["containers"] = {}
        
        self.data["containers"][name] = {
            "visual_type": self.var_cont_visual.get(),
            "min_items": self.var_cont_min.get(),
            "max_items": self.var_cont_max.get()
        }
        self.save_json(DATA_FILE, self.data)
        self.refresh_ui()

    # --- TAB 4: LEVEL CONFIG (UPDATED) ---
    def setup_level_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Level Config  ")

        # --- FILE SELECTOR ---
        sel_frame = ttk.LabelFrame(frame, text="Select Level File")
        sel_frame.pack(fill="x", padx=10, pady=10)
        
        self.var_level_path = tk.StringVar()
        self.level_dd = ttk.Combobox(sel_frame, textvariable=self.var_level_path, state="readonly")
        self.level_dd.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.level_dd.bind("<<ComboboxSelected>>", self.on_level_changed)
        
        ttk.Button(sel_frame, text="Scan Folders", command=self.update_level_list).pack(side="left", padx=10)

        # --- SAVE BUTTON ---
        header = ttk.Frame(frame)
        header.pack(fill="x", padx=10, pady=5)
        tk.Button(header, text="SAVE LEVEL CONFIG", bg=SUCCESS_COLOR, fg="white", font=("Arial", 10, "bold"), relief="flat", command=self.save_level).pack(side="right")

        # --- SCROLLABLE CONTENT ---
        canvas_frame = ttk.Frame(frame)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.level_rows = {}

        # Fill dropdown initially
        self.update_level_list()
        if self.available_levels:
            self.level_dd.current(0)
            self.on_level_changed(None)

    # --- LOGIC ---

    def update_level_list(self):
        self.available_levels = self.scan_levels()
        self.level_dd['values'] = self.available_levels
        if not self.available_levels:
            self.var_level_path.set("No levels found in /levels")

    def on_level_changed(self, event):
        path = self.var_level_path.get()
        if not path or not os.path.exists(path): return
        
        self.current_level_path = path
        # Load the selected level data
        self.level_data = self.load_json(path, {"objects": [], "recipes": {}})
        
        # Convert legacy if needed
        if isinstance(self.level_data.get("recipes"), list):
            new_recs = {r: [1800, 3600] for r in self.level_data["recipes"]}
            self.level_data["recipes"] = new_recs
            
        self.refresh_level_rows_only()

    def refresh_ui(self):
        # 1. Update Global Lists
        ings = sorted(self.data["ingredients"].keys())
        self.ing_listbox.delete(0, tk.END)
        self.list_avail.delete(0, tk.END)
        for i in ings:
            self.ing_listbox.insert(tk.END, i)
            self.list_avail.insert(tk.END, i)

        recs = sorted(self.data["recipes"].keys())
        self.rec_listbox.delete(0, tk.END)
        for r in recs: self.rec_listbox.insert(tk.END, r)

        conts = sorted(self.data.get("containers", {}).keys())
        if hasattr(self, "cont_listbox"):
            self.cont_listbox.delete(0, tk.END)
            for c in conts: self.cont_listbox.insert(tk.END, c)

        # 2. Update Level Rows
        self.refresh_level_rows_only()

    def refresh_level_rows_only(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.level_rows = {}
        
        if not self.current_level_path: return

        # Header
        h = ttk.Frame(self.scroll_frame)
        h.pack(fill="x", pady=5)
        ttk.Label(h, text="Active", width=10).pack(side="left")
        ttk.Label(h, text="Recipe Name", width=30).pack(side="left")
        ttk.Label(h, text="Min Time (frames)", width=15).pack(side="left")
        ttk.Label(h, text="Max Time (frames)", width=15).pack(side="left")
        ttk.Separator(self.scroll_frame, orient='horizontal').pack(fill='x', pady=5)

        recs = sorted(self.data["recipes"].keys())
        active_data = self.level_data.get("recipes", {})

        for r in recs:
            row = ttk.Frame(self.scroll_frame)
            row.pack(fill="x", pady=2)
            
            is_active = r in active_data
            times = active_data.get(r, [1800, 3600])

            var_active = tk.BooleanVar(value=is_active)
            var_min = tk.IntVar(value=times[0])
            var_max = tk.IntVar(value=times[1])

            ttk.Checkbutton(row, variable=var_active).pack(side="left", padx=15)
            ttk.Label(row, text=r, width=30).pack(side="left")
            ttk.Entry(row, textvariable=var_min, width=10).pack(side="left", padx=10)
            ttk.Entry(row, textvariable=var_max, width=10).pack(side="left", padx=10)

            self.level_rows[r] = {"active": var_active, "min": var_min, "max": var_max}

    # --- INGREDIENT ACTIONS (Unchanged) ---
    def on_ing_select(self, event):
        sel = self.ing_listbox.curselection()
        if not sel: return
        name = self.ing_listbox.get(sel[0])
        data = self.data["ingredients"][name]
        self.lbl_ing_header.config(text=f"Editing: {name}")
        self.var_ing_name.set(name)
        self.var_ing_cont.set(data.get("container_type", "pot"))
        for k, var in self.vars_ing_timers.items(): var.set(data.get(k, 100))
        for k in self.current_ing_colors:
            if k in data: self.current_ing_colors[k] = tuple(data[k])
            self.update_color_btn(k)

    def clear_ingredient_form(self):
        self.lbl_ing_header.config(text="Creating New Ingredient")
        self.var_ing_name.set("")
        self.var_ing_cont.set("pot")
        for var in self.vars_ing_timers.values(): var.set(100)
        self.ing_listbox.selection_clear(0, tk.END)

    def pick_color(self, key):
        c = colorchooser.askcolor(color=self.current_ing_colors[key], title=f"Color for {key}")
        if c[0]:
            self.current_ing_colors[key] = [int(x) for x in c[0]]
            self.update_color_btn(key)

    def update_color_btn(self, key):
        rgb = self.current_ing_colors[key]
        hex_c = '#%02x%02x%02x' % tuple(rgb)
        self.color_btns[key].config(bg=hex_c, activebackground=hex_c)

    def save_ingredient(self):
        name = self.var_ing_name.get().strip().lower()
        if not name: return
        obj = {
            "container_type": self.var_ing_cont.get(),
            "prepare_time": self.vars_ing_timers["prepare_time"].get(),
            "cook_time": self.vars_ing_timers["cook_time"].get(),
            "burn_time": self.vars_ing_timers["burn_time"].get(),
        }
        for k, v in self.current_ing_colors.items(): obj[k] = v
        self.data["ingredients"][name] = obj
        self.save_json(DATA_FILE, self.data)
        self.refresh_ui()

    # --- RECIPE ACTIONS (Unchanged) ---
    def on_rec_select(self, event):
        sel = self.rec_listbox.curselection()
        if not sel: return
        name = self.rec_listbox.get(sel[0])
        self.lbl_rec_header.config(text=f"Editing: {name}")
        self.var_rec_name.set(name)
        self.list_in_rec.delete(0, tk.END)
        for i in self.data["recipes"][name].get("ingredients", []):
            self.list_in_rec.insert(tk.END, i)

    def clear_recipe_form(self):
        self.lbl_rec_header.config(text="Creating New Recipe")
        self.var_rec_name.set("")
        self.list_in_rec.delete(0, tk.END)
        self.rec_listbox.selection_clear(0, tk.END)

    def add_to_rec(self):
        sel = self.list_avail.curselection()
        if sel: self.list_in_rec.insert(tk.END, self.list_avail.get(sel[0]))

    def rem_from_rec(self):
        sel = self.list_in_rec.curselection()
        if sel: self.list_in_rec.delete(sel[0])

    def save_recipe(self):
        name = self.var_rec_name.get().strip().lower()
        if not name: return
        ings = list(self.list_in_rec.get(0, tk.END))
        if not ings:
            messagebox.showerror("Error", "Recipe cannot be empty")
            return
        self.data["recipes"][name] = {"ingredients": ings}
        self.save_json(DATA_FILE, self.data)
        self.refresh_ui()

    # --- LEVEL ACTIONS ---
    def save_level(self):
        if not self.current_level_path:
            messagebox.showerror("Error", "No level file selected!")
            return

        new_config = {}
        for name, vars_ in self.level_rows.items():
            if vars_["active"].get():
                try:
                    mn = vars_["min"].get()
                    mx = vars_["max"].get()
                    new_config[name] = [mn, mx]
                except:
                    messagebox.showerror("Error", f"Invalid time for {name}")
                    return
        
        self.level_data["recipes"] = new_config
        self.save_json(self.current_level_path, self.level_data)
        messagebox.showinfo("Success", f"Saved config to {self.current_level_path}!")

if __name__ == "__main__":
    app = DarkLevelEditor()
    app.run()
