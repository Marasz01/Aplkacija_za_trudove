import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pygame

class TrudoviApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacija za praćenje trudova")
        self.root.geometry("800x600")
        self.style = ttk.Style()
        self.style.theme_use("vista")  # Standardna Windows tema

        self.trudovi = []
        self.start_time = None
        self.running = False

        # Postavi SQLite bazu podataka
        self.conn = sqlite3.connect("trudovi.db")
        self.create_table()

        # Sučelje
        self.setup_ui()

        # Inicijaliziraj pygame za muziku
        pygame.mixer.init()

    def setup_ui(self):
        # Glavni okvir
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Status trudova
        self.label_status = ttk.Label(main_frame, text="Status: Nema aktivnih trudova", font=("Arial", 14))
        self.label_status.pack(pady=10)

        # Indikator boje
        self.label_boja = ttk.Label(main_frame, text="", font=("Arial", 18), width=20, style="TLabel")
        self.label_boja.pack(pady=20)

        # Gumbi
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.button_start = ttk.Button(button_frame, text="Počni mjeriti trud", command=self.start_trud)
        self.button_start.pack(side=tk.LEFT, padx=5)

        self.button_stop = ttk.Button(button_frame, text="Zaustavi mjerenje", command=self.stop_trud, state=tk.DISABLED)
        self.button_stop.pack(side=tk.LEFT, padx=5)

        self.button_reset = ttk.Button(button_frame, text="Resetuj", command=self.reset)
        self.button_reset.pack(side=tk.LEFT, padx=5)

        # Graf
        self.figure, self.ax = plt.subplots(figsize=(6, 3))
        self.canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        self.canvas.get_tk_widget().pack(pady=20)

        # Opcije za opuštanje
        self.button_music = ttk.Button(main_frame, text="Reproduciraj opuštajuću muziku", command=self.play_music)
        self.button_music.pack(pady=10)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trudovi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def start_trud(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.button_start.config(state=tk.DISABLED)
            self.button_stop.config(state=tk.NORMAL)
            self.label_status.config(text="Status: Mjerenje u toku")
            self.thread = threading.Thread(target=self.mjeri_trud)
            self.thread.start()

    def stop_trud(self):
        if self.running:
            self.running = False
            end_time = time.time()
            duration = end_time - self.start_time
            self.trudovi.append(duration)
            self.save_to_db(duration)
            self.button_start.config(state=tk.NORMAL)
            self.button_stop.config(state=tk.DISABLED)
            self.label_status.config(text="Status: Mjerenje zaustavljeno")
            self.azuriraj_informacije()
            self.provjeri_trudove()
            self.update_graph()

    def save_to_db(self, duration):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO trudovi (duration) VALUES (?)", (int(duration),))
        self.conn.commit()

    def update_graph(self):
        self.ax.clear()
        self.ax.plot(self.trudovi, marker="o", color="blue")
        self.ax.set_title("Učestalost trudova")
        self.ax.set_xlabel("Broj trudova")
        self.ax.set_ylabel("Trajanje (s)")
        self.canvas.draw()

    def provjeri_trudove(self):
        if len(self.trudovi) >= 3:
            prosjek = sum(self.trudovi[-3:]) / 3
            if prosjek < 300:  # Ako su trudovi češći od svakih 5 minuta
                self.label_boja.config(style="Red.TLabel", text="Hitno idite u bolnicu!")
                self.alarm()
            elif prosjek < 600:  # Ako su trudovi češći od svakih 10 minuta
                self.label_boja.config(style="Green.TLabel", text="Vrijeme je za porod!")
            else:
                self.label_boja.config(style="Yellow.TLabel", text="Nije vrijeme za porod.")

    def alarm(self):
        messagebox.showwarning("Alarm", "Hitno idite u bolnicu! Porađate se.")
        self.play_music("alarm.mp3")  # Dodaj alarm.mp3 u assets folder

    def play_music(self, file="relaxing_music.mp3"):
        pygame.mixer.music.load(f"assets/{file}")
        pygame.mixer.music.play()

    def reset(self):
        self.trudovi = []
        self.label_boja.config(text="", style="TLabel")
        self.label_status.config(text="Status: Nema aktivnih trudova")
        self.update_graph()

if __name__ == "__main__":
    root = tk.Tk()
    app = TrudoviApp(root)
    root.mainloop()