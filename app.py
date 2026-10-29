"""StockYield: historical stock-price analysis dashboard.
Run with: python app.py
"""
import csv
import math
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, FuncFormatter
from algorithm import max_profit

SAMPLE = "100, 113, 110, 85, 105, 102, 86, 63, 81, 101, 94, 106, 101, 79, 94, 90, 97"
BG, PANEL, BORDER = "#0b1120", "#111a2b", "#26364d"
TEXT, MUTED, GREEN, RED, BLUE = "#e5edf7", "#8ea1bb", "#36d399", "#fb7185", "#60a5fa"


def parse_prices(raw):
    tokens = [x for x in re.split(r"[,;\s]+", raw.strip()) if x]
    if len(tokens) < 2:
        raise ValueError("Enter at least two closing prices.")
    try:
        values = [float(x) for x in tokens]
    except ValueError as exc:
        raise ValueError("Prices must be numbers separated by commas or spaces.") from exc
    if any(not math.isfinite(x) or x <= 0 for x in values):
        raise ValueError("Every price must be a finite number greater than zero.")
    return values


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise ValueError("This CSV is empty.")
    headers = [x.strip().lower() for x in rows[0]]
    col = next((i for i, h in enumerate(headers) if h in ("close", "closing price", "adj close", "adj_close")), None)
    start = 1 if col is not None else 0
    if col is None:
        col = len(rows[0]) - 1
        try:
            [float(x) for x in rows[0]]
        except (ValueError, TypeError):
            start = 1
    prices = []
    for row in rows[start:]:
        try:
            value = float(row[col].replace(",", "").strip())
            if math.isfinite(value) and value > 0:
                prices.append(value)
        except (ValueError, IndexError, AttributeError):
            pass
    if len(prices) < 2:
        raise ValueError("Could not find two numeric prices. Use a CSV with a Close column.")
    return prices


