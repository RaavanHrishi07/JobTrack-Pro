import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import calendar as month_calendar
from datetime import datetime, date, timedelta
from collections import Counter

DB_NAME = "jobtrack.db"

BG = "#F4F6FA"
CARD = "#FFFFFF"
PRIMARY = "#4F46E5"
TEXT = "#1F2937"
MUTED = "#6B7280"


class JobTrackPro:
    def __init__(self, root):
        self.root = root
        self.root.title("JobTrack Pro | Application Manager")
        # Fit the application inside the usable screen area (including taskbar space).
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w = min(1250, max(900, screen_w - 80))
        window_h = min(790, max(560, screen_h - 100))
        self.root.geometry(f"{window_w}x{window_h}")
        self.root.minsize(900, 560)
        self.root.configure(bg=BG)

        self.selected_id = None
        self.dark_mode = False
        self.sort_order = "Newest First"
        self.status_filter = tk.StringVar(value="All Statuses")
        self.search_var = tk.StringVar()

        self.create_database()
        self.build_ui()
        self.refresh_dashboard()
        self.root.after(1800, self.check_due_reminders)

    # ---------------- DATABASE ----------------

    def create_database(self):
        """Create or safely upgrade the existing database."""
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    location TEXT,
                    salary TEXT,
                    date_applied TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Applied',
                    notes TEXT,
                    interview_date TEXT
                )
            """)

            cursor.execute("PRAGMA table_info(applications)")
            columns = [column[1] for column in cursor.fetchall()]

            if "interview_date" not in columns:
                cursor.execute(
                    "ALTER TABLE applications ADD COLUMN interview_date TEXT"
                )
            if "follow_up_date" not in columns:
                cursor.execute(
                    "ALTER TABLE applications ADD COLUMN follow_up_date TEXT"
                )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminder_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    reminder_type TEXT NOT NULL,
                    reminder_date TEXT NOT NULL,
                    notified_at TEXT NOT NULL,
                    UNIQUE(application_id, reminder_type, reminder_date)
                )
            """)
            conn.commit()

    # ---------------- MAIN UI ----------------

    def build_ui(self):
        """Build the modern application shell and dashboard."""
        self.apply_widget_styles()

        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True)

        # Modern left navigation sidebar
        sidebar = tk.Frame(shell, bg="#111827", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg="#111827")
        brand.pack(fill="x", padx=20, pady=(25, 30))

        tk.Label(
            brand, text="JT", font=("Segoe UI", 17, "bold"),
            bg=PRIMARY, fg="white", width=3, height=1
        ).pack(anchor="w", pady=(0, 12))
        tk.Label(
            brand, text="JobTrack Pro", font=("Segoe UI", 16, "bold"),
            bg="#111827", fg="white"
        ).pack(anchor="w")
        tk.Label(
            brand, text="CAREER WORKSPACE", font=("Segoe UI", 8, "bold"),
            bg="#111827", fg="#9CA3AF"
        ).pack(anchor="w", pady=(4, 0))

        self.nav_button(sidebar, "▦   Dashboard", self.show_dashboard, active=True)
        self.nav_button(sidebar, "▤   Applications", self.focus_applications)
        self.nav_button(sidebar, "▣   Kanban Board", self.open_kanban)
        self.nav_button(sidebar, "▦   Calendar & Reminders", self.open_calendar)
        self.nav_button(sidebar, "▥   Analytics", self.open_analytics)
        self.nav_button(sidebar, "⇩   Export Data", self.export_csv)

        tk.Frame(sidebar, bg="#374151", height=1).pack(
            fill="x", padx=18, pady=18
        )

        tk.Button(
            sidebar,
            text="☾   Toggle Theme",
            command=self.toggle_theme,
            bg="#1F2937", fg="#E5E7EB",
            activebackground="#374151", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat",
            bd=0, anchor="w", padx=18, pady=11, cursor="hand2"
        ).pack(fill="x", padx=12, pady=3)

        tk.Label(
            sidebar, text="Organise your next move.",
            bg="#111827", fg="#9CA3AF",
            font=("Segoe UI", 8), wraplength=175, justify="left"
        ).pack(side="bottom", anchor="w", padx=20, pady=20)

        # Main workspace
        self.workspace = tk.Frame(shell, bg=BG)
        self.workspace.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.workspace, bg=BG)
        header.pack(fill="x", padx=25, pady=(20, 10))

        heading_area = tk.Frame(header, bg=BG)
        heading_area.pack(side="left", fill="x", expand=True)

        tk.Label(
            heading_area, text="Dashboard",
            font=("Segoe UI", 23, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w")
        tk.Label(
            heading_area,
            text="Track applications, interviews and career progress in one place.",
            font=("Segoe UI", 9), bg=BG, fg=MUTED
        ).pack(anchor="w", pady=(3, 0))

        tk.Label(
            header, text=date.today().strftime("%A, %d %B %Y"),
            font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED,
            padx=13, pady=9
        ).pack(side="right", anchor="n")

        self.cards_frame = tk.Frame(self.workspace, bg=BG)
        self.cards_frame.pack(fill="x", padx=25, pady=(8, 12))

        self.total_label = self.create_summary_card(
            self.cards_frame, "TOTAL APPLICATIONS"
        )
        self.applied_label = self.create_summary_card(
            self.cards_frame, "APPLIED"
        )
        self.interview_label = self.create_summary_card(
            self.cards_frame, "INTERVIEWS"
        )
        self.selected_label = self.create_summary_card(
            self.cards_frame, "SELECTED"
        )
        self.success_label = self.create_summary_card(
            self.cards_frame, "SUCCESS RATE"
        )

        self.upcoming_frame = tk.Frame(
            self.workspace,
            bg="#1E3A5F" if getattr(self, "dark_mode", False) else "#EEF2FF",
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#C7D2FE",
            highlightthickness=1
        )
        self.upcoming_frame.pack(fill="x", padx=25, pady=(0, 12))

        self.upcoming_label = tk.Label(
            self.upcoming_frame,
            text="Upcoming interviews: None scheduled",
            font=("Segoe UI", 9, "bold"),
            bg="#1E3A5F" if getattr(self, "dark_mode", False) else "#EEF2FF",
            fg="#BFDBFE" if getattr(self, "dark_mode", False) else "#3730A3",
            anchor="w", padx=15, pady=10
        )
        self.upcoming_label.pack(fill="x")

        main = tk.Frame(self.workspace, bg=BG)
        main.pack(fill="both", expand=True, padx=25, pady=(0, 12))

        self.create_form(main)
        self.create_table_section(main)

        footer = tk.Frame(self.workspace, bg=BG)
        footer.pack(fill="x", padx=25, pady=(0, 13))
        tk.Label(
            footer, text="JOBTRACK PRO  •  YOUR CAREER, ORGANISED",
            bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")
        ).pack(side="left")

    def nav_button(self, parent, text, command, active=False):
        bg = "#312E81" if active else "#111827"
        fg = "#FFFFFF" if active else "#D1D5DB"
        button = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground="#374151",
            activeforeground="white", font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, anchor="w", padx=18, pady=12,
            cursor="hand2"
        )
        button.pack(fill="x", padx=12, pady=3)
        return button

    def show_dashboard(self):
        self.refresh_dashboard()

    def focus_applications(self):
        self.search_entry.focus_set()
        self.tree.focus_set()

    def apply_widget_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TEntry", padding=7, fieldbackground=CARD,
            foreground=TEXT, bordercolor="#D1D5DB"
        )
        style.configure(
            "TCombobox", padding=6, fieldbackground=CARD,
            foreground=TEXT, background=CARD
        )
        style.map(
            "TCombobox", fieldbackground=[("readonly", CARD)],
            foreground=[("readonly", TEXT)]
        )
        style.configure(
            "Treeview", background=CARD, foreground=TEXT,
            fieldbackground=CARD, rowheight=30,
            borderwidth=0, font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading", background="#E5E7EB",
            foreground="#374151", font=("Segoe UI", 9, "bold"),
            padding=8, relief="flat"
        )
        style.map(
            "Treeview", background=[("selected", "#C7D2FE")],
            foreground=[("selected", "#1E1B4B")]
        )

    def toggle_theme(self):
        """Switch between light and dark palettes, preserving database data."""
        global BG, CARD, PRIMARY, TEXT, MUTED

        self.dark_mode = not getattr(self, "dark_mode", False)
        if self.dark_mode:
            BG = "#0F172A"
            CARD = "#1E293B"
            PRIMARY = "#818CF8"
            TEXT = "#F1F5F9"
            MUTED = "#94A3B8"
        else:
            BG = "#F4F6FA"
            CARD = "#FFFFFF"
            PRIMARY = "#4F46E5"
            TEXT = "#1F2937"
            MUTED = "#6B7280"

        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_ui()
        self.refresh_dashboard()

    def create_summary_card(self, parent, title):
        card = tk.Frame(
            parent, bg=CARD, padx=14, pady=13,
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#E5E7EB",
            highlightthickness=1
        )
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            card, text=title, font=("Segoe UI", 8, "bold"),
            bg=CARD, fg=MUTED
        ).pack(anchor="w")

        value_label = tk.Label(
            card, text="0", font=("Segoe UI", 21, "bold"),
            bg=CARD, fg=PRIMARY
        )
        value_label.pack(anchor="w", pady=(4, 0))
        return value_label

    # ---------------- APPLICATION FORM ----------------

    def create_form(self, parent):
        """Create a vertically scrollable form so every field and action stays reachable."""
        form_shell = tk.Frame(
            parent, bg=CARD, width=270,
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#E5E7EB",
            highlightthickness=1
        )
        form_shell.pack(side="left", fill="y", padx=(0, 14))
        form_shell.pack_propagate(False)

        title_bar = tk.Frame(form_shell, bg=CARD)
        title_bar.pack(fill="x", padx=14, pady=(12, 5))
        tk.Label(
            title_bar, text="Application Details",
            font=("Segoe UI", 14, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w")

        # Canvas + scrollbar: the form scrolls independently from the applications table.
        canvas_host = tk.Frame(form_shell, bg=CARD)
        canvas_host.pack(fill="both", expand=True, padx=(10, 4), pady=(0, 8))

        self.form_canvas = tk.Canvas(
            canvas_host, bg=CARD, highlightthickness=0, borderwidth=0
        )
        form_scrollbar = ttk.Scrollbar(
            canvas_host, orient="vertical", command=self.form_canvas.yview
        )
        self.form_canvas.configure(yscrollcommand=form_scrollbar.set)
        form_scrollbar.pack(side="right", fill="y")
        self.form_canvas.pack(side="left", fill="both", expand=True)

        form = tk.Frame(self.form_canvas, bg=CARD, padx=5, pady=4)
        self.form_canvas_window = self.form_canvas.create_window(
            (0, 0), window=form, anchor="nw"
        )

        def update_scroll_region(_event=None):
            self.form_canvas.configure(
                scrollregion=self.form_canvas.bbox("all")
            )

        def fit_form_width(event):
            self.form_canvas.itemconfigure(
                self.form_canvas_window, width=event.width
            )

        form.bind("<Configure>", update_scroll_region)
        self.form_canvas.bind("<Configure>", fit_form_width)

        # Mouse-wheel scrolling works while the pointer is over the form.
        def on_form_mousewheel(event):
            if getattr(event, "delta", 0):
                self.form_canvas.yview_scroll(
                    int(-1 * (event.delta / 120)), "units"
                )
            elif getattr(event, "num", None) == 4:
                self.form_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                self.form_canvas.yview_scroll(1, "units")

        self.form_canvas.bind("<MouseWheel>", on_form_mousewheel)
        self.form_canvas.bind("<Button-4>", on_form_mousewheel)
        self.form_canvas.bind("<Button-5>", on_form_mousewheel)
        form.bind("<Enter>", lambda _e: self.form_canvas.bind_all(
            "<MouseWheel>", on_form_mousewheel
        ))
        form.bind("<Leave>", lambda _e: self.form_canvas.unbind_all(
            "<MouseWheel>"
        ))

        self.entries = {}
        fields = [
            ("Company Name", "company"),
            ("Job Role", "role"),
            ("Location", "location"),
            ("Salary / Package", "salary"),
            ("Application Date (YYYY-MM-DD)", "date_applied"),
            ("Interview Date (YYYY-MM-DD)", "interview_date"),
            ("Follow-up Date (YYYY-MM-DD)", "follow_up_date")
        ]

        for label_text, key in fields:
            tk.Label(
                form, text=label_text, font=("Segoe UI", 8, "bold"),
                bg=CARD, fg=MUTED
            ).pack(anchor="w", pady=(5, 2))

            entry = ttk.Entry(form, font=("Segoe UI", 9))
            entry.pack(fill="x", pady=(0, 3))
            self.entries[key] = entry

        self.entries["date_applied"].insert(0, date.today().isoformat())

        tk.Label(
            form, text="Application Status",
            font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 2))

        self.status_box = ttk.Combobox(
            form,
            values=["Applied", "Interview", "Selected", "Rejected"],
            state="readonly"
        )
        self.status_box.set("Applied")
        self.status_box.pack(fill="x", pady=(0, 5))

        tk.Label(
            form, text="Notes", font=("Segoe UI", 8, "bold"),
            bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 2))

        self.notes_text = tk.Text(
            form, height=3, font=("Segoe UI", 9),
            relief="solid", bd=1, wrap="word"
        )
        self.notes_text.pack(fill="x", pady=(0, 8))

        self.add_button = tk.Button(
            form, text="＋ Add Application",
            command=self.add_application,
            bg=PRIMARY, fg="white", activebackground="#4338CA",
            activeforeground="white", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", pady=8
        )
        self.add_button.pack(fill="x", pady=3)

        tk.Button(
            form, text="Update Selected",
            command=self.update_application,
            bg="#0F766E", fg="white", activebackground="#115E59",
            activeforeground="white", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", pady=8
        ).pack(fill="x", pady=3)

        tk.Button(
            form, text="Delete Selected",
            command=self.delete_application,
            bg="#DC2626", fg="white", activebackground="#B91C1C",
            activeforeground="white", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", pady=8
        ).pack(fill="x", pady=3)

        tk.Button(
            form, text="Clear Form",
            command=self.clear_form,
            bg="#E5E7EB", fg=TEXT, activebackground="#D1D5DB",
            font=("Segoe UI", 9, "bold"), relief="flat",
            cursor="hand2", pady=8
        ).pack(fill="x", pady=3)

        # Keep the scroll position at the top whenever the form is cleared.
        self.form_canvas.yview_moveto(0)

    # ---------------- APPLICATION TABLE ----------------

    def create_table_section(self, parent):
        section = tk.Frame(
            parent, bg=CARD, padx=13, pady=13,
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#E5E7EB", highlightthickness=1
        )
        section.pack(side="left", fill="both", expand=True)

        tk.Label(
            section, text="Your Applications",
            font=("Segoe UI", 14, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 10))

        controls = tk.Frame(section, bg=CARD)
        controls.pack(fill="x", pady=(0, 8))

        self.search_entry = ttk.Entry(
            controls, textvariable=self.search_var, font=("Segoe UI", 9)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda event: self.refresh_table())

        tk.Button(
            controls, text="Search", command=self.refresh_table,
            bg=PRIMARY, fg="white", relief="flat", padx=9, pady=4
        ).pack(side="left", padx=2)

        tk.Button(
            controls, text="Reset", command=self.reset_filters,
            bg="#E5E7EB", fg=TEXT, relief="flat", padx=9, pady=4
        ).pack(side="left", padx=2)

        filters = tk.Frame(section, bg=CARD)
        filters.pack(fill="x", pady=(0, 8))

        tk.Label(
            filters, text="Status:", bg=CARD, fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(side="left", padx=(0, 5))

        self.status_filter_box = ttk.Combobox(
            filters, textvariable=self.status_filter,
            values=["All Statuses", "Applied", "Interview", "Selected", "Rejected"],
            state="readonly", width=14
        )
        self.status_filter_box.pack(side="left", padx=(0, 10))
        self.status_filter_box.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_table()
        )

        tk.Label(
            filters, text="Sort:", bg=CARD, fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(side="left", padx=(0, 5))

        self.sort_box = ttk.Combobox(
            filters, values=["Newest First", "Oldest First"],
            state="readonly", width=13
        )
        self.sort_box.set("Newest First")
        self.sort_box.pack(side="left")
        self.sort_box.bind("<<ComboboxSelected>>", self.change_sort)

        table_frame = tk.Frame(section, bg=CARD)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "id", "company", "role", "location",
            "date_applied", "status", "interview_date"
        )
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            selectmode="browse"
        )

        headings = {
            "id": "ID", "company": "Company", "role": "Job Role",
            "location": "Location", "date_applied": "Applied On",
            "status": "Status", "interview_date": "Interview Date"
        }
        widths = {
            "id": 35, "company": 105, "role": 110,
            "location": 80, "date_applied": 85,
            "status": 80, "interview_date": 100
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.select_application)
        self.tree.tag_configure("Selected", foreground="#047857")
        self.tree.tag_configure("Rejected", foreground="#DC2626")
        self.tree.tag_configure("Interview", foreground="#4338CA")

        self.result_label = tk.Label(
            section, text="", bg=CARD, fg=MUTED,
            font=("Segoe UI", 8)
        )
        self.result_label.pack(anchor="w", pady=(7, 0))

    # ---------------- KANBAN BOARD ----------------

    def open_kanban(self):
        """Open a drag-and-drop board for changing application statuses."""
        if getattr(self, "kanban_window", None) is not None:
            try:
                if self.kanban_window.winfo_exists():
                    self.kanban_window.lift()
                    self.refresh_kanban_board()
                    return
            except tk.TclError:
                pass

        self.kanban_window = tk.Toplevel(self.root)
        self.kanban_window.title("JobTrack Pro | Kanban Board")
        self.kanban_window.geometry("1120x680")
        self.kanban_window.minsize(900, 560)
        self.kanban_window.configure(bg=BG)
        self.kanban_window.protocol("WM_DELETE_WINDOW", self.close_kanban)

        header = tk.Frame(self.kanban_window, bg=BG)
        header.pack(fill="x", padx=22, pady=(18, 5))

        tk.Label(
            header, text="Application Pipeline",
            font=("Segoe UI", 21, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Drag an application card into another column to update its status.",
            font=("Segoe UI", 9), bg=BG, fg=MUTED
        ).pack(anchor="w", pady=(3, 0))

        self.kanban_feedback = tk.Label(
            self.kanban_window,
            text="Tip: Drop each card inside the target status column.",
            font=("Segoe UI", 9, "bold"), bg=BG, fg=PRIMARY,
            anchor="w"
        )
        self.kanban_feedback.pack(fill="x", padx=23, pady=(5, 8))

        self.kanban_board = tk.Frame(self.kanban_window, bg=BG)
        self.kanban_board.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.kanban_columns = {}
        self.kanban_counts = {}
        self.dragged_application_id = None
        self.drag_ghost = None
        self.refresh_kanban_board()

    def close_kanban(self):
        if getattr(self, "drag_ghost", None) is not None:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass
            self.drag_ghost = None
        if getattr(self, "kanban_window", None) is not None:
            try:
                self.kanban_window.destroy()
            except tk.TclError:
                pass
        self.kanban_window = None
        self.kanban_columns = {}

    def refresh_kanban_board(self):
        """Rebuild board columns from the current SQLite records."""
        if getattr(self, "kanban_window", None) is None:
            return
        try:
            if not self.kanban_window.winfo_exists():
                return
        except tk.TclError:
            return

        for widget in self.kanban_board.winfo_children():
            widget.destroy()

        statuses = [
            ("Applied", "#6366F1"),
            ("Interview", "#0EA5E9"),
            ("Selected", "#10B981"),
            ("Rejected", "#EF4444")
        ]
        rows = self.get_all_applications()
        grouped = {status: [] for status, _ in statuses}
        for row in rows:
            status = row[6] if row[6] in grouped else "Applied"
            grouped[status].append(row)

        self.kanban_columns = {}
        self.kanban_counts = {}

        for status, accent in statuses:
            column = tk.Frame(
                self.kanban_board, bg=CARD,
                highlightbackground="#334155" if self.dark_mode else "#E5E7EB",
                highlightthickness=1
            )
            column.pack(side="left", fill="both", expand=True, padx=5)
            self.kanban_columns[status] = column

            heading = tk.Frame(column, bg=CARD)
            heading.pack(fill="x", padx=10, pady=(10, 7))
            tk.Frame(heading, bg=accent, height=4).pack(fill="x", pady=(0, 8))

            title_row = tk.Frame(heading, bg=CARD)
            title_row.pack(fill="x")
            tk.Label(
                title_row, text=status, bg=CARD, fg=TEXT,
                font=("Segoe UI", 10, "bold")
            ).pack(side="left")
            count_label = tk.Label(
                title_row, text=str(len(grouped[status])), bg=BG, fg=MUTED,
                font=("Segoe UI", 8, "bold"), padx=7, pady=2
            )
            count_label.pack(side="right")
            self.kanban_counts[status] = count_label

            body = tk.Frame(column, bg=BG)
            body.pack(fill="both", expand=True, padx=7, pady=(0, 8))

            canvas = tk.Canvas(
                body, bg=BG, highlightthickness=0, borderwidth=0
            )
            scrollbar = ttk.Scrollbar(
                body, orient="vertical", command=canvas.yview
            )
            cards_frame = tk.Frame(canvas, bg=BG)
            cards_frame.bind(
                "<Configure>",
                lambda event, c=canvas: c.configure(
                    scrollregion=c.bbox("all")
                )
            )
            canvas_window = canvas.create_window(
                (0, 0), window=cards_frame, anchor="nw"
            )
            canvas.bind(
                "<Configure>",
                lambda event, c=canvas, item=canvas_window:
                    c.itemconfigure(item, width=event.width)
            )
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            for app in grouped[status]:
                self.create_kanban_card(cards_frame, app, accent)

            if not grouped[status]:
                tk.Label(
                    cards_frame, text="No applications",
                    bg=BG, fg=MUTED, font=("Segoe UI", 9),
                    pady=18
                ).pack(fill="x")

    def create_kanban_card(self, parent, app, accent):
        """Create a draggable card. app uses the get_all_applications tuple."""
        app_id, company, role, location, salary, applied, status, notes, interview = app
        card = tk.Frame(
            parent, bg=CARD, padx=10, pady=9,
            highlightbackground="#334155" if self.dark_mode else "#E5E7EB",
            highlightthickness=1, cursor="fleur"
        )
        card.pack(fill="x", padx=3, pady=5)
        tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(0, 7))

        tk.Label(
            card, text=company, bg=CARD, fg=TEXT,
            font=("Segoe UI", 10, "bold"), anchor="w",
            wraplength=205, justify="left"
        ).pack(fill="x")
        tk.Label(
            card, text=role, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9), anchor="w",
            wraplength=205, justify="left"
        ).pack(fill="x", pady=(2, 6))

        details = f"Applied: {applied}"
        if location:
            details += f"\n{location}"
        if interview:
            details += f"\nInterview: {interview}"
        tk.Label(
            card, text=details, bg=CARD, fg=MUTED,
            font=("Segoe UI", 8), anchor="w", justify="left"
        ).pack(fill="x")

        # Bind drag handlers to the card and its child labels.
        for widget in (card, *card.winfo_children()):
            widget.bind(
                "<ButtonPress-1>",
                lambda event, record_id=app_id, name=company:
                    self.kanban_drag_start(event, record_id, name)
            )
            widget.bind("<B1-Motion>", self.kanban_drag_motion)
            widget.bind("<ButtonRelease-1>", self.kanban_drag_drop)

    def kanban_drag_start(self, event, app_id, company):
        self.dragged_application_id = app_id
        if self.drag_ghost is not None:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass

        ghost = tk.Toplevel(self.kanban_window)
        ghost.overrideredirect(True)
        ghost.attributes("-topmost", True)
        ghost.configure(bg="#312E81")
        tk.Label(
            ghost, text=f"Moving: {company}",
            bg="#312E81", fg="white",
            font=("Segoe UI", 9, "bold"), padx=12, pady=7
        ).pack()
        self.drag_ghost = ghost
        ghost.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
        self.kanban_feedback.config(
            text=f"Moving {company} — release over a status column.", fg=PRIMARY
        )

    def kanban_drag_motion(self, event):
        if self.dragged_application_id is None or self.drag_ghost is None:
            return
        try:
            self.drag_ghost.geometry(
                f"+{event.x_root + 12}+{event.y_root + 12}"
            )
        except tk.TclError:
            pass

    def kanban_drag_drop(self, event):
        if self.dragged_application_id is None:
            return

        target_status = None
        x, y = event.x_root, event.y_root
        for status, column in self.kanban_columns.items():
            try:
                left = column.winfo_rootx()
                top = column.winfo_rooty()
                right = left + column.winfo_width()
                bottom = top + column.winfo_height()
                if left <= x <= right and top <= y <= bottom:
                    target_status = status
                    break
            except tk.TclError:
                continue

        app_id = self.dragged_application_id
        self.dragged_application_id = None

        if self.drag_ghost is not None:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass
            self.drag_ghost = None

        if target_status is None:
            self.kanban_feedback.config(
                text="Card returned unchanged. Drop it inside a status column.",
                fg=MUTED
            )
            return

        try:
            with sqlite3.connect(DB_NAME) as conn:
                current = conn.execute(
                    "SELECT status, company FROM applications WHERE id=?",
                    (app_id,)
                ).fetchone()
                if not current:
                    self.kanban_feedback.config(
                        text="This application no longer exists.", fg="#DC2626"
                    )
                    self.refresh_kanban_board()
                    return
                old_status, company = current
                if old_status == target_status:
                    self.kanban_feedback.config(
                        text=f"{company} is already in {target_status}.", fg=MUTED
                    )
                    return
                conn.execute(
                    "UPDATE applications SET status=? WHERE id=?",
                    (target_status, app_id)
                )

            self.kanban_feedback.config(
                text=f"{company}: {old_status} → {target_status}",
                fg="#10B981"
            )
            self.refresh_dashboard()
            self.refresh_kanban_board()
        except sqlite3.Error as error:
            messagebox.showerror("Kanban Update Error", str(error))
            self.refresh_kanban_board()

    # ---------------- VALIDATION ----------------

    def valid_date(self, value, field_name, optional=False):
        if not value and optional:
            return True
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                f"{field_name} must use YYYY-MM-DD format."
            )
            return False

    def get_form_data(self):
        data = {
            key: entry.get().strip()
            for key, entry in self.entries.items()
        }
        data["status"] = self.status_box.get()
        data["notes"] = self.notes_text.get("1.0", "end").strip()

        if not data["company"] or not data["role"]:
            messagebox.showwarning(
                "Missing Information",
                "Company Name and Job Role are required."
            )
            return None

        if not self.valid_date(data["date_applied"], "Application Date"):
            return None
        if not self.valid_date(
            data["interview_date"], "Interview Date", optional=True
        ):
            return None
        if not self.valid_date(
            data["follow_up_date"], "Follow-up Date", optional=True
        ):
            return None
        return data

    # ---------------- CRUD OPERATIONS ----------------

    def add_application(self):
        data = self.get_form_data()
        if not data:
            return
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("""
                    INSERT INTO applications
                    (company, role, location, salary, date_applied,
                     status, notes, interview_date, follow_up_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["company"], data["role"], data["location"],
                    data["salary"], data["date_applied"], data["status"],
                    data["notes"], data["interview_date"] or None,
                    data["follow_up_date"] or None
                ))
            messagebox.showinfo("Success", "Application added successfully!")
            self.clear_form()
            self.refresh_dashboard()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def update_application(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "No Selection", "Select an application from the table first."
            )
            return
        data = self.get_form_data()
        if not data:
            return
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("""
                    UPDATE applications
                    SET company=?, role=?, location=?, salary=?,
                        date_applied=?, status=?, notes=?, interview_date=?,
                        follow_up_date=?
                    WHERE id=?
                """, (
                    data["company"], data["role"], data["location"],
                    data["salary"], data["date_applied"], data["status"],
                    data["notes"], data["interview_date"] or None,
                    data["follow_up_date"] or None, self.selected_id
                ))
            messagebox.showinfo("Success", "Application updated successfully!")
            self.clear_form()
            self.refresh_dashboard()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_application(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "No Selection", "Select an application to delete."
            )
            return
        if not messagebox.askyesno(
            "Confirm Delete", "Are you sure you want to delete this application?"
        ):
            return
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute(
                    "DELETE FROM applications WHERE id=?", (self.selected_id,)
                )
            messagebox.showinfo("Deleted", "Application deleted successfully.")
            self.clear_form()
            self.refresh_dashboard()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def clear_form(self):
        self.selected_id = None
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.entries["date_applied"].insert(0, date.today().isoformat())
        self.status_box.set("Applied")
        self.notes_text.delete("1.0", "end")
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def select_application(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.selected_id = int(values[0])

        try:
            with sqlite3.connect(DB_NAME) as conn:
                row = conn.execute("""
                    SELECT company, role, location, salary, date_applied,
                           status, notes, interview_date, follow_up_date
                    FROM applications WHERE id=?
                """, (self.selected_id,)).fetchone()

            if not row:
                return

            keys = [
                "company", "role", "location", "salary",
                "date_applied", "status", "notes", "interview_date",
                "follow_up_date"
            ]
            for key, value in zip(keys, row):
                if key in self.entries:
                    self.entries[key].delete(0, "end")
                    self.entries[key].insert(0, value or "")

            self.status_box.set(row[5] or "Applied")
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", row[6] or "")
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    # ---------------- FILTERING AND SORTING ----------------

    def change_sort(self, event=None):
        self.sort_order = self.sort_box.get()
        self.refresh_table()

    def reset_filters(self):
        self.search_var.set("")
        self.status_filter.set("All Statuses")
        self.sort_box.set("Newest First")
        self.sort_order = "Newest First"
        self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_var.get().strip()
        status = self.status_filter.get()

        # Parentheses ensure the status filter applies to all search fields.
        query = """
            SELECT id, company, role, location, date_applied,
                   status, interview_date
            FROM applications
            WHERE (company LIKE ? OR role LIKE ? OR location LIKE ?)
        """
        pattern = f"%{search_text}%"
        params = [pattern, pattern, pattern]

        if status != "All Statuses":
            query += " AND status=?"
            params.append(status)

        order = "ASC" if self.sort_order == "Oldest First" else "DESC"
        query += f" ORDER BY date_applied {order}, id {order}"

        try:
            with sqlite3.connect(DB_NAME) as conn:
                rows = conn.execute(query, params).fetchall()

            for row in rows:
                tag = row[5] if row[5] in (
                    "Selected", "Rejected", "Interview"
                ) else ""
                self.tree.insert(
                    "", "end",
                    values=(
                        row[0], row[1], row[2], row[3],
                        row[4], row[5], row[6] or "—"
                    ),
                    tags=(tag,)
                )
            self.result_label.config(
                text=f"Showing {len(rows)} application(s)"
            )
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    # ---------------- DASHBOARD ----------------

    def get_all_applications(self):
        with sqlite3.connect(DB_NAME) as conn:
            return conn.execute("""
                SELECT id, company, role, location, salary,
                       date_applied, status, notes, interview_date
                FROM applications
                ORDER BY date_applied DESC, id DESC
            """).fetchall()

    def refresh_dashboard(self):
        try:
            rows = self.get_all_applications()
            total = len(rows)
            counts = Counter(row[6] for row in rows)

            success_rate = (
                counts.get("Selected", 0) / total * 100
            ) if total else 0

            self.total_label.config(text=str(total))
            self.applied_label.config(text=str(counts.get("Applied", 0)))
            self.interview_label.config(text=str(counts.get("Interview", 0)))
            self.selected_label.config(text=str(counts.get("Selected", 0)))
            self.success_label.config(text=f"{success_rate:.1f}%")

            today = date.today().isoformat()
            upcoming = [
                row for row in rows
                if row[8] and row[8] >= today
                and row[6] not in ("Selected", "Rejected")
            ]
            upcoming.sort(key=lambda row: row[8])

            if upcoming:
                details = [
                    f"{row[1]} ({row[2]}) — {row[8]}"
                    for row in upcoming[:3]
                ]
                message = "Upcoming interviews: " + "  |  ".join(details)
                if len(upcoming) > 3:
                    message += f"  |  +{len(upcoming) - 3} more"
                self.upcoming_label.config(text=message)
            else:
                self.upcoming_label.config(
                    text="Upcoming interviews: None scheduled"
                )

            self.refresh_table()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    # ---------------- CALENDAR & SMART REMINDERS ----------------

    def open_calendar(self):
        """Open a month calendar showing interviews and follow-up dates."""
        existing = getattr(self, "calendar_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    self.refresh_calendar()
                    return
            except tk.TclError:
                pass

        self.calendar_year = date.today().year
        self.calendar_month = date.today().month
        self.calendar_selected_date = date.today()

        self.calendar_window = tk.Toplevel(self.root)
        self.calendar_window.title("JobTrack Pro | Calendar & Reminders")
        self.calendar_window.geometry("1050x700")
        self.calendar_window.minsize(900, 600)
        self.calendar_window.configure(bg=BG)
        self.calendar_window.protocol(
            "WM_DELETE_WINDOW", self.close_calendar
        )

        header = tk.Frame(self.calendar_window, bg=BG)
        header.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(
            header, text="Calendar & Reminders",
            font=("Segoe UI", 21, "bold"), bg=BG, fg=TEXT
        ).pack(side="left")
        tk.Label(
            header,
            text="Plan interviews and follow up at the right time.",
            font=("Segoe UI", 9), bg=BG, fg=MUTED
        ).pack(side="left", padx=15, pady=(8, 0))

        content = tk.Frame(self.calendar_window, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        self.calendar_left = tk.Frame(
            content, bg=CARD, padx=15, pady=15,
            highlightbackground="#334155" if self.dark_mode else "#E5E7EB",
            highlightthickness=1
        )
        self.calendar_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.calendar_right = tk.Frame(
            content, bg=CARD, width=310, padx=15, pady=15,
            highlightbackground="#334155" if self.dark_mode else "#E5E7EB",
            highlightthickness=1
        )
        self.calendar_right.pack(side="right", fill="y")
        self.calendar_right.pack_propagate(False)

        month_nav = tk.Frame(self.calendar_left, bg=CARD)
        month_nav.pack(fill="x", pady=(0, 12))
        tk.Button(
            month_nav, text="‹", command=self.previous_calendar_month,
            bg=BG, fg=TEXT, relief="flat", font=("Segoe UI", 15, "bold"),
            width=3, cursor="hand2"
        ).pack(side="left")
        self.calendar_month_label = tk.Label(
            month_nav, text="", bg=CARD, fg=TEXT,
            font=("Segoe UI", 14, "bold")
        )
        self.calendar_month_label.pack(side="left", expand=True)
        tk.Button(
            month_nav, text="Today", command=self.go_calendar_today,
            bg=PRIMARY, fg="white", relief="flat",
            font=("Segoe UI", 9, "bold"), padx=12, pady=6,
            cursor="hand2"
        ).pack(side="right", padx=(5, 0))
        tk.Button(
            month_nav, text="›", command=self.next_calendar_month,
            bg=BG, fg=TEXT, relief="flat", font=("Segoe UI", 15, "bold"),
            width=3, cursor="hand2"
        ).pack(side="right")

        self.calendar_grid = tk.Frame(self.calendar_left, bg=CARD)
        self.calendar_grid.pack(fill="both", expand=True)

        tk.Label(
            self.calendar_right, text="Selected date",
            font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED
        ).pack(anchor="w")
        self.calendar_selected_label = tk.Label(
            self.calendar_right, text="", font=("Segoe UI", 15, "bold"),
            bg=CARD, fg=TEXT
        )
        self.calendar_selected_label.pack(anchor="w", pady=(3, 14))
        tk.Label(
            self.calendar_right, text="Scheduled items",
            font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 8))
        self.calendar_events_frame = tk.Frame(self.calendar_right, bg=CARD)
        self.calendar_events_frame.pack(fill="both", expand=True)

        tk.Label(
            self.calendar_right,
            text="● Interview     ● Follow-up",
            font=("Segoe UI", 8), bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(8, 0))

        self.refresh_calendar()

    def close_calendar(self):
        if getattr(self, "calendar_window", None) is not None:
            try:
                self.calendar_window.destroy()
            except tk.TclError:
                pass
        self.calendar_window = None

    def previous_calendar_month(self):
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        self.refresh_calendar()

    def next_calendar_month(self):
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        self.refresh_calendar()

    def go_calendar_today(self):
        today = date.today()
        self.calendar_year, self.calendar_month = today.year, today.month
        self.calendar_selected_date = today
        self.refresh_calendar()

    def get_calendar_events(self, year=None, month=None):
        """Return dated interview and follow-up events from SQLite."""
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("""
                SELECT id, company, role, status, interview_date, follow_up_date
                FROM applications
                WHERE interview_date IS NOT NULL OR follow_up_date IS NOT NULL
            """).fetchall()

        events = {}
        for app_id, company, role, status, interview_date, follow_up_date in rows:
            for event_type, event_date in (
                ("Interview", interview_date), ("Follow-up", follow_up_date)
            ):
                if not event_date:
                    continue
                try:
                    parsed = datetime.strptime(event_date, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if year is not None and (parsed.year != year or parsed.month != month):
                    continue
                events.setdefault(parsed, []).append({
                    "id": app_id, "company": company, "role": role,
                    "status": status, "type": event_type
                })
        return events

    def refresh_calendar(self):
        if getattr(self, "calendar_window", None) is None:
            return
        try:
            if not self.calendar_window.winfo_exists():
                return
        except tk.TclError:
            return

        for child in self.calendar_grid.winfo_children():
            child.destroy()

        month_name = date(self.calendar_year, self.calendar_month, 1).strftime("%B %Y")
        self.calendar_month_label.config(text=month_name)
        events = self.get_calendar_events(self.calendar_year, self.calendar_month)
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for col, weekday in enumerate(weekdays):
            tk.Label(
                self.calendar_grid, text=weekday, bg=CARD, fg=MUTED,
                font=("Segoe UI", 9, "bold"), pady=8
            ).grid(row=0, column=col, sticky="nsew", padx=2)
            self.calendar_grid.grid_columnconfigure(col, weight=1, uniform="day")

        weeks = month_calendar.monthcalendar(self.calendar_year, self.calendar_month)
        today = date.today()
        for row_index, week in enumerate(weeks, start=1):
            self.calendar_grid.grid_rowconfigure(row_index, weight=1, uniform="week")
            for col, day_number in enumerate(week):
                if day_number == 0:
                    tk.Frame(self.calendar_grid, bg=BG).grid(
                        row=row_index, column=col, sticky="nsew", padx=2, pady=2
                    )
                    continue

                day_date = date(self.calendar_year, self.calendar_month, day_number)
                day_events = events.get(day_date, [])
                is_selected = day_date == self.calendar_selected_date
                if is_selected:
                    cell_bg, day_fg = ("#312E81", "white")
                elif day_date == today:
                    cell_bg, day_fg = ("#E0E7FF", "#3730A3")
                else:
                    cell_bg, day_fg = (BG, TEXT)

                label = f"{day_number}"
                if day_events:
                    interview_count = sum(e["type"] == "Interview" for e in day_events)
                    follow_count = sum(e["type"] == "Follow-up" for e in day_events)
                    dots = ("●" if interview_count else "") + ("  ◆" if follow_count else "")
                    label += f"\n{dots}"

                button = tk.Button(
                    self.calendar_grid, text=label,
                    command=lambda selected=day_date: self.select_calendar_date(selected),
                    bg=cell_bg, fg=day_fg,
                    activebackground="#C7D2FE", activeforeground=TEXT,
                    relief="flat", bd=0, cursor="hand2",
                    font=("Segoe UI", 10, "bold"), justify="center"
                )
                button.grid(
                    row=row_index, column=col, sticky="nsew", padx=2, pady=2,
                    ipadx=2, ipady=8
                )

        self.show_calendar_events(self.calendar_selected_date)

    def select_calendar_date(self, selected_date):
        self.calendar_selected_date = selected_date
        self.refresh_calendar()

    def show_calendar_events(self, selected_date):
        self.calendar_selected_label.config(
            text=selected_date.strftime("%A, %d %B %Y")
        )
        for child in self.calendar_events_frame.winfo_children():
            child.destroy()

        events = self.get_calendar_events().get(selected_date, [])
        if not events:
            tk.Label(
                self.calendar_events_frame, text="No events scheduled for this date.",
                bg=CARD, fg=MUTED, font=("Segoe UI", 9),
                wraplength=260, justify="left"
            ).pack(anchor="w", pady=8)
            return

        for event in events:
            colour = "#2563EB" if event["type"] == "Interview" else "#0F766E"
            card = tk.Frame(
                self.calendar_events_frame, bg=BG, padx=9, pady=8,
                highlightbackground="#CBD5E1", highlightthickness=1
            )
            card.pack(fill="x", pady=5)
            tk.Label(
                card, text=event["type"], bg=BG, fg=colour,
                font=("Segoe UI", 8, "bold")
            ).pack(anchor="w")
            tk.Label(
                card, text=event["company"], bg=BG, fg=TEXT,
                font=("Segoe UI", 10, "bold"), wraplength=240,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))
            tk.Label(
                card, text=f'{event["role"]} • {event["status"]}',
                bg=BG, fg=MUTED, font=("Segoe UI", 8),
                wraplength=240, justify="left"
            ).pack(anchor="w")
            tk.Button(
                card, text="Open application",
                command=lambda app_id=event["id"]: self.open_application_from_calendar(app_id),
                bg=PRIMARY, fg="white", relief="flat",
                font=("Segoe UI", 8, "bold"), padx=8, pady=4,
                cursor="hand2"
            ).pack(anchor="w", pady=(6, 0))

    def open_application_from_calendar(self, app_id):
        """Load a calendar item into the main application form."""
        try:
            with sqlite3.connect(DB_NAME) as conn:
                row = conn.execute("""
                    SELECT company, role, location, salary, date_applied,
                           status, notes, interview_date, follow_up_date
                    FROM applications WHERE id=?
                """, (app_id,)).fetchone()
            if not row:
                messagebox.showwarning("Not Found", "This application no longer exists.")
                return

            fields = [
                "company", "role", "location", "salary", "date_applied",
                "status", "notes", "interview_date", "follow_up_date"
            ]
            for key, value in zip(fields, row):
                if key in self.entries:
                    self.entries[key].delete(0, "end")
                    self.entries[key].insert(0, value or "")
            self.status_box.set(row[5] or "Applied")
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", row[6] or "")
            self.selected_id = app_id
            self.calendar_window.lift()
        except sqlite3.Error as error:
            messagebox.showerror("Calendar Error", str(error))

    def check_due_reminders(self):
        """Show each due interview/follow-up reminder once per event date."""
        try:
            today = date.today().isoformat()
            due_items = []
            with sqlite3.connect(DB_NAME) as conn:
                records = conn.execute("""
                    SELECT id, company, role, status, interview_date, follow_up_date
                    FROM applications
                    WHERE (interview_date = ? OR follow_up_date <= ?)
                      AND status NOT IN ('Selected', 'Rejected')
                """, (today, today)).fetchall()

                for app_id, company, role, status, interview_date, follow_up_date in records:
                    candidates = []
                    if interview_date == today:
                        candidates.append(("Interview", interview_date))
                    if follow_up_date and follow_up_date <= today:
                        candidates.append(("Follow-up", follow_up_date))

                    for reminder_type, reminder_date in candidates:
                        cursor = conn.execute("""
                            INSERT OR IGNORE INTO reminder_log
                            (application_id, reminder_type, reminder_date, notified_at)
                            VALUES (?, ?, ?, ?)
                        """, (
                            app_id, reminder_type, reminder_date,
                            datetime.now().isoformat(timespec="seconds")
                        ))
                        if cursor.rowcount == 1:
                            due_items.append((company, role, reminder_type, reminder_date))
                conn.commit()

            if due_items:
                lines = [
                    f"• {kind}: {company} — {role} ({event_date})"
                    for company, role, kind, event_date in due_items[:10]
                ]
                if len(due_items) > 10:
                    lines.append(f"...and {len(due_items) - 10} more")
                messagebox.showinfo(
                    "JobTrack Pro Reminders",
                    "You have reminders due:\n\n" + "\n".join(lines)
                )
        except sqlite3.Error as error:
            # Reminder failures should not stop the main application.
            print(f"Reminder check error: {error}")
        finally:
            try:
                if self.root.winfo_exists():
                    self.root.after(60000, self.check_due_reminders)
            except tk.TclError:
                pass

    # ---------------- CSV EXPORT ----------------

    def export_csv(self):
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("""
                SELECT id, company, role, location, salary, date_applied,
                       status, notes, interview_date, follow_up_date
                FROM applications ORDER BY date_applied DESC, id DESC
            """).fetchall()

        if not rows:
            messagebox.showinfo(
                "No Data", "There are no applications to export yet."
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Job Applications",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="jobtrack_applications.csv"
        )
        if not file_path:
            return

        headers = [
            "ID", "Company", "Job Role", "Location", "Salary / Package",
            "Application Date", "Status", "Notes", "Interview Date",
            "Follow-up Date"
        ]

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(rows)

            messagebox.showinfo(
                "Export Successful",
                f"Exported {len(rows)} application(s) successfully.\n\n{file_path}"
            )
        except OSError as error:
            messagebox.showerror("Export Error", str(error))

    # ---------------- ANALYTICS ----------------

    def open_analytics(self):
        rows = self.get_all_applications()

        if not rows:
            messagebox.showinfo(
                "No Data", "Add some applications to view analytics."
            )
            return

        counts = Counter(row[6] for row in rows)
        total = len(rows)
        selected = counts.get("Selected", 0)
        rejected = counts.get("Rejected", 0)

        success_rate = selected / total * 100
        response_rate = (selected + rejected) / total * 100

        window = tk.Toplevel(self.root)
        window.title("JobTrack Pro | Analytics")
        window.geometry("850x650")
        window.minsize(750, 580)
        window.configure(bg=BG)

        tk.Label(
            window, text="Application Analytics",
            font=("Segoe UI", 22, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w", padx=25, pady=(20, 4))

        tk.Label(
            window, text="A visual overview of your job search progress",
            font=("Segoe UI", 10), bg=BG, fg=MUTED
        ).pack(anchor="w", padx=25, pady=(0, 15))

        metrics = tk.Frame(window, bg=BG)
        metrics.pack(fill="x", padx=20, pady=5)

        self.analytics_metric(metrics, "TOTAL APPLICATIONS", str(total))
        self.analytics_metric(metrics, "SUCCESS RATE", f"{success_rate:.1f}%")
        self.analytics_metric(metrics, "RESPONSE RATE", f"{response_rate:.1f}%")

        charts = tk.Frame(window, bg=BG)
        charts.pack(fill="both", expand=True, padx=20, pady=15)

        status_card = tk.Frame(
            charts, bg=CARD, padx=15, pady=15,
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#E5E7EB", highlightthickness=1
        )
        status_card.pack(side="left", fill="both", expand=True, padx=5)

        monthly_card = tk.Frame(
            charts, bg=CARD, padx=15, pady=15,
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#E5E7EB", highlightthickness=1
        )
        monthly_card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(
            status_card, text="Applications by Status",
            font=("Segoe UI", 12, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 10))

        self.draw_status_chart(status_card, counts, total)

        tk.Label(
            monthly_card, text="Applications by Month",
            font=("Segoe UI", 12, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 10))

        self.draw_monthly_chart(monthly_card, rows)

        tk.Label(
            window,
            text=(
                "Success rate = Selected / Total applications.  "
                "Response rate = (Selected + Rejected) / Total applications."
            ),
            font=("Segoe UI", 8), bg=BG, fg=MUTED, wraplength=800
        ).pack(padx=20, pady=(0, 15))

    def analytics_metric(self, parent, title, value):
        card = tk.Frame(
            parent, bg=CARD, padx=15, pady=12,
            highlightbackground="#334155" if getattr(self, "dark_mode", False) else "#E5E7EB", highlightthickness=1
        )
        card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(
            card, text=title, font=("Segoe UI", 8, "bold"),
            bg=CARD, fg=MUTED
        ).pack(anchor="w")
        tk.Label(
            card, text=value, font=("Segoe UI", 21, "bold"),
            bg=CARD, fg=PRIMARY
        ).pack(anchor="w", pady=(4, 0))

    def draw_status_chart(self, parent, counts, total):
        canvas = tk.Canvas(
            parent, width=350, height=390,
            bg=CARD, highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)

        statuses = [
            ("Applied", "#6366F1"),
            ("Interview", "#0EA5E9"),
            ("Selected", "#10B981"),
            ("Rejected", "#EF4444")
        ]

        y = 20
        for status, colour in statuses:
            value = counts.get(status, 0)
            percentage = value / total if total else 0

            canvas.create_text(
                8, y + 9, text=status, anchor="w",
                font=("Segoe UI", 9, "bold"), fill=TEXT
            )
            canvas.create_rectangle(
                95, y, 285, y + 19, fill="#E5E7EB", outline=""
            )

            bar_width = 190 * percentage
            if bar_width > 0:
                canvas.create_rectangle(
                    95, y, 95 + bar_width, y + 19,
                    fill=colour, outline=""
                )

            canvas.create_text(
                295, y + 9,
                text=f"{value} ({percentage:.0%})",
                anchor="w", font=("Segoe UI", 8), fill=MUTED
            )
            y += 55

        canvas.create_text(
            8, y + 15,
            text=f"Total applications: {total}",
            anchor="w", font=("Segoe UI", 10, "bold"), fill=TEXT
        )

    def draw_monthly_chart(self, parent, rows):
        canvas = tk.Canvas(
            parent, width=350, height=390,
            bg=CARD, highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)

        monthly = Counter()
        for row in rows:
            try:
                month_key = datetime.strptime(
                    row[5], "%Y-%m-%d"
                ).strftime("%Y-%m")
                monthly[month_key] += 1
            except (ValueError, TypeError):
                continue

        if not monthly:
            canvas.create_text(
                175, 100, text="No valid application dates",
                fill=MUTED, font=("Segoe UI", 10)
            )
            return

        recent_months = sorted(monthly.keys())[-6:]
        max_value = max(monthly[m] for m in recent_months) or 1

        left, bottom, chart_height = 35, 300, 210
        canvas.create_line(
            left, bottom, 325, bottom, fill="#9CA3AF", width=1
        )

        bar_width = 28
        available = 280
        gap = (
            available - len(recent_months) * bar_width
        ) / (len(recent_months) + 1)

        for index, month in enumerate(recent_months):
            value = monthly[month]
            height = chart_height * value / max_value
            x1 = left + gap * (index + 1) + bar_width * index
            x2 = x1 + bar_width
            y1 = bottom - height

            canvas.create_rectangle(
                x1, y1, x2, bottom, fill=PRIMARY, outline=""
            )
            canvas.create_text(
                (x1 + x2) / 2, y1 - 12,
                text=str(value), fill=TEXT,
                font=("Segoe UI", 9, "bold")
            )
            canvas.create_text(
                (x1 + x2) / 2, bottom + 18,
                text=datetime.strptime(month, "%Y-%m").strftime("%b %y"),
                fill=MUTED, font=("Segoe UI", 8)
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = JobTrackPro(root)
    root.mainloop()
