import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel
import time
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pygame
from datetime import datetime
import pytz

class TrudoviApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacija za praćenje trudova")
        self.root.geometry("1000x600")
        
        # Inicijalizacija
        self.trudovi = []
        self.start_time = None
        self.running = False
        self.stopwatch_running = False
        
        # Baza podataka
        self.conn = sqlite3.connect("trudovi.db")
        self.create_table()
        
        # Sučelje
        self.setup_ui()
        
        # Inicijalizacija pygame za muziku
        pygame.mixer.init()
        
        # Postavi graf
        self.setup_graph()
        
        # Ažuriranje lokalnog vremena
        self.update_local_time()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.local_time_label = ttk.Label(main_frame, text="Lokalno vrijeme:", font=("Arial", 12))
        self.local_time_label.pack(pady=10)

        self.stopwatch_label = ttk.Label(main_frame, text="Trajanje truda: 0.0 s", font=("Arial", 14))
        self.stopwatch_label.pack(pady=10)

        self.label_status = ttk.Label(main_frame, text="Status: Nema aktivnih trudova", font=("Arial", 14))
        self.label_status.pack(pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.button_start = ttk.Button(button_frame, text="Počni mjeriti", command=self.start_trud, bootstyle=SUCCESS)
        self.button_start.pack(side=tk.LEFT, padx=5)

        self.button_stop = ttk.Button(button_frame, text="Zaustavi", command=self.stop_trud, bootstyle=DANGER, state=tk.DISABLED)
        self.button_stop.pack(side=tk.LEFT, padx=5)

        self.button_reset = ttk.Button(button_frame, text="Resetuj", command=self.reset, bootstyle=INFO)
        self.button_reset.pack(side=tk.LEFT, padx=5)

        self.button_history = ttk.Button(button_frame, text="Povijest", command=self.show_history, bootstyle=WARNING)
        self.button_history.pack(side=tk.LEFT, padx=5)
        
        self.setup_graph()

        self.button_music = ttk.Button(main_frame, text="Opuštajuća muzika", command=self.play_music, bootstyle=WARNING)
        self.button_music.pack(pady=10)
    
    def setup_graph(self):
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot([], [], color="red", linewidth=2)
        self.ax.set_title("Kumulativno trajanje trudova")
        self.ax.set_xlabel("Broj trudova")
        self.ax.set_ylabel("Trajanje (s)")
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(pady=20)
    
    def start_trud(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.button_start.config(state=tk.DISABLED)
            self.button_stop.config(state=tk.NORMAL)
            self.label_status.config(text="Status: Mjerenje u toku")
            self.stopwatch_running = True
            self.update_stopwatch()
    
    def stop_trud(self):
        if self.running:
            self.running = False
            self.stopwatch_running = False
            duration = time.time() - self.start_time
            self.trudovi.append(duration)
            self.save_to_db(duration)
            self.button_start.config(state=tk.NORMAL)
            self.button_stop.config(state=tk.DISABLED)
            self.label_status.config(text="Status: Mjerenje zaustavljeno")
            self.update_graph()
    
    def reset(self):
        self.trudovi = []
        self.label_status.config(text="Status: Nema aktivnih trudova")
        self.update_graph()
    
    def update_graph(self):
        self.ax.clear()
        self.ax.set_title("Kumulativno trajanje trudova")
        self.ax.set_xlabel("Broj trudova")
        self.ax.set_ylabel("Trajanje (s)")
        if self.trudovi:
            self.ax.plot(range(1, len(self.trudovi) + 1), self.trudovi, color="red", linewidth=2)
        self.canvas.draw()
    
    def save_to_db(self, duration):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO trudovi (duration, timestamp) VALUES (?, CURRENT_TIMESTAMP)", (duration,))
        self.conn.commit()
    
    def show_history(self):
        history_window = Toplevel(self.root)
        history_window.title("Povijest trudova")
        history_window.geometry("600x400")

        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp, duration FROM trudovi ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        columns = ("#1", "#2")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")
        tree.heading("#1", text="Vrijeme")
        tree.heading("#2", text="Trajanje (s)")
        tree.pack(fill=tk.BOTH, expand=True)

        for row in rows:
            tree.insert("", tk.END, values=row)
    
    def play_music(self):
        pygame.mixer.music.load("assets/relaxing_music.mp3")
        pygame.mixer.music.play()
    
    def update_stopwatch(self):
        if self.stopwatch_running:
            elapsed_time = time.time() - self.start_time
            self.stopwatch_label.config(text=f"Trajanje truda: {elapsed_time:.1f} s")
            self.root.after(100, self.update_stopwatch)
    
    def update_local_time(self):
        local_time = datetime.now(pytz.timezone("Europe/Zagreb"))
        self.local_time_label.config(text=f"Lokalno vrijeme: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.root.after(1000, self.update_local_time)

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = TrudoviApp(root)
    root.mainloop()
