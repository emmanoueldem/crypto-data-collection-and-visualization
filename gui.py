import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
import json
import os
from datetime import datetime, timedelta
import matplotlib.dates as mdates

CACHE_PATH = os.path.join("data", "cache.json")

class CryptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Live Chart")
        self.root.geometry("900x650")

        self.selected_coin = tk.StringVar()
        self.data_history = {}
        self.plot_thread = None
        self.running = False

        # UI Components
        self.dropdown = ttk.Combobox(root, textvariable=self.selected_coin, state="readonly")
        self.dropdown.pack(pady=10)

        self.plot_button = ttk.Button(root, text="Εμφάνιση Γραφήματος", command=self.start_live_plot)
        self.plot_button.pack(pady=5)

        self.stats_label = tk.Label(root, text="", font=("Arial", 10))
        self.stats_label.pack(pady=5)

        self.fig = Figure(figsize=(8, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        # Load initial data
        self.update_dropdown_options()

    def load_cached_data(self):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print("❌ Error loading cache:", e)
            return []

    def update_dropdown_options(self):
        data = self.load_cached_data()
        if data:
            coin_names = [coin['Name'] for coin in data]
            self.dropdown['values'] = coin_names
            if not self.selected_coin.get() and coin_names:
                self.selected_coin.set(coin_names[0])
        else:
            print("⚠️ Δεν υπάρχουν δεδομένα στην cache.")

    def start_live_plot(self):
        self.plot_button.config(state=tk.DISABLED)

        if self.plot_thread and self.plot_thread.is_alive():
            self.running = False
            self.plot_thread.join()

        self.running = True
        selected = self.selected_coin.get()
        self.data_history[selected] = []
        self.plot_thread = threading.Thread(target=self.update_plot_loop, args=(selected,), daemon=True)
        self.plot_thread.start()

        self.root.after(1000, lambda: self.plot_button.config(state=tk.NORMAL))

    def update_plot_loop(self, coin):
        while self.running:
            data = self.load_cached_data()
            now = datetime.now()

            row = next((item for item in data if item['Name'] == coin), None)
            if row:
                price = row['Price (USD)']
                self.data_history.setdefault(coin, []).append((now, price))

                # Remove entries older than 5 minutes
                five_minutes_ago = now - timedelta(minutes=5)
                self.data_history[coin] = [entry for entry in self.data_history[coin] if entry[0] >= five_minutes_ago]

                if len(self.data_history[coin]) < 2:
                    time.sleep(2)
                    continue

                self.ax.clear()
                times, prices = zip(*self.data_history[coin])

                color = 'green' if prices[-1] >= prices[0] else 'red'

                self.ax.plot(times, prices, marker='o', color=color)
                self.ax.set_title(f"Τιμή {coin} σε Πραγματικό Χρόνο")
                self.ax.set_ylabel("USD")
                self.ax.set_xlabel("Ώρα")

                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                self.ax.tick_params(axis='x', rotation=45)
                self.ax.ticklabel_format(style='plain', axis='y')
                self.ax.grid(True, linestyle='--', alpha=0.5)

                price_range = max(prices) - min(prices)
                if price_range > 0:
                    margin = price_range * 0.2
                    self.ax.set_ylim(min(prices) - margin, max(prices) + margin)
                else:
                    self.ax.set_ylim(prices[0] - 1, prices[0] + 1)

                avg_price = sum(prices) / len(prices)
                stats_text = f"📈 Τελευταία: ${prices[-1]:,.4f} | Ελάχιστο (5'): ${min(prices):,.4f} | Μέγιστο (5'): ${max(prices):,.4f} | Μέσος Όρος (5'): ${avg_price:,.4f}"
                self.stats_label.config(text=stats_text)

                self.fig.tight_layout()
                self.canvas.draw()

            time.sleep(2)

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoGUI(root)
    root.mainloop()
