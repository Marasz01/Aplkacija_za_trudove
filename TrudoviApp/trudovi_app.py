import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel
import time
import threading
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pygame
from datetime import datetime
import pytz  # Dodano za podršku vremenskih zona

class TrudoviApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacija za praćenje trudova")
        self.root.geometry("1000x600")

        self.texts = {
            "title": "Aplikacija za praćenje trudova",
            "status_no_contractions": "Status: Nema aktivnih trudova",
            "status_measuring": "Status: Mjerenje u toku",
            "status_stopped": "Status: Mjerenje zaustavljeno",
            "start_button": "Počni mjeriti trud",
            "stop_button": "Zaustavi mjerenje",
            "reset_button": "Resetuj",
            "info_label": "Informacije o trudovima:",
            "music_button": "Reproduciraj opuštajuću muziku",
            "yellow_text": "Nije vrijeme za porod",
            "green_text": "Vrijeme je za porod!",
            "red_text": "Hitno idite u bolnicu!",
            "alarm_message": "Hitno idite u bolnicu! Porađate se.",
            "history_button": "Povijest trudova",
            "history_title": "Povijest trudova",
            "history_time": "Vrijeme",
            "history_duration": "Trajanje (s)",
            "history_status": "Status",
            "false_alarm": "Lažni trud",
            "hospital_needed": "Potreban odlazak u bolnicu",
            "stopwatch_label": "Trajanje truda: 0.0 s",
            "local_time_label": "Lokalno vrijeme:"
        }

        self.trudovi = []
        self.start_time = None
        self.running = False
        self.stopwatch_running = False

        # Postavi SQLite bazu podataka
        self.conn = sqlite3.connect("trudovi.db")
        self.create_table()

        # Sučelje
        self.setup_ui()

        # Inicijaliziraj pygame za muziku
        pygame.mixer.init()

        # Postavi graf
        self.setup_graph()

        # Pokreni ažuriranje lokalnog vremena
        self.update_local_time()

    def setup_ui(self):
        # Glavni okvir
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Lokalno vrijeme
        self.local_time_label = ttk.Label(main_frame, text=self.texts["local_time_label"], font=("Arial", 12))
        self.local_time_label.pack(pady=10)

        # Štoperica
        self.stopwatch_label = ttk.Label(main_frame, text=self.texts["stopwatch_label"], font=("Arial", 14))
        self.stopwatch_label.pack(pady=10)

        # Status trudova
        self.label_status = ttk.Label(main_frame, text=self.texts["status_no_contractions"], font=("Arial", 14))
        self.label_status.pack(pady=10)

        # Indikator boje
        self.label_boja = ttk.Label(main_frame, text="", font=("Arial", 18), width=20)
        self.label_boja.pack(pady=20)

        # Gumbi
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.button_start = ttk.Button(button_frame, text=self.texts["start_button"], command=self.start_trud, bootstyle=SUCCESS)
        self.button_start.pack(side=tk.LEFT, padx=5)

        self.button_stop = ttk.Button(button_frame, text=self.texts["stop_button"], command=self.stop_trud, bootstyle=DANGER, state=tk.DISABLED)
        self.button_stop.pack(side=tk.LEFT, padx=5)

        self.button_reset = ttk.Button(button_frame, text=self.texts["reset_button"], command=self.reset, bootstyle=INFO)
        self.button_reset.pack(side=tk.LEFT, padx=5)

        self.button_history = ttk.Button(button_frame, text=self.texts["history_button"], command=self.show_history, bootstyle=WARNING)
        self.button_history.pack(side=tk.LEFT, padx=5)

        # Graf
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot([], [], color="red", linewidth=2)
        self.ax.set_title("Kumulativno trajanje trudova")
        self.ax.set_xlabel("Broj trudova")
        self.ax.set_ylabel("Trajanje (s)")
        self.canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        self.canvas.get_tk_widget().pack(pady=20)

        # Opcije za opuštanje
        self.button_music = ttk.Button(main_frame, text=self.texts["music_button"], command=self.play_music, bootstyle=WARNING)
        self.button_music.pack(pady=10)

    def setup_graph(self):
        # Inicijaliziraj graf
        self.x_data = []
        self.y_data = []
        self.update_graph()

    def update_graph(self):
        # Ažuriraj graf s novim podacima
        if self.running:
            self.x_data.append(len(self.trudovi) + 1)
            self.y_data.append(sum(self.trudovi))
            self.line.set_data(self.x_data, self.y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

        # Ponovi ažuriranje nakon 500 ms
        self.root.after(500, self.update_graph)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trudovi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        """)
        self.conn.commit()

    def start_trud(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.button_start.config(state=tk.DISABLED)
            self.button_stop.config(state=tk.NORMAL)
            self.label_status.config(text=self.texts["status_measuring"])
            self.stopwatch_running = True
            self.update_stopwatch()
            self.animate_start()

    def stop_trud(self):
        if self.running:
            self.running = False
            self.stopwatch_running = False
            end_time = time.time()
            duration = end_time - self.start_time
            self.trudovi.append(duration)
            status = self.determine_status(duration)
            self.save_to_db(duration, status)
            self.button_start.config(state=tk.NORMAL)
            self.button_stop.config(state=tk.DISABLED)
            self.label_status.config(text=self.texts["status_stopped"])
            self.provjeri_trudove()
            self.animate_stop()

    def animate_start(self):
        # Animacija za pokretanje truda
        self.label_status.config(bootstyle=SUCCESS)
        self.label_boja.config(bootstyle=SUCCESS)
        self.root.after(100, self.animate_start)

    def animate_stop(self):
        # Animacija za zaustavljanje truda
        self.label_status.config(bootstyle=DANGER)
        self.label_boja.config(bootstyle=DANGER)
        self.root.after(100, self.animate_stop)

    def determine_status(self, duration):
        if duration < 300:  # Ako je trud kraći od 5 minuta
            return self.texts["false_alarm"]
        elif duration < 600:  # Ako je trud kraći od 10 minuta
            return self.texts["hospital_needed"]
        else:
            return self.texts["false_alarm"]

    def save_to_db(self, duration, status):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO trudovi (duration, status) VALUES (?, ?)", (duration, status))
        self.conn.commit()

    def provjeri_trudove(self):
        if len(self.trudovi) >= 5:
            prosjek = sum(self.trudovi[-5:]) / 5
            if prosjek < 300:  # Ako su trudovi češći od svakih 5 minuta
                self.label_boja.config(text=self.texts["red_text"], bootstyle=DANGER)
                self.alarm()
            elif prosjek < 600:  # Ako su trudovi češći od svakih 10 minuta
                self.label_boja.config(text=self.texts["green_text"], bootstyle=SUCCESS)
            else:
                self.label_boja.config(text=self.texts["yellow_text"], bootstyle=WARNING)

    def alarm(self):
        messagebox.showwarning("Upozorenje", self.texts["alarm_message"])
        self.play_music("alarm.mp3")  # Dodaj alarm.mp3 u assets folder

    def play_music(self, file="relaxing_music.mp3"):
        pygame.mixer.music.load(f"assets/{file}")
        pygame.mixer.music.play()

    def reset(self):
        self.trudovi = []
        self.x_data = []
        self.y_data = []
        self.label_boja.config(text="", bootstyle=DEFAULT)
        self.label_status.config(text=self.texts["status_no_contractions"])
        self.update_graph()

    def update_stopwatch(self):
        if self.stopwatch_running:
            elapsed_time = time.time() - self.start_time
            self.stopwatch_label.config(text=f"Trajanje truda: {elapsed_time:.1f} s")
            self.root.after(100, self.update_stopwatch)

    def update_local_time(self):
        # Dohvati trenutno lokalno vrijeme
        local_time = datetime.now(pytz.timezone("Europe/Zagreb"))
        self.local_time_label.config(text=f"{self.texts['local_time_label']} {local_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Ponovi ažuriranje svake sekunde
        self.root.after(1000, self.update_local_time)

    def show_history(self):
        # Otvori novi prozor s poviješću trudova
        history_window = Toplevel(self.root)
        history_window.title(self.texts["history_title"])
        history_window.geometry("600x400")

        # Prikaz podataka iz baze
        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp, duration, status FROM trudovi ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        # Tablica za prikaz podataka
        columns = ("#1", "#2", "#3")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")
        tree.heading("#1", text=self.texts["history_time"])
        tree.heading("#2", text=self.texts["history_duration"])
        tree.heading("#3", text=self.texts["history_status"])
        tree.pack(fill=tk.BOTH, expand=True)

        for row in rows:
            tree.insert("", tk.END, values=row)

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")  # Postavi temu na "superhero"
    app = TrudoviApp(root)
    root.mainloop()