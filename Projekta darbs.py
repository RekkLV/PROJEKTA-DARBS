import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

# Datubāzes darbības
class DatabaseManager:
    """ Klase, kas pārvalda datubāzi  """
    def __init__(self, db_name="games.db"):
        self.db_name = db_name
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS developers ( 
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE)''') # Izstrādātāju tabula
    
        cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        image_path TEXT,
                        developer_id INTEGER,
                        FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL)''') # Spēļu tabula
        conn.commit()
        conn.close()

    def add_developer(self, name): # Pievieno izstrādātāju datubāzei
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO developers (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.IntegrityError: # Izstrādātājs jau eksistē
            pass 
        conn.close()

    def remove_developer(self, dev_id): # Izdzēš izstrādātāju no datubāzes
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM developers WHERE id = ?", (dev_id,))
        conn.commit()
        conn.close()
        

    def get_developers(self): # Atgriež visus izstrādātājus
        conn = self.connect()
        cursor = conn.cursor()
        cursor = conn.execute("SELECT id, name FROM developers")
        developers = cursor.fetchall()
        conn.close()
        return developers

    def add_game(self, title, image_path, developer_id): # Pievieno spēli datubāzei
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO games (title, image_path, developer_id) VALUES (?, ?, ?)", (title, image_path, developer_id))
        conn.commit()
        conn.close()
        

    def remove_game(self, game_id): # Izdzēš spēli no datubāzes
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
        conn.commit()
        conn.close()
        

    def get_games(self, query=None): # Ielādē visas spēles no datubāzes
        conn = self.connect()
        cursor = conn.cursor()
        if query and query.strip():
            cursor.execute("""SELECT games.id, games.title, games.image_path, developers.name
                            FROM games
                            LEFT JOIN developers ON games.developer_id = developers.id
                            WHERE games.title LIKE ?""", (f'%{query.strip()}%',))
        else:
            cursor.execute("""SELECT games.id, games.title, games.image_path, developers.name
                            FROM games
                            LEFT JOIN developers ON games.developer_id = developers.id""")
        games = cursor.fetchall()
        conn.close()
        return games
    
class GameCollectionApp:
    """Klase GUI izveidei"""
    def __init__(self, root): # GUI izveide
        self.root = root
        root.title("Game Collection")
        root.geometry("600x550") # Loga izmērs
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_games()
        
    
    def setup_ui(self):
        # Filtrēšanas rāmītis
        self.filter_frame = ttk.Frame(self.root, padding=10)
        self.filter_frame.pack(side="top", fill="x")
        ttk.Label(self.filter_frame, text="Filter by Title:").pack(side="left")
        self.search_entry = ttk.Entry(self.filter_frame)
        self.search_entry.pack(side="left", padx=(5,5))
        ttk.Button(self.filter_frame, text="Filter", command=self.filter_games).pack(side="left", padx=(5,5))
        ttk.Button(self.filter_frame, text="Clear Filter", command=self.clear_filter).pack(side="left")
        
        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.menu_bar.add_command(label="Add Game", command=self.add_game_popup)
        self.menu_bar.add_command(label="Add Developer", command=self.add_developer_popup)
        self.menu_bar.add_command(label="Manage Developers", command=self.manage_devs)    
        self.menu_bar.add_command(label="About", command=self.about_popup)
        self.menu_bar.add_command(label="Exit", command=self.root.quit)

        # Canva, Scrollbar un Frame
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def open_file(self): # Atver failu izvēlni
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        return file_path
    
    def load_games(self, query=None): # Ielādē visas spēles no datubāzes
        for widget in self.frame.winfo_children():
            widget.destroy()
        games = self.db.get_games(query)
        for idx, (game_id, title, image_path, dev_name) in enumerate(games):
            try:
                img = Image.open(image_path)
                img = img.resize((100, 150))
                img = ImageTk.PhotoImage(img)
            except:
                img = tk.PhotoImage(width=100, height=150)
        
            frame_card = ttk.Frame(self.frame, padding=5, relief="ridge")
            frame_card.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)
            label_img = tk.Label(frame_card, image=img)
            label_img.image = img  # Saglabā attēlu atmiņā
            label_img.pack()
            label_title = tk.Label(frame_card, text=title)
            label_title.pack()
            if dev_name:
                label_dev = tk.Label(frame_card, text = f"Developer: {dev_name}", font=(None, 8, 'italic'))
                label_dev.pack()
            btn_delete = ttk.Button(frame_card, text="Remove", command=lambda gid=game_id: self.remove_game(gid))
            btn_delete.pack()
    
    def remove_game(self, game_id):
        self.db.remove_game(game_id)
        self.load_games()

    def add_game_popup(self): # Pievieno spēli
        popup = tk.Toplevel(self.root)
        popup.title("Add Game")
        ttk.Label(popup, text="Game Title:").pack(pady=(10,0))
        entry_title = ttk.Entry(popup)
        entry_title.pack(pady=(0,10))

        ttk.Label(popup, text="Izvēlaties izstrādātāju:").pack(pady=(0,0))
        developers = self.db.get_developers()
        dev_options = [dev[1]for dev in developers]
        dev_var = tk.StringVar()
        combo_dev = ttk.Combobox(popup, textvariable=dev_var, values=["None"] + dev_options,state="readonly")
        combo_dev.current(0)
        combo_dev.pack(pady=(0,10))

        def save_game(): # Saglabā spēli
            title = entry_title.get()
            image_path = self.open_file()
            dev_selection = combo_dev.get()
            developer_id = None
            if dev_selection != "None":
                for dev in developers:
                    if dev[1] == dev_selection:
                        developer_id = dev[0]
                        break
            if title and image_path:
                self.db.add_game(title, image_path, developer_id)
                popup.destroy()
                self.load_games()
    
        ttk.Button(popup, text="Choose Image & Save", command=save_game).pack()

    def add_developer_popup(self): # Pievieno izstrādātāju
        popup = tk.Toplevel(self.root)
        popup.title("Pievienot izstrādātāju")
        ttk.Label(popup, text="Izstrādātāja nosaukums:").pack(pady=(10,0))
        entry_dev = ttk.Entry(popup)
        entry_dev.pack(pady=(0,10))

        def save_developer():
            name = entry_dev.get()
            if name:
                self.db.add_developer(name)
                popup.destroy()
        ttk.Button(popup, text= "Saglabāt", command=save_developer).pack(pady=(0,10))

    def manage_devs(self):
        popup = tk.Toplevel(self.root)
        popup.title("Pārvaldīt izstrādātājus")
        list_frame = ttk.Frame(popup, padding=10)
        list_frame.pack(fill="both", expand=True)

        developers = self.db.get_developers()
        for dev in developers:
            dev_id, name = dev
            frame_dev = ttk.Frame(list_frame, padding=5, relief="ridge")
            frame_dev.pack(fill="x", pady=5) 
            ttk.Label(frame_dev, text=name).pack(side="left", padx=5)
            btn_remove = ttk.Button(frame_dev, text="Noņemt", command=lambda did=dev_id: self.remove_dev_refresh(did, popup))
            btn_remove.pack(side="right", padx=5)

    def remove_dev_refresh(self, dev_id, window):
        self.db.remove_developer(dev_id)
        window.destroy()
        self.manage_devs()
        self.load_games()


    def about_popup(self): # Par programmu
        tk.messagebox.showinfo("About", "Datorspēļu kolekcijas pārvaldnieka programmatūra.\nVeidoja Renārs Gricjus, Jēkabs Kūms un Kristiāns Kalniņš, 12.a, ZMGV, 2024./2025.")

    def filter_games(self):
        query = self.search_entry.get()
        self.load_games(query)

    def clear_filter(self):
        self.search_entry.delete(0, tk.END)
        self.load_games()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameCollectionApp(root)
    root.mainloop()


