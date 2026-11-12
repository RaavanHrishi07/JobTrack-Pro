
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date, timedelta

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
        self.root.geometry("1200x760")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG)

        self.selected_id = None
        self.sort_order = "Newest First"
        self.status_filter = tk.StringVar(value="All Statuses")
        self.search_var = tk.StringVar()

        self.create_database()
        self.build_ui()
        self.refresh_dashboard()

    # ---------------- DATABASE ----------------

    def create_database(self):
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

            # Upgrade an existing database without deleting old records.
            cursor.execute("PRAGMA table_info(applications)")
            columns = [column[1] for column in cursor.fetchall()]

            if "interview_date" not in columns:
                cursor.execute(
                    "ALTER TABLE applications ADD COLUMN interview_date TEXT"
                )

            conn.commit()

    # ---------------- UI ----------------

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=25, pady=(20, 10))

        tk.Label(
            header,
            text="JobTrack Pro",
            font=("Segoe UI", 25, "bold"),
            bg=BG,
            fg=TEXT
        ).pack(side="left")

        tk.Label(
            header,
            text="Your personal job application dashboard",
            font=("Segoe UI", 10),
            bg=BG,
            fg=MUTED
        ).pack(side="left", padx=18, pady=(10, 0))

        self.cards_frame = tk.Frame(self.root, bg=BG)
        self.cards_frame.pack(fill="x", padx=25, pady=10)

        self.total_label = self.create_summary_card(
            self.cards_frame, "TOTAL APPLICATIONS", "0"
        )
        self.applied_label = self.create_summary_card(
            self.cards_frame, "APPLIED", "0"
        )
        self.interview_label = self.create_summary_card(
            self.cards_frame, "INTERVIEWS", "0"
        )
        self.selected_label = self.create_summary_card(
            self.cards_frame, "SELECTED", "0"
        )

        self.upcoming_frame = tk.Frame(
            self.root, bg="#EEF2FF", highlightbackground="#C7D2FE",
            highlightthickness=1
        )
        self.upcoming_frame.pack(fill="x", padx=25, pady=(5, 12))

        self.upcoming_label = tk.Label(
            self.upcoming_frame,
            text="Upcoming interviews: None",
            font=("Segoe UI", 10, "bold"),
            bg="#EEF2FF",
            fg="#3730A3",
            anchor="w",
            padx=15,
            pady=10
        )
        self.upcoming_label.pack(fill="x")

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=25, pady=5)

        self.create_form(main)
        self.create_table_section(main)

    def create_summary_card(self, parent, title, value):
        card = tk.Frame(
            parent, bg=CARD, padx=18, pady=14,
            highlightbackground="#E5E7EB", highlightthickness=1
        )
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            card, text=title, font=("Segoe UI", 9, "bold"),
            bg=CARD, fg=MUTED
        ).pack(anchor="w")

        label = tk.Label(
            card, text=value, font=("Segoe UI", 23, "bold"),
            bg=CARD, fg=PRIMARY
        )
        label.pack(anchor="w", pady=(5, 0))
        return label

    def create_form(self, parent):
        form = tk.Frame(
            parent, bg=CARD, padx=18, pady=18,
            highlightbackground="#E5E7EB", highlightthickness=1
        )
        form.pack(side="left", fill="y", padx=(0, 15))

        tk.Label(
            form, text="Application Details",
            font=("Segoe UI", 15, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 15))

        self.entries = {}

        fields = [
            ("Company Name", "company"),
            ("Job Role", "role"),
            ("Location", "location"),
            ("Salary / Package", "salary"),
            ("Application Date (YYYY-MM-DD)", "date_applied"),
            ("Interview Date (YYYY-MM-DD)", "interview_date")
        ]

        for label_text, key in fields:
            tk.Label(
                form, text=label_text, font=("Segoe UI", 9, "bold"),
                bg=CARD, fg=MUTED
            ).pack(anchor="w", pady=(5, 3))

            entry = ttk.Entry(form, width=32, font=("Segoe UI", 10))
            entry.pack(fill="x", pady=(0, 5))
            self.entries[key] = entry

        self.entries["date_applied"].insert(0, date.today().isoformat())

        tk.Label(
            form, text="Application Status",
            font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 3))

        self.status_box = ttk.Combobox(
            form,
            values=["Applied", "Interview", "Selected", "Rejected"],
            state="readonly",
            width=29
        )
        self.status_box.set("Applied")
        self.status_box.pack(fill="x", pady=(0, 8))

        tk.Label(
            form, text="Notes",
            font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 3))

        self.notes_text = tk.Text(
            form, width=32, height=4, font=("Segoe UI", 10),
            relief="solid", bd=1, wrap="word"
        )
        self.notes_text.pack(fill="x", pady=(0, 12))

        self.add_button = tk.Button(
            form, text="＋ Add Application",
            command=self.add_application,
            bg=PRIMARY, fg="white", activebackground="#4338CA",
            activeforeground="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", pady=9
        )
        self.add_button.pack(fill="x", pady=3)

        tk.Button(
            form, text="Update Selected",
            command=self.update_application,
            bg="#0F766E", fg="white", activebackground="#115E59",
            activeforeground="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", pady=9
        ).pack(fill="x", pady=3)

        tk.Button(
            form, text="Delete Selected",
            command=self.delete_application,
            bg="#DC2626", fg="white", activebackground="#B91C1C",
            activeforeground="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", pady=9
        ).pack(fill="x", pady=3)

        tk.Button(
            form, text="Clear Form",
            command=self.clear_form,
            bg="#E5E7EB", fg=TEXT, activebackground="#D1D5DB",
            font=("Segoe UI", 10, "bold"), relief="flat",
            cursor="hand2", pady=9
        ).pack(fill="x", pady=3)

    def create_table_section(self, parent):
        section = tk.Frame(
            parent, bg=CARD, padx=15, pady=15,
            highlightbackground="#E5E7EB", highlightthickness=1
        )
        section.pack(side="left", fill="both", expand=True)

        tk.Label(
            section, text="Your Applications",
            font=("Segoe UI", 15, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 12))

        controls = tk.Frame(section, bg=CARD)
        controls.pack(fill="x", pady=(0, 10))

        self.search_entry = ttk.Entry(
            controls, textvariable=self.search_var,
            font=("Segoe UI", 10)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.search_entry.bind("<Return>", lambda event: self.refresh_table())

        tk.Button(
            controls, text="Search", command=self.refresh_table,
            bg=PRIMARY, fg="white", relief="flat", padx=10, pady=5
        ).pack(side="left", padx=3)

        tk.Button(
            controls, text="Reset", command=self.reset_filters,
            bg="#E5E7EB", fg=TEXT, relief="flat", padx=10, pady=5
        ).pack(side="left", padx=3)

        filters = tk.Frame(section, bg=CARD)
        filters.pack(fill="x", pady=(0, 10))

        tk.Label(
            filters, text="Status:", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 5))

        self.status_filter_box = ttk.Combobox(
            filters, textvariable=self.status_filter,
            values=["All Statuses", "Applied", "Interview", "Selected", "Rejected"],
            state="readonly", width=16
        )
        self.status_filter_box.pack(side="left", padx=(0, 12))
        self.status_filter_box.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_table()
        )

        tk.Label(
            filters, text="Sort:", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 5))

        self.sort_box = ttk.Combobox(
            filters,
            values=["Newest First", "Oldest First"],
            state="readonly", width=15
        )
        self.sort_box.set("Newest First")
        self.sort_box.pack(side="left")
        self.sort_box.bind(
            "<<ComboboxSelected>>", self.change_sort
        )

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
            "id": "ID",
            "company": "Company",
            "role": "Job Role",
            "location": "Location",
            "date_applied": "Applied On",
            "status": "Status",
            "interview_date": "Interview Date"
        }

        widths = {
            "id": 40, "company": 115, "role": 120,
            "location": 90, "date_applied": 90,
            "status": 85, "interview_date": 105
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column, width=widths[column], anchor="center"
            )

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
            font=("Segoe UI", 9)
        )
        self.result_label.pack(anchor="w", pady=(8, 0))

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

        return data

    # ---------------- CRUD ----------------

    def add_application(self):
        data = self.get_form_data()
        if not data:
            return

        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("""
                    INSERT INTO applications
                    (company, role, location, salary, date_applied,
                     status, notes, interview_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["company"], data["role"], data["location"],
                    data["salary"], data["date_applied"], data["status"],
                    data["notes"], data["interview_date"] or None
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
                        date_applied=?, status=?, notes=?, interview_date=?
                    WHERE id=?
                """, (
                    data["company"], data["role"], data["location"],
                    data["salary"], data["date_applied"], data["status"],
                    data["notes"], data["interview_date"] or None,
                    self.selected_id
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

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this application?"
        )

        if not confirm:
            return

        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute(
                    "DELETE FROM applications WHERE id=?",
                    (self.selected_id,)
                )

            messagebox.showinfo("Deleted", "Application deleted successfully.")
            self.clear_form()
            self.refresh_dashboard()

        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def clear_form(self):
        self.selected_id = None

        for key, entry in self.entries.items():
            entry.delete(0, "end")

        self.entries["date_applied"].insert(0, date.today().isoformat())
        self.status_box.set("Applied")
        self.notes_text.delete("1.0", "end")

        for item in self.tree.selection():
            self.tree.selection_remove(item)

        self.add_button.config(text="＋ Add Application")

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
                           status, notes, interview_date
                    FROM applications WHERE id=?
                """, (self.selected_id,)).fetchone()

            if not row:
                return

            keys = [
                "company", "role", "location", "salary",
                "date_applied", "status", "notes", "interview_date"
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

        query = """
            SELECT id, company, role, location, date_applied,
                   status, interview_date
            FROM applications
            WHERE (
                company LIKE ? OR role LIKE ? OR location LIKE ?
            )
        """
        search_pattern = f"%{search_text}%"
        params = [search_pattern, search_pattern, search_pattern]

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
                    "", "end", values=(
                        row[0], row[1], row[2], row[3],
                        row[4], row[5], row[6] or "—"
                    ), tags=(tag,)
                )

            self.result_label.config(
                text=f"Showing {len(rows)} application(s)"
            )

        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    # ---------------- DASHBOARD ----------------

    def refresh_dashboard(self):
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM applications")
                total = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT status, COUNT(*)
                    FROM applications GROUP BY status
                """)
                counts = dict(cursor.fetchall())

                cursor.execute("""
                    SELECT company, role, interview_date
                    FROM applications
                    WHERE interview_date IS NOT NULL
                      AND interview_date >= ?
                      AND status NOT IN ('Selected', 'Rejected')
                    ORDER BY interview_date ASC
                """, (date.today().isoformat(),))

                upcoming = cursor.fetchall()

            self.total_label.config(text=str(total))
            self.applied_label.config(text=str(counts.get("Applied", 0)))
            self.interview_label.config(text=str(counts.get("Interview", 0)))
            self.selected_label.config(text=str(counts.get("Selected", 0)))

            if upcoming:
                details = []
                for company, role, interview_date in upcoming[:3]:
                    details.append(
                        f"{company} ({role}) — {interview_date}"
                    )

                remaining = len(upcoming) - len(details)
                message = "Upcoming interviews: " + "  |  ".join(details)

                if remaining > 0:
                    message += f"  |  +{remaining} more"

                self.upcoming_label.config(text=message)
            else:
                self.upcoming_label.config(
                    text="Upcoming interviews: None scheduled"
                )

            self.refresh_table()

        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    app = JobTrackPro(root)
    root.mainloop()