class Metric(ctk.CTkFrame):
    def __init__(self, parent, label, color=GREEN):
        super().__init__(parent, fg_color=PANEL, corner_radius=14, border_width=1, border_color=BORDER)
        ctk.CTkLabel(self, text=label.upper(), text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=15, pady=(13, 3))
        self.value = ctk.CTkLabel(self, text="—", text_color=color, font=ctk.CTkFont(size=23, weight="bold"))
        self.value.pack(anchor="w", padx=15)
        self.note = ctk.CTkLabel(self, text="Awaiting analysis", text_color=MUTED, font=ctk.CTkFont(size=10))
        self.note.pack(anchor="w", padx=15, pady=(2, 13))

    def set(self, value, note, color=None):
        self.value.configure(text=value)
        self.note.configure(text=note)
        if color:
            self.value.configure(text_color=color)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("StockYield | Historical Analysis")
        self.geometry("1360x860")
        self.minsize(1050, 700)
        self.configure(fg_color=BG)
        self.prices, self.result, self.source = [], None, "Sample dataset"
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar()
        self._main()
        self.price_input.insert("1.0", SAMPLE)
        self.analyze()

    def _sidebar(self):
        side = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#0e1728")
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="↗  StockYield", text_color=GREEN, font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=20, pady=(28, 35))
        ctk.CTkLabel(side, text="WORKSPACE", text_color="#647993", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=20, pady=(0, 10))
        for label, action in [("▦  Overview", lambda: self.main.focus_set()), ("⌁  Price input", lambda: self.price_input.focus_set()), ("⑂  Algorithm trace", lambda: self.trace.focus_set())]:
            ctk.CTkButton(side, text=label, anchor="w", fg_color="transparent", hover_color="#1b2c40", text_color=TEXT, command=action, height=38).pack(fill="x", padx=10, pady=3)
        ctk.CTkFrame(side, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=22)
        ctk.CTkLabel(side, text="ALGORITHM", text_color="#647993", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(side, text="Divide and Conquer\nMaximum Subarray\nO(n log n) time", justify="left", text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=8)
        ctk.CTkLabel(side, text="DAA PROJECT • PYTHON", text_color="#647993", font=ctk.CTkFont(size=9, weight="bold")).pack(side="bottom", anchor="w", padx=20, pady=20)

    def _main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=25, pady=22)
        self.main.grid_columnconfigure(0, weight=1)
        # Give the price chart most of the available vertical space.
        self.main.grid_rowconfigure(3, weight=6, minsize=260)
        self.main.grid_rowconfigure(4, weight=1, minsize=100)
        head = ctk.CTkFrame(self.main, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="Historical Stock Yield Optimization", text_color=TEXT, font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(head, text="Find the best historical buy and sell days from closing prices.", text_color=MUTED).grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.status = ctk.CTkLabel(head, text="● READY", text_color=GREEN, fg_color="#123c36", corner_radius=18, padx=12, pady=7)
        self.status.grid(row=0, column=1, rowspan=2, sticky="e")
        metrics = ctk.CTkFrame(self.main, fg_color="transparent")
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(4): metrics.grid_columnconfigure(i, weight=1, uniform="metric")
        self.m_profit = Metric(metrics, "Maximum profit", GREEN)
        self.m_return = Metric(metrics, "Return", GREEN)
        self.m_buy = Metric(metrics, "Optimal buy", BLUE)
        self.m_sell = Metric(metrics, "Optimal sell", RED)
        for i, m in enumerate((self.m_profit, self.m_return, self.m_buy, self.m_sell)):
            m.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 7, 0 if i == 3 else 7))
        inp = ctk.CTkFrame(self.main, fg_color=PANEL, corner_radius=14, border_width=1, border_color=BORDER)
        inp.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        inp.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(inp, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 4))
        ctk.CTkLabel(top, text="PRICE INPUT", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.source_label = ctk.CTkLabel(top, text=self.source, text_color=MUTED, font=ctk.CTkFont(size=10))
        self.source_label.pack(side="right")
        self.price_input = ctk.CTkTextbox(inp, height=58, fg_color="#0b1322", border_color=BORDER, border_width=1, font=ctk.CTkFont(family="Consolas", size=12))
        self.price_input.grid(row=1, column=0, sticky="ew", padx=15, pady=4)
        buttons = ctk.CTkFrame(inp, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="w", padx=12, pady=(5, 12))
        ctk.CTkButton(buttons, text="Analyze prices", command=self.analyze, fg_color="#16865f", hover_color="#126b4c").pack(side="left", padx=4)
        ctk.CTkButton(buttons, text="Load CSV", command=self.load_csv).pack(side="left", padx=4)
        ctk.CTkButton(buttons, text="Use sample", command=self.use_sample, fg_color="#26364d").pack(side="left", padx=4)
        ctk.CTkButton(buttons, text="Clear", command=self.clear, fg_color="#26364d").pack(side="left", padx=4)
        ctk.CTkButton(buttons, text="Export report", command=self.export, fg_color="#26364d").pack(side="left", padx=4)
        chart = ctk.CTkFrame(self.main, fg_color=PANEL, corner_radius=14, border_width=1, border_color=BORDER)
        chart.grid(row=3, column=0, sticky="nsew", pady=(0, 15))
        chart.grid_columnconfigure(0, weight=1)
        chart.grid_rowconfigure(1, weight=1, minsize=220)
        ctk.CTkLabel(chart, text="PRICE MOVEMENT", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=12)
        # Keep the requested canvas height modest so the chart remains visible
        # inside the dashboard instead of pushing the panel below the window.
        self.fig = Figure(figsize=(8, 3.4), dpi=100, facecolor=PANEL)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 2))

        # Scrollbars let users move through the chart after zooming in.
        self.chart_x_scroll = tk.Scrollbar(
            chart, orient="horizontal", command=self._scroll_chart_x,
            troughcolor="#172338", bg="#26364d", activebackground="#60a5fa",
            highlightthickness=0, bd=0,
        )
        self.chart_x_scroll.grid(row=2, column=0, sticky="ew", padx=(12, 4), pady=(0, 2))
        self.chart_y_scroll = tk.Scrollbar(
            chart, orient="vertical", command=self._scroll_chart_y,
            troughcolor="#172338", bg="#26364d", activebackground="#60a5fa",
            highlightthickness=0, bd=0,
        )
        self.chart_y_scroll.grid(row=1, column=1, sticky="ns", padx=(2, 8), pady=(0, 2))

        # Custom dashboard controls replace Matplotlib's default toolbar.
        controls = ctk.CTkFrame(chart, fg_color="transparent")
        controls.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(3, 6))
        self.pan_enabled = False
        self._pan_start = None
        self._default_xlim = None
        self._default_ylim = None
        ctk.CTkLabel(controls, text="CHART CONTROLS", text_color=MUTED,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls, text="− Zoom out", width=90, height=30,
                      fg_color="#26364d", hover_color="#344a66",
                      command=lambda: self._zoom_chart(1.25)).pack(side="left", padx=3)
        ctk.CTkButton(controls, text="+ Zoom in", width=85, height=30,
                      fg_color="#26364d", hover_color="#344a66",
                      command=lambda: self._zoom_chart(0.8)).pack(side="left", padx=3)
        self.pan_button = ctk.CTkButton(
            controls, text="Pan: off", width=80, height=30,
            fg_color="#26364d", hover_color="#344a66",
            command=self._toggle_pan,
        )
        self.pan_button.pack(side="left", padx=3)
        ctk.CTkButton(controls, text="Reset view", width=85, height=30,
                      fg_color="#26364d", hover_color="#344a66",
                      command=self._reset_chart_view).pack(side="left", padx=3)
        ctk.CTkButton(controls, text="Save chart", width=85, height=30,
                      fg_color="#26364d", hover_color="#344a66",
                      command=self._save_chart).pack(side="left", padx=3)
        self.chart_hint = ctk.CTkLabel(
            chart,
            text="Hover over a point for details • Click a point to inspect • Scroll to zoom",
            text_color=MUTED,
            font=ctk.CTkFont(size=10),
        )
        self.chart_hint.grid(row=4, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))
        self._hover_annotation = None
        self._hover_line = None
        self._selected_point = None
        self.canvas.mpl_connect("motion_notify_event", self._on_chart_hover)
        self.canvas.mpl_connect("button_press_event", self._on_chart_click)
        self.canvas.mpl_connect("scroll_event", self._on_chart_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_pan_press)
        self.canvas.mpl_connect("button_release_event", self._on_pan_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_pan_motion)
        trace_panel = ctk.CTkFrame(self.main, fg_color=PANEL, corner_radius=14, border_width=1, border_color=BORDER)
        trace_panel.grid(row=4, column=0, sticky="nsew")
        trace_panel.grid_columnconfigure(0, weight=1); trace_panel.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(trace_panel, text="ALGORITHM EXECUTION TRACE  •  DIVIDE / CONQUER / COMBINE", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=10)
        self.trace = ctk.CTkTextbox(trace_panel, fg_color="#0b1322", border_color=BORDER, border_width=1, font=ctk.CTkFont(family="Consolas", size=10), wrap="none")
        self.trace.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _draw_chart(self):
        # Recreate transient hover artists whenever the plot is rebuilt.
        self._hover_annotation = None
        self._hover_line = None
        self.ax.clear()
        self.ax.set_facecolor(PANEL)

        days = list(range(1, len(self.prices) + 1))
        if not days:
            self.ax.text(
                0.5, 0.5, "Enter prices and run analysis",
                color=MUTED, ha="center", va="center",
                transform=self.ax.transAxes, fontsize=11,
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self._default_xlim = None
            self._default_ylim = None
        else:
            self.ax.plot(
                days, self.prices, color=BLUE, linewidth=2.2,
                marker="o", markersize=3.5, markerfacecolor=BLUE,
                markeredgewidth=0, label="Closing price", zorder=2,
            )
            self.ax.set_xlim(max(0.5, days[0] - 0.6), days[-1] + 0.6)
            self.ax.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
            self.ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.2f}"))
            self.ax.grid(axis="y", color=BORDER, linewidth=0.7, alpha=0.8)
            self.ax.grid(axis="x", color=BORDER, linewidth=0.35, alpha=0.35)
            self.ax.set_axisbelow(True)
            self.ax.margins(y=0.13)
            self.ax.set_xlabel("Trading day", color=MUTED, labelpad=8)
            self.ax.set_ylabel("Closing price", color=MUTED, labelpad=8)
            self.ax.tick_params(axis="both", colors=MUTED, labelsize=9, length=0, pad=6)
            for spine in self.ax.spines.values():
                spine.set_color(BORDER)
                spine.set_linewidth(0.8)

            if self.result and self.result.buy_day is not None:
                r = self.result
                self.ax.axvspan(r.buy_day, r.sell_day, color=GREEN, alpha=0.09, zorder=0)
                self.ax.scatter(
                    [r.buy_day], [r.buy_price], color=GREEN, s=78,
                    edgecolors=PANEL, linewidths=1.4, label="Optimal buy", zorder=5,
                )
                self.ax.scatter(
                    [r.sell_day], [r.sell_price], color=RED, s=78,
                    edgecolors=PANEL, linewidths=1.4, label="Optimal sell", zorder=5,
                )
                buy_offset = (8, 10) if r.buy_day < r.sell_day else (8, -18)
                sell_offset = (8, -18) if r.sell_price >= r.buy_price else (8, 10)
                self.ax.annotate(
                    f"BUY · D{r.buy_day}", (r.buy_day, r.buy_price),
                    xytext=buy_offset, textcoords="offset points",
                    color=GREEN, fontsize=8, fontweight="bold", annotation_clip=True,
                )
                self.ax.annotate(
                    f"SELL · D{r.sell_day}", (r.sell_day, r.sell_price),
                    xytext=sell_offset, textcoords="offset points",
                    color=RED, fontsize=8, fontweight="bold", annotation_clip=True,
                )

            if self._selected_point is not None and 1 <= self._selected_point <= len(self.prices):
                selected_price = self.prices[self._selected_point - 1]
                self.ax.scatter(
                    [self._selected_point], [selected_price], s=150,
                    facecolors="none", edgecolors="#fbbf24", linewidths=2,
                    label=f"Selected day {self._selected_point}", zorder=6,
                )

            handles, labels = self.ax.get_legend_handles_labels()
            if handles:
                legend = self.ax.legend(
                    loc="upper left", ncol=min(len(labels), 3),
                    facecolor="#172338", edgecolor=BORDER,
                    labelcolor=TEXT, fontsize=8, framealpha=0.95,
                    borderpad=0.7, handlelength=1.6,
                )
                legend.get_frame().set_linewidth(0.7)
            self._default_xlim = self.ax.get_xlim()
            self._default_ylim = self.ax.get_ylim()

        self.fig.subplots_adjust(left=0.105, right=0.985, top=0.96, bottom=0.16)
        self.canvas.draw_idle()
        self._sync_chart_scrollbars()

    def _sync_chart_scrollbars(self):
        """Keep scrollbar thumbs aligned with the current chart view."""
        if self._default_xlim is None or self._default_ylim is None:
            self.chart_x_scroll.set(0.0, 1.0)
            self.chart_y_scroll.set(0.0, 1.0)
            return

        def fractions(current, default):
            base_span = max(default[1] - default[0], 1e-9)
            view_span = max(current[1] - current[0], 1e-9)
            start = (current[0] - default[0]) / base_span
            end = start + view_span / base_span
            # Tk scrollbars accept fractions from 0 to 1.
            return max(0.0, min(1.0, start)), max(0.0, min(1.0, end))

        self.chart_x_scroll.set(*fractions(self.ax.get_xlim(), self._default_xlim))
        self.chart_y_scroll.set(*fractions(self.ax.get_ylim(), self._default_ylim))

    def _scroll_chart_x(self, *args):
        if self._default_xlim is None:
            return
        base0, base1 = self._default_xlim
        base_span = base1 - base0
        current0, current1 = self.ax.get_xlim()
        span = min(current1 - current0, base_span * 3.0)
        if args[0] == "moveto":
            start = base0 + float(args[1]) * base_span
        elif args[0] == "scroll":
            units = int(args[1])
            mode = args[2] if len(args) > 2 else "units"
            step = span * (0.1 if mode == "pages" else 0.08)
            start = current0 + units * step
        else:
            return
        start = min(max(start, base0 - span + 0.05 * base_span), base1 - 0.05 * base_span)
        self.ax.set_xlim(start, start + span)
        self.canvas.draw_idle()
        self._sync_chart_scrollbars()

    def _scroll_chart_y(self, *args):
        if self._default_ylim is None:
            return
        base0, base1 = self._default_ylim
        base_span = base1 - base0
        current0, current1 = self.ax.get_ylim()
        span = min(current1 - current0, base_span * 3.0)
        if args[0] == "moveto":
            start = base0 + float(args[1]) * base_span
        elif args[0] == "scroll":
            units = int(args[1])
            mode = args[2] if len(args) > 2 else "units"
            step = span * (0.1 if mode == "pages" else 0.08)
            start = current0 + units * step
        else:
            return
        start = min(max(start, base0 - span + 0.05 * base_span), base1 - 0.05 * base_span)
        self.ax.set_ylim(start, start + span)
        self.canvas.draw_idle()
        self._sync_chart_scrollbars()

    def _apply_zoom(self, scale, center_x=None, center_y=None):
        """Zoom around a data point while keeping the view within sensible limits."""
        if self._default_xlim is None or self._default_ylim is None:
            return

        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        if center_x is None:
            center_x = (x0 + x1) / 2
        if center_y is None:
            center_y = (y0 + y1) / 2

        base_x_span = max(self._default_xlim[1] - self._default_xlim[0], 1e-9)
        base_y_span = max(self._default_ylim[1] - self._default_ylim[0], 1e-9)
        min_x_span, max_x_span = base_x_span * 0.03, base_x_span * 3.0
        min_y_span, max_y_span = base_y_span * 0.03, base_y_span * 3.0

        new_x_span = min(max((x1 - x0) * scale, min_x_span), max_x_span)
        new_y_span = min(max((y1 - y0) * scale, min_y_span), max_y_span)
        x_fraction = 0.5 if x1 == x0 else (center_x - x0) / (x1 - x0)
        y_fraction = 0.5 if y1 == y0 else (center_y - y0) / (y1 - y0)

        self.ax.set_xlim(center_x - new_x_span * x_fraction,
                         center_x + new_x_span * (1 - x_fraction))
        self.ax.set_ylim(center_y - new_y_span * y_fraction,
                         center_y + new_y_span * (1 - y_fraction))
        self.canvas.draw_idle()
        self._sync_chart_scrollbars()

    def _zoom_chart(self, scale):
        self._apply_zoom(scale)

    def _reset_chart_view(self):
        if self._default_xlim is not None and self._default_ylim is not None:
            self.ax.set_xlim(self._default_xlim)
            self.ax.set_ylim(self._default_ylim)
            self.canvas.draw_idle()
            self._sync_chart_scrollbars()
        self.chart_hint.configure(text="Chart view reset • Hover for details • Click a point to inspect")

    def _toggle_pan(self):
        self.pan_enabled = not self.pan_enabled
        self.pan_button.configure(
            text="Pan: on" if self.pan_enabled else "Pan: off",
            fg_color="#16865f" if self.pan_enabled else "#26364d",
            hover_color="#126b4c" if self.pan_enabled else "#344a66",
        )
        self._pan_start = None
        self.canvas.get_tk_widget().configure(cursor="fleur" if self.pan_enabled else "")
        self.chart_hint.configure(
            text="Pan mode: drag the chart to move around" if self.pan_enabled
            else "Hover for details • Click a point to inspect • Scroll or use zoom buttons"
        )

    def _on_pan_press(self, event):
        if (not self.pan_enabled or event.button != 1 or event.inaxes != self.ax
                or event.x is None or event.y is None):
            return
        # Store screen pixels, not data coordinates. Data coordinates change as
        # the axes move, which made the old drag implementation feel jumpy.
        self._pan_start = (event.x, event.y, self.ax.get_xlim(), self.ax.get_ylim())
        if self._hover_annotation is not None:
            self._hover_annotation.set_visible(False)
        if self._hover_line is not None:
            self._hover_line.set_visible(False)

    def _on_pan_motion(self, event):
        if not self.pan_enabled or self._pan_start is None:
            return
        if event.x is None or event.y is None:
            return
        start_x, start_y, xlim, ylim = self._pan_start
        width = max(float(self.ax.bbox.width), 1.0)
        height = max(float(self.ax.bbox.height), 1.0)
        dx = (event.x - start_x) * (xlim[1] - xlim[0]) / width
        dy = (event.y - start_y) * (ylim[1] - ylim[0]) / height
        self.ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
        self.ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
        self.canvas.draw_idle()
        self._sync_chart_scrollbars()

    def _on_pan_release(self, event):
        self._pan_start = None

    def _save_chart(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Save chart image", defaultextension=".png",
            initialfile="stockyield_chart.png",
            filetypes=[("PNG image", "*.png"), ("PDF document", "*.pdf"), ("SVG image", "*.svg")],
        )
        if not path:
            return
        try:
            self.fig.savefig(path, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Save chart failed", str(exc), parent=self)
            return
        messagebox.showinfo("Chart saved", f"Chart saved to:\n{path}", parent=self)

    def _nearest_day(self, event):
        """Return a day only when the pointer is close to its actual plotted point."""
        if (event.inaxes != self.ax or event.x is None or event.y is None
                or event.xdata is None or not self.prices):
            return None
        day = int(round(event.xdata))
        if day < 1 or day > len(self.prices):
            return None
        point_x, point_y = self.ax.transData.transform((day, self.prices[day - 1]))
        # Pixel-based tolerance behaves consistently at different zoom levels.
        distance = math.hypot(event.x - point_x, event.y - point_y)
        return day if distance <= 14 else None

    def _on_chart_hover(self, event):
        if self.pan_enabled:
            return
        day = self._nearest_day(event)
        if day is None:
            if self._hover_annotation is not None and self._hover_annotation.get_visible():
                self._hover_annotation.set_visible(False)
                if self._hover_line is not None:
                    self._hover_line.set_visible(False)
                self.canvas.draw_idle()
            return
        price = self.prices[day - 1]
        if self._hover_annotation is None:
            self._hover_annotation = self.ax.annotate(
                "", xy=(day, price), xytext=(12, 12), textcoords="offset points",
                color=TEXT, fontsize=9,
                bbox=dict(boxstyle="round,pad=0.45", fc="#172338", ec=BORDER, alpha=0.97),
                arrowprops=dict(arrowstyle="->", color=BLUE),
            )
            self._hover_line = self.ax.axvline(day, color=MUTED, linewidth=0.8, linestyle="--", alpha=0.7)
        self._hover_annotation.xy = (day, price)
        self._hover_annotation.set_text(f"Day {day}\nPrice: {price:,.2f}")
        self._hover_annotation.set_visible(True)
        self._hover_line.set_xdata([day, day])
        self._hover_line.set_visible(True)
        self.canvas.draw_idle()

    def _on_chart_click(self, event):
        if self.pan_enabled or event.button != 1:
            return
        day = self._nearest_day(event)
        if day is None:
            return
        price = self.prices[day - 1]
        role = ""
        if self.result and self.result.buy_day == day:
            role = " • OPTIMAL BUY"
        elif self.result and self.result.sell_day == day:
            role = " • OPTIMAL SELL"
        # Selecting a point should not unexpectedly reset the user's zoom.
        current_xlim, current_ylim = self.ax.get_xlim(), self.ax.get_ylim()
        self.chart_hint.configure(text=f"Selected Day {day} • Closing price: {price:,.2f}{role}")
        self._selected_point = day
        self._draw_chart()
        self.ax.set_xlim(current_xlim)
        self.ax.set_ylim(current_ylim)
        self.canvas.draw_idle()

    def _on_chart_scroll(self, event):
        if self.pan_enabled or event.inaxes != self.ax or event.xdata is None:
            return
        # Keep wheel zoom centered on the pointer and clamp extreme zoom levels.
        scale = 0.8 if event.button == "up" else 1.25
        center_y = event.ydata if event.ydata is not None else (sum(self.ax.get_ylim()) / 2)
        self._apply_zoom(scale, event.xdata, center_y)

    def analyze(self):
        try:
            prices = parse_prices(self.price_input.get("1.0", "end"))
            result = max_profit(prices)
        except (ValueError, OverflowError) as exc:
            messagebox.showerror("Cannot analyze prices", str(exc), parent=self)
            return
        self.prices, self.result = prices, result
        self._selected_point = None
        self.chart_hint.configure(text="Hover over a point for details • Click a point to inspect • Scroll to zoom")
        self.status.configure(text="● ANALYSIS COMPLETE", text_color=GREEN)
        self.source_label.configure(text=f"{self.source} • {len(prices)} prices")
        if result.buy_day is None:
            self.m_profit.set("0.00", "No profitable trade")
            self.m_return.set("0.00%", "No positive return")
            self.m_buy.set("No trade", "No buy point", BLUE)
            self.m_sell.set("No trade", "No sell point", RED)
        else:
            self.m_profit.set(f"{result.profit:,.2f}", "Best price difference")
            self.m_return.set(f"{result.profit / result.buy_price * 100:.2f}%", "Profit ÷ buy price")
            self.m_buy.set(f"Day {result.buy_day}", f"Price {result.buy_price:,.2f}", BLUE)
            self.m_sell.set(f"Day {result.sell_day}", f"Price {result.sell_price:,.2f}", RED)
        self.trace.configure(state="normal"); self.trace.delete("1.0", "end")
        self.trace.insert("1.0", "\n".join(result.trace)); self.trace.configure(state="disabled")
        self._draw_chart()

    def load_csv(self):
        path = filedialog.askopenfilename(parent=self, title="Load historical prices", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path: return
        try: prices = read_csv(path)
        except (OSError, ValueError, csv.Error) as exc:
            messagebox.showerror("CSV import failed", str(exc), parent=self); return
        self.source = Path(path).name
        self.price_input.delete("1.0", "end"); self.price_input.insert("1.0", ", ".join(f"{p:g}" for p in prices))
        self.analyze()

    def use_sample(self):
        self.source = "Sample dataset"
        self.price_input.delete("1.0", "end"); self.price_input.insert("1.0", SAMPLE)
        self.analyze()

    def clear(self):
        self.price_input.delete("1.0", "end")
        self.prices, self.result, self.source = [], None, "No dataset"
        self._selected_point = None
        self.chart_hint.configure(text="Hover over a point for details • Click a point to inspect • Scroll to zoom")
        self.source_label.configure(text=self.source)
        self.status.configure(text="● WAITING FOR INPUT", text_color=MUTED)
        for metric in (self.m_profit, self.m_return, self.m_buy, self.m_sell): metric.set("—", "Awaiting analysis")
        self._hover_annotation = None; self._hover_line = None
        self._default_xlim = None; self._default_ylim = None
        self.ax.clear(); self.ax.set_facecolor(PANEL); self.ax.text(.5, .5, "Enter prices and run analysis", color=MUTED, ha="center", va="center", transform=self.ax.transAxes)
        self.ax.set_xticks([]); self.ax.set_yticks([]); self.fig.subplots_adjust(left=0.105, right=0.985, top=0.96, bottom=0.16); self.canvas.draw_idle(); self._sync_chart_scrollbars()
        self.trace.configure(state="normal"); self.trace.delete("1.0", "end"); self.trace.insert("1.0", "Input cleared. Enter at least two positive closing prices."); self.trace.configure(state="disabled")

    def export(self):
        if not self.result:
            messagebox.showinfo("Nothing to export", "Analyze a price sequence first.", parent=self); return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", initialfile="stockyield_report.csv", filetypes=[("CSV report", "*.csv")])
        if not path: return
        r = self.result
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["StockYield Historical Analysis Report"]); w.writerow(["Source", self.source])
                w.writerow(["Algorithm", "Divide and Conquer - Maximum Subarray"]); w.writerow(["Time complexity", "O(n log n)"])
                w.writerow([]); w.writerow(["Day", "Closing Price"])
                w.writerows((i, p) for i, p in enumerate(self.prices, 1))
                w.writerow([]); w.writerow(["Maximum profit", r.profit])
                if r.buy_day is not None:
                    w.writerow(["Buy day", r.buy_day]); w.writerow(["Buy price", r.buy_price])
                    w.writerow(["Sell day", r.sell_day]); w.writerow(["Sell price", r.sell_price])
                    w.writerow(["Return (%)", r.profit / r.buy_price * 100])
                else: w.writerow(["Best action", "No profitable trade"])
                w.writerow([]); w.writerow(["Algorithm trace"]); w.writerows([[line] for line in r.trace])
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc), parent=self); return
        messagebox.showinfo("Export complete", f"Report saved to:\n{path}", parent=self)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    App().mainloop()
