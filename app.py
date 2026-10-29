"""
Historical Stock Yield Optimization System (GUI)
Design technique: Divide-and-Conquer (Maximum Subarray)
Run:  python app.py
"""
import csv
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from algorithm import max_profit

SAMPLE = "100, 113, 110, 85, 105, 102, 86, 63, 81, 101, 94, 106, 101, 79, 94, 90, 97"


def parse_prices(text):
    """Accepts numbers separated by commas, spaces, or new lines."""
    tokens = [t for t in re.split(r"[,\s;]+", text.strip()) if t]
    if len(tokens) < 2:
        raise ValueError("Enter at least 2 prices.")
    try:
        prices = [float(t) for t in tokens]
    except ValueError:
        raise ValueError("Prices must be numbers only (e.g. 100, 113, 110).")
    if any(p <= 0 for p in prices):
        raise ValueError("Prices must be greater than zero.")
    return prices


def load_csv_prices(path):
    """Reads a 'Close' column if present, otherwise the last numeric column."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise ValueError("The CSV file is empty.")
    header = [h.strip().lower() for h in rows[0]]
    col = header.index("close") if "close" in header else len(rows[0]) - 1
    values = []
    for row in rows[1:] if "close" in header or not _is_number(rows[0][col]) else rows:
        if col < len(row) and _is_number(row[col]):
            values.append(row[col].strip())
    return ", ".join(values)


def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Historical Stock Yield Optimization System")
        self.geometry("980x680")
        self.minsize(900, 600)
        self.prices = []
        self.result = None
        self._build()

    # ---------- UI ----------
    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Daily closing prices (comma, space, or new-line separated):",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.input = tk.Text(top, height=4, wrap="word", font=("Consolas", 10))
        self.input.pack(fill="x", pady=4)
        self.input.insert("1.0", SAMPLE)

        btns = ttk.Frame(top)
        btns.pack(fill="x")
        ttk.Button(btns, text="Find Best Buy/Sell Days", command=self.analyze).pack(side="left")
        ttk.Button(btns, text="Load CSV...", command=self.load_csv).pack(side="left", padx=6)
        ttk.Button(btns, text="Use Sample", command=self.use_sample).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.clear).pack(side="left", padx=6)

        self.summary = ttk.Label(self, text="Enter prices and press the button.",
                                 font=("Segoe UI", 12, "bold"), padding=(10, 6))
        self.summary.pack(fill="x")

        mid = ttk.Frame(self, padding=(10, 0))
        mid.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(mid, height=260, bg="white", highlightthickness=1,
                                highlightbackground="#bbb")
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda e: self.draw_chart())

        ttk.Label(self, text="Divide-and-Conquer trace (divide, conquer, combine):",
                  padding=(10, 8, 10, 0)).pack(anchor="w")
        box = ttk.Frame(self, padding=(10, 0, 10, 10))
        box.pack(fill="both", expand=True)
        self.trace = tk.Text(box, height=8, font=("Consolas", 9), state="disabled")
        sb = ttk.Scrollbar(box, command=self.trace.yview)
        self.trace.configure(yscrollcommand=sb.set)
        self.trace.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ---------- actions ----------
    def use_sample(self):
        self.input.delete("1.0", "end")
        self.input.insert("1.0", SAMPLE)

    def clear(self):
        self.input.delete("1.0", "end")
        self.prices, self.result = [], None
        self.summary.config(text="Enter prices and press the button.")
        self.set_trace("")
        self.draw_chart()

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            text = load_csv_prices(path)
            self.input.delete("1.0", "end")
            self.input.insert("1.0", text)
            self.analyze()
        except Exception as e:
            messagebox.showerror("Could not read CSV", str(e))

    def analyze(self):
        try:
            self.prices = parse_prices(self.input.get("1.0", "end"))
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.result = max_profit(self.prices)
        r = self.result
        if r.buy_day is None:
            self.summary.config(text="No profitable trade: prices never rise. Best action: do not trade.")
        else:
            pct = r.profit / r.buy_price * 100
            self.summary.config(
                text=f"Buy on Day {r.buy_day} at {r.buy_price:,.2f}  |  Sell on Day {r.sell_day} "
                     f"at {r.sell_price:,.2f}  |  Profit: {r.profit:,.2f} ({pct:.1f}%)")
        self.set_trace("\n".join(r.trace))
        self.draw_chart()

    def set_trace(self, text):
        self.trace.config(state="normal")
        self.trace.delete("1.0", "end")
        self.trace.insert("1.0", text)
        self.trace.config(state="disabled")

    # ---------- chart ----------
    def draw_chart(self):
        c = self.canvas
        c.delete("all")
        if not self.prices:
            return
        w, h = c.winfo_width(), c.winfo_height()
        pad_l, pad_r, pad_t, pad_b = 55, 20, 20, 30
        lo, hi = min(self.prices), max(self.prices)
        span = (hi - lo) or 1
        n = len(self.prices)

        def x(i):
            return pad_l + (w - pad_l - pad_r) * (i / (n - 1))

        def y(p):
            return h - pad_b - (h - pad_t - pad_b) * ((p - lo) / span)

        c.create_line(pad_l, pad_t, pad_l, h - pad_b, fill="#888")
        c.create_line(pad_l, h - pad_b, w - pad_r, h - pad_b, fill="#888")
        for k in range(5):
            val = lo + span * k / 4
            c.create_text(pad_l - 6, y(val), text=f"{val:,.0f}", anchor="e", font=("Segoe UI", 8))
            c.create_line(pad_l, y(val), w - pad_r, y(val), fill="#eee")

        step = max(1, n // 12)
        for i in range(0, n, step):
            c.create_text(x(i), h - pad_b + 12, text=str(i + 1), font=("Segoe UI", 8))

        pts = [coord for i, p in enumerate(self.prices) for coord in (x(i), y(p))]
        c.create_line(*pts, fill="#2563eb", width=2)

        r = self.result
        if r and r.buy_day:
            bi, si = r.buy_day - 1, r.sell_day - 1
            c.create_rectangle(x(bi), pad_t, x(si), h - pad_b, fill="#dcfce7", outline="", stipple="gray25")
            c.create_oval(x(bi) - 6, y(r.buy_price) - 6, x(bi) + 6, y(r.buy_price) + 6, fill="#16a34a")
            c.create_oval(x(si) - 6, y(r.sell_price) - 6, x(si) + 6, y(r.sell_price) + 6, fill="#dc2626")
            c.create_text(x(bi), y(r.buy_price) + 16, text=f"BUY D{r.buy_day}", fill="#16a34a",
                          font=("Segoe UI", 9, "bold"))
            c.create_text(x(si), y(r.sell_price) - 14, text=f"SELL D{r.sell_day}", fill="#dc2626",
                          font=("Segoe UI", 9, "bold"))


if __name__ == "__main__":
    App().mainloop()
