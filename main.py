
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime


DB_NAME = "jobtrack.db"

STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview",
    "Selected",
    "Rejected"
]


class JobTrackPro:

    def __init__(self, root):
        self.root = root
        self.root.title("JobTrack Pro | Job Application Manager")
        self.root.geometry("1200x780")
        self.root.minsize(1000, 680)

        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()

        self.create_database()
        self.setup_style()
        self.create_widgets()
        self.load_applications()
        self.update_dashboard()

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    # DATABASE

    def create_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT,
                salary TEXT,
                date_applied TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT
            )
        """)
        self.conn.commit()

    # STYLE

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            rowheight=32,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 9),
            padding=7
        )

    # MAIN GUI

    def create_widgets(self):

        header = tk.Frame(
            self.root,
            bg="#172554",
            height=85
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="JOBTRACK PRO",
            font=("Segoe UI", 23, "bold"),
            fg="white",
            bg="#172554"
        ).pack(side="left", padx=25, pady=18)

        tk.Label(
            header,
            text="Manage your career journey",
            font=("Segoe UI", 11),
            fg="#CBD5E1",
            bg="#172554"
        ).pack(side="right", padx=25)

        # DASHBOARD CARDS

        cards_frame = tk.Frame(self.root, bg="#F1F5F9")
        cards_frame.pack(fill="x", padx=20, pady=18)

        self.total_label = self.create_card(
            cards_frame, "TOTAL APPLICATIONS", "0"
        )

        self.applied_label = self.create_card(
            cards_frame, "APPLIED", "0"
        )

        self.interview_label = self.create_card(
            cards_frame, "INTERVIEWS", "0"
        )

        self.selected_label = self.create_card(
            cards_frame, "SELECTED", "0"
        )

        # APPLICATION FORM

        form = tk.LabelFrame(
            self.root,
            text="  Add / Edit Job Application  ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=12
        )
        form.pack(fill="x", padx=20, pady=5)

        self.company_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.date_var = tk.StringVar(
            value=datetime.today().strftime("%Y-%m-%d")
        )
        self.status_var = tk.StringVar(value="Applied")

        tk.Label(form, text="Company Name").grid(
            row=0, column=0, sticky="w", padx=7, pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.company_var,
            width=25
        ).grid(row=0, column=1, padx=7, pady=5)

        tk.Label(form, text="Job Role").grid(
            row=0, column=2, sticky="w", padx=7
        )

        ttk.Entry(
            form,
            textvariable=self.role_var,
            width=25
        ).grid(row=0, column=3, padx=7, pady=5)

        tk.Label(form, text="Location").grid(
            row=0, column=4, sticky="w", padx=7
        )

        ttk.Entry(
            form,
            textvariable=self.location_var,
            width=22
        ).grid(row=0, column=5, padx=7, pady=5)

        tk.Label(form, text="Salary").grid(
            row=1, column=0, sticky="w", padx=7, pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.salary_var,
            width=25
        ).grid(row=1, column=1, padx=7, pady=5)

        tk.Label(form, text="Date Applied").grid(
            row=1, column=2, sticky="w", padx=7
        )

        ttk.Entry(
            form,
            textvariable=self.date_var,
            width=25
        ).grid(row=1, column=3, padx=7, pady=5)

        tk.Label(form, text="Status").grid(
            row=1, column=4, sticky="w", padx=7
        )

        ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=STATUSES,
            state="readonly",
            width=20
        ).grid(row=1, column=5, padx=7, pady=5)

        tk.Label(form, text="Notes").grid(
            row=2, column=0, sticky="w", padx=7, pady=5
        )

        self.notes_entry = ttk.Entry(form, width=95)
        self.notes_entry.grid(
            row=2,
            column=1,
            columnspan=5,
            sticky="ew",
            padx=7,
            pady=5
        )

        # FORM BUTTONS

        button_frame = tk.Frame(form)
        button_frame.grid(
            row=3,
            column=0,
            columnspan=6,
            pady=12
        )

        ttk.Button(
            button_frame,
            text="Add Application",
            command=self.add_application
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Update Selected",
            command=self.update_application
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Clear Form",
            command=self.clear_form
        ).pack(side="left", padx=5)

        # SEARCH AND FILTER

        search_frame = tk.LabelFrame(
            self.root,
            text="  Search Applications  ",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        search_frame.pack(fill="x", padx=20, pady=10)

        self.search_var = tk.StringVar()

        ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="Search",
            command=self.search_applications
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="Show All",
            command=self.reset_search
        ).pack(side="left", padx=5)

        # APPLICATION TABLE

        table_frame = tk.LabelFrame(
            self.root,
            text="  Job Application History  ",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        columns = (
            "ID",
            "Company",
            "Role",
            "Location",
            "Salary",
            "Date",
            "Status"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        widths = {
            "ID": 45,
            "Company": 160,
            "Role": 180,
            "Location": 140,
            "Salary": 110,
            "Date": 110,
            "Status": 120
        }

        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(side="right", fill="y")

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_application
        )

        # DELETE BUTTON

        ttk.Button(
            self.root,
            text="Delete Selected Application",
            command=self.delete_application
        ).pack(pady=12)

    # DASHBOARD CARD

    def create_card(self, parent, title, value):

        card = tk.LabelFrame(
            parent,
            text=title,
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=10
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=7
        )

        label = tk.Label(
            card,
            text=value,
            font=("Segoe UI", 22, "bold"),
            fg="#1D4ED8"
        )

        label.pack()

        return label

    # ADD APPLICATION

    def add_application(self):

        company = self.company_var.get().strip()
        role = self.role_var.get().strip()
        location = self.location_var.get().strip()
        salary = self.salary_var.get().strip()
        date_applied = self.date_var.get().strip()
        status = self.status_var.get()
        notes = self.notes_entry.get().strip()

        if not company or not role:
            messagebox.showerror(
                "Validation Error",
                "Company name and job role are required."
            )
            return

        try:
            datetime.strptime(date_applied, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Use YYYY-MM-DD date format."
            )
            return

        self.cursor.execute("""
            INSERT INTO applications
            (company, role, location, salary, date_applied, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            company,
            role,
            location,
            salary,
            date_applied,
            status,
            notes
        ))

        self.conn.commit()

        self.clear_form()
        self.load_applications()
        self.update_dashboard()

        messagebox.showinfo(
            "Success",
            "Job application added successfully!"
        )

    # LOAD APPLICATIONS

    def load_applications(self, query=None, params=()):

        for item in self.tree.get_children():
            self.tree.delete(item)

        if query is None:
            query = """
                SELECT id, company, role, location,
                       salary, date_applied, status
                FROM applications
                ORDER BY date_applied DESC, id DESC
            """

        self.cursor.execute(query, params)

        for row in self.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    # UPDATE APPLICATION

    def update_application(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Select an application to update."
            )
            return

        company = self.company_var.get().strip()
        role = self.role_var.get().strip()
        location = self.location_var.get().strip()
        salary = self.salary_var.get().strip()
        date_applied = self.date_var.get().strip()
        status = self.status_var.get()
        notes = self.notes_entry.get().strip()

        if not company or not role:
            messagebox.showerror(
                "Validation Error",
                "Company name and job role are required."
            )
            return

        try:
            datetime.strptime(date_applied, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Use YYYY-MM-DD date format."
            )
            return

        application_id = self.tree.item(
            selected[0], "values"
        )[0]

        self.cursor.execute("""
            UPDATE applications
            SET company=?, role=?, location=?, salary=?,
                date_applied=?, status=?, notes=?
            WHERE id=?
        """, (
            company,
            role,
            location,
            salary,
            date_applied,
            status,
            notes,
            application_id
        ))

        self.conn.commit()

        self.clear_form()
        self.load_applications()
        self.update_dashboard()

        messagebox.showinfo(
            "Updated",
            "Application updated successfully!"
        )

    # DELETE APPLICATION

    def delete_application(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Select an application to delete."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this application?"
        )

        if not confirm:
            return

        application_id = self.tree.item(
            selected[0], "values"
        )[0]

        self.cursor.execute(
            "DELETE FROM applications WHERE id=?",
            (application_id,)
        )

        self.conn.commit()

        self.clear_form()
        self.load_applications()
        self.update_dashboard()

        messagebox.showinfo(
            "Deleted",
            "Application deleted successfully!"
        )

    # SELECT APPLICATION

    def select_application(self, event=None):

        selected = self.tree.selection()

        if not selected:
            return

        application_id = self.tree.item(
            selected[0], "values"
        )[0]

        self.cursor.execute("""
            SELECT company, role, location, salary,
                   date_applied, status, notes
            FROM applications
            WHERE id=?
        """, (application_id,))

        row = self.cursor.fetchone()

        if row:

            self.company_var.set(row[0])
            self.role_var.set(row[1])
            self.location_var.set(row[2] or "")
            self.salary_var.set(row[3] or "")
            self.date_var.set(row[4])
            self.status_var.set(row[5])

            self.notes_entry.delete(0, tk.END)
            self.notes_entry.insert(0, row[6] or "")

    # CLEAR FORM

    def clear_form(self):

        self.company_var.set("")
        self.role_var.set("")
        self.location_var.set("")
        self.salary_var.set("")
        self.date_var.set(
            datetime.today().strftime("%Y-%m-%d")
        )
        self.status_var.set("Applied")

        self.notes_entry.delete(0, tk.END)

        for item in self.tree.selection():
            self.tree.selection_remove(item)

    # SEARCH

    def search_applications(self):

        keyword = self.search_var.get().strip()

        if not keyword:
            self.load_applications()
            return

        query = """
            SELECT id, company, role, location,
                   salary, date_applied, status
            FROM applications
            WHERE company LIKE ?
               OR role LIKE ?
               OR location LIKE ?
            ORDER BY date_applied DESC, id DESC
        """

        search_value = f"%{keyword}%"

        self.load_applications(
            query,
            (search_value, search_value, search_value)
        )

    def reset_search(self):

        self.search_var.set("")
        self.load_applications()

    # DASHBOARD SUMMARY

    def update_dashboard(self):

        self.cursor.execute("""
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
        """)

        status_counts = dict(self.cursor.fetchall())

        total = sum(status_counts.values())

        applied = status_counts.get("Applied", 0)
        interviews = status_counts.get("Interview", 0)
        selected = status_counts.get("Selected", 0)

        self.total_label.config(text=str(total))
        self.applied_label.config(text=str(applied))
        self.interview_label.config(text=str(interviews))
        self.selected_label.config(text=str(selected))

    # CLOSE APPLICATION

    def close_app(self):

        self.conn.close()
        self.root.destroy()


# RUN APPLICATION

if __name__ == "__main__":

    root = tk.Tk()
    app = JobTrackPro(root)
    root.mainloop()
