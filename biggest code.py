#!/usr/bin/env python3
# python_project_healthcare_full.py
# Final combined Healthcare App (single-file). Run locally (IDLE / VS Code / PyCharm).

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime
import csv
import threading
import os
import sys

# Try to import matplotlib for graphs; fallback if missing
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

# ---------------------------
# Configuration / Theme
# ---------------------------
APP_TITLE = "💊 Python Project Healthcare (Final)"
DB_FILE = "healthcare_full.db"
DEFAULT_BG = "#e8f5e9"    # light green
DARK_BG = "#2e2e2e"
LANG_EN = "EN"
LANG_HI = "HI"

# Simple multi-language map for a few UI strings
LANG_MAP = {
    "title": {LANG_EN: "Python Project Healthcare", LANG_HI: "पायथन हेल्थकेयर प्रोजेक्ट"},
    "add_patient": {LANG_EN: "Add Patient", LANG_HI: "रोगी जोड़ें"},
    "add_report": {LANG_EN: "Add Report", LANG_HI: "रिपोर्ट जोड़ें"},
    "view_reports": {LANG_EN: "View Reports", LANG_HI: "रिपोर्ट देखें"},
    "disease_info": {LANG_EN: "Disease Info", LANG_HI: "रोग जानकारी"},
    "symptom_checker": {LANG_EN: "Symptom Checker", LANG_HI: "लक्षण जाँच"},
    "export_csv": {LANG_EN: "Export Reports (CSV)", LANG_HI: "रिपोर्ट निर्यात (CSV)"},
    "reminders": {LANG_EN: "Reminders", LANG_HI: "रिमाइंडर"},
    "sos": {LANG_EN: "Emergency SOS", LANG_HI: "आपातकालीन SOS"},
    "logout": {LANG_EN: "Logout", LANG_HI: "लॉग आउट"},
    "login": {LANG_EN: "Login", LANG_HI: "लॉगिन"},
    "register": {LANG_EN: "Register", LANG_HI: "पंजीकरण"},
    "mode": {LANG_EN: "Dark Mode", LANG_HI: "डार्क मोड"},
}

# ---------------------------
# Database setup
# ---------------------------
def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_conn() as con:
        cur = con.cursor()
        # users for simple login
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'patient' -- 'admin' or 'patient' or 'doctor'
            );
        """)
        # patients
        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                contact TEXT,
                created_at TEXT
            );
        """)
        # reports (monthly)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                month TEXT NOT NULL,  -- 'YYYY-MM'
                bp_systolic INTEGER,
                bp_diastolic INTEGER,
                sugar REAL,
                uric_acid REAL,
                created_at TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            );
        """)
        # disease table (editable via app)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diseases(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                details TEXT,
                symptoms TEXT,
                treatable INTEGER, -- 1 for treatable (medicines), 0 for needs doctor
                medicines TEXT,
                hospitals TEXT,
                notes TEXT
            );
        """)
        # reminders
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reminders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                patient_id INTEGER,
                medicine TEXT,
                remind_at TEXT,
                done INTEGER DEFAULT 0,
                created_at TEXT
            );
        """)
        # hospitals (optional editable list)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hospitals(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                city TEXT,
                contact TEXT
            );
        """)
        con.commit()
    seed_initial_data()

def seed_initial_data():
    """Insert some default diseases, hospitals and an admin user if not present."""
    with get_conn() as con:
        cur = con.cursor()
        # admin user
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO users(username, password, role) VALUES (?,?,?)", ("admin", "admin123", "admin"))
        # default hospitals
        cur.execute("SELECT COUNT(*) FROM hospitals")
        if cur.fetchone()[0] == 0:
            hospitals = [
                ("AIIMS Delhi", "Delhi", "011-2658xxxx"),
                ("Apollo Hospitals", "Chennai", "044-2829xxxx"),
                ("Fortis", "New Delhi", "011-4706xxxx"),
                ("Max Healthcare", "New Delhi", "011-4150xxxx"),
            ]
            cur.executemany("INSERT INTO hospitals(name, city, contact) VALUES(?,?,?)", hospitals)
        # default diseases (10+)
        cur.execute("SELECT COUNT(*) FROM diseases")
        if cur.fetchone()[0] == 0:
            defaults = [
                ("fever", "Temporary rise in body temperature", "fever,chills,headache", 1, "Paracetamol, Ibuprofen", "", "Consult if >3 days"),
                ("diabetes", "Chronic high blood sugar", "thirst,urination,fatigue", 0, "", "AIIMS Delhi, Apollo", "Long-term care"),
                ("hypertension", "High blood pressure", "headache,breathlessness", 0, "", "Cardiology Centers", "Monitor regularly"),
                ("common cold", "Viral URTI", "sneezing,cough,sore throat", 1, "Antihistamines, Decongestants", "", "Usually self-limited"),
                ("malaria", "Mosquito-borne parasitic infection", "fever,chills", 1, "ACT, Chloroquine", "Infectious Disease Hospitals", "Diagnose with test"),
                ("asthma", "Chronic airway inflammation", "wheezing,shortness of breath", 0, "Inhalers (Salbutamol)", "Pulmonology Centers", "Doctor plan needed"),
                ("covid-19", "Viral infection SARS-CoV-2", "fever,cough,loss of smell", 0, "Supportive care", "COVID Hospitals", "Test and isolate"),
                ("dengue", "Mosquito-borne viral infection", "fever,joint pain,rash", 0, "Supportive care (hydration)", "Dengue care units", "Avoid NSAIDs"),
                ("tuberculosis", "Bacterial lung infection", "cough,weight loss,fever", 0, "DOTS therapy", "TB Centers", "Long supervised treatment"),
                ("migraine", "Neurological headaches", "throbbing headache,nausea", 1, "Pain relievers, Triptans", "", "Avoid triggers"),
            ]
            cur.executemany(
                "INSERT INTO diseases(name, details, symptoms, treatable, medicines, hospitals, notes) VALUES(?,?,?,?,?,?,?)",
                defaults
            )
        con.commit()

# ---------------------------
# Utility helpers
# ---------------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def month_str():
    return datetime.now().strftime("%Y-%m")

def parse_bp(bp_text):
    if not bp_text: return None, None
    try:
        if "/" in bp_text:
            a, b = bp_text.split("/", 1)
            return int(a.strip()), int(b.strip())
        else:
            return int(bp_text.strip()), None
    except:
        return None, None

# ---------------------------
# App Class (Tk)
# ---------------------------
class HealthcareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x620")
        self.lang = LANG_EN
        self.dark = False
        self.current_user = None  # (id, username, role)
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Top toolbar: language switch, dark mode, logout
        toolbar = tk.Frame(self, bg=DEFAULT_BG)
        toolbar.pack(side="top", fill="x")

        self.title_label = tk.Label(toolbar, text=LANG_MAP["title"][self.lang], font=("Helvetica", 16, "bold"), bg=DEFAULT_BG)
        self.title_label.pack(side="left", padx=10, pady=8)

        # Language toggle
        self.lang_btn = ttk.Button(toolbar, text="हिंदी", width=8, command=self.toggle_language)
        self.lang_btn.pack(side="right", padx=6)

        # Dark mode toggle
        self.mode_btn = ttk.Button(toolbar, text=LANG_MAP["mode"][self.lang], width=12, command=self.toggle_mode)
        self.mode_btn.pack(side="right", padx=6)

        # Logout / Login buttons
        self.logout_btn = ttk.Button(toolbar, text=LANG_MAP["logout"][self.lang], width=10, command=self.logout)
        self.logout_btn.pack(side="right", padx=6)
        self.login_btn = ttk.Button(toolbar, text=LANG_MAP["login"][self.lang], width=10, command=self.open_login)
        self.login_btn.pack(side="right", padx=6)

        # Main notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        # Patient tab
        self.tab_patient = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_patient, text="Patients")

        # Disease tab
        self.tab_disease = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_disease, text="Diseases")

        # Reports tab
        self.tab_reports = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reports, text="Reports")

        # Tools tab (reminders, SOS, export)
        self.tab_tools = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tools, text="Tools")

        # Build contents
        self.build_patients_tab()
        self.build_diseases_tab()
        self.build_reports_tab()
        self.build_tools_tab()

        # Initial mode & language
        self.apply_theme()
        self.update_language()

    # ---------------------------
    # Theme & Language
    # ---------------------------
    def toggle_language(self):
        self.lang = LANG_HI if self.lang == LANG_EN else LANG_EN
        self.update_language()

    def update_language(self):
        self.title_label.config(text=LANG_MAP["title"][self.lang])
        self.mode_btn.config(text=LANG_MAP["mode"][self.lang])
        self.logout_btn.config(text=LANG_MAP["logout"][self.lang])
        self.login_btn.config(text=LANG_MAP["login"][self.lang])
        # update other labels that are dynamic if needed

    def toggle_mode(self):
        self.dark = not self.dark
        self.apply_theme()

    def apply_theme(self):
        bg = DARK_BG if self.dark else DEFAULT_BG
        fg = "white" if self.dark else "black"
        style = ttk.Style()
        if sys.platform == "win32":
            style.theme_use('clam')
        style.configure("TButton", padding=6)
        # apply background
        self.configure(bg=bg)
        self.title_label.config(bg=bg, fg=fg)
        # iterate children and set bg where appropriate
        for child in self.winfo_children():
            try:
                child.config(bg=bg)
            except:
                pass

    # ---------------------------
    # Patients Tab
    # ---------------------------
    def build_patients_tab(self):
        frm = self.tab_patient
        left = ttk.Frame(frm)
        left.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(left, text="Name:").grid(row=0, column=0, sticky="w", pady=4)
        self.p_name = ttk.Entry(left, width=25); self.p_name.grid(row=0, column=1, pady=4)

        ttk.Label(left, text="Age:").grid(row=1, column=0, sticky="w", pady=4)
        self.p_age = ttk.Entry(left, width=25); self.p_age.grid(row=1, column=1, pady=4)

        ttk.Label(left, text="Gender:").grid(row=2, column=0, sticky="w", pady=4)
        self.p_gender = ttk.Entry(left, width=25); self.p_gender.grid(row=2, column=1, pady=4)

        ttk.Label(left, text="Contact:").grid(row=3, column=0, sticky="w", pady=4)
        self.p_contact = ttk.Entry(left, width=25); self.p_contact.grid(row=3, column=1, pady=4)

        ttk.Button(left, text="Add Patient", command=self.add_patient).grid(row=4, column=0, columnspan=2, pady=8)

        # Right: patient list
        right = ttk.Frame(frm)
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        cols = ("id", "name", "age", "gender", "contact")
        self.p_table = ttk.Treeview(right, columns=cols, show="headings", height=15)
        for c in cols:
            self.p_table.heading(c, text=c.upper())
            self.p_table.column(c, width=100)
        self.p_table.pack(fill="both", expand=True)
        self.p_table.bind("<Double-1>", lambda e: self.open_patient_reports())

        ttk.Button(right, text="Refresh List", command=self.refresh_patients).pack(pady=6)
        self.refresh_patients()

    def add_patient(self):
        name = self.p_name.get().strip()
        age = None
        try:
            age = int(self.p_age.get().strip())
        except:
            age = None
        gender = self.p_gender.get().strip()
        contact = self.p_contact.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required")
            return
        with get_conn() as con:
            con.execute(
                "INSERT INTO patients(name, age, gender, contact, created_at) VALUES (?,?,?,?,?)",
                (name, age, gender, contact, now_str())
            )
            con.commit()
        messagebox.showinfo("Saved", f"Patient {name} added")
        self.p_name.delete(0, "end"); self.p_age.delete(0, "end"); self.p_gender.delete(0, "end"); self.p_contact.delete(0, "end")
        self.refresh_patients()

    def refresh_patients(self):
        for r in self.p_table.get_children():
            self.p_table.delete(r)
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT id,name,age,gender,contact FROM patients ORDER BY id DESC")
            for row in cur.fetchall():
                self.p_table.insert("", "end", values=row)

    def selected_patient(self):
        sel = self.p_table.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a patient row first.")
            return None
        vals = self.p_table.item(sel[0], "values")
        return int(vals[0])

    def open_patient_reports(self):
        pid = self.selected_patient()
        if not pid: return
        self.notebook.select(self.tab_reports)
        self.r_pid_var.set(pid)
        self.refresh_reports_table()

    # ---------------------------
    # Diseases Tab
    # ---------------------------
    def build_diseases_tab(self):
        frm = self.tab_disease
        top = ttk.Frame(frm)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Disease Name:").grid(row=0, column=0, sticky="w")
        self.d_name = ttk.Entry(top, width=30); self.d_name.grid(row=0, column=1, padx=4)
        ttk.Button(top, text="Search", command=self.search_disease).grid(row=0, column=2, padx=4)

        ttk.Label(top, text="Add / Update Disease").grid(row=1, column=0, columnspan=3, pady=8)
        ttk.Label(top, text="Name:").grid(row=2, column=0, sticky="w")
        self.d_add_name = ttk.Entry(top, width=30); self.d_add_name.grid(row=2, column=1)
        ttk.Label(top, text="Details:").grid(row=3, column=0, sticky="w")
        self.d_add_details = ttk.Entry(top, width=60); self.d_add_details.grid(row=3, column=1, columnspan=2, pady=4)
        ttk.Label(top, text="Symptoms (csv):").grid(row=4, column=0, sticky="w")
        self.d_add_symp = ttk.Entry(top, width=60); self.d_add_symp.grid(row=4, column=1, columnspan=2, pady=4)
        ttk.Label(top, text="Medicines:").grid(row=5, column=0, sticky="w")
        self.d_add_med = ttk.Entry(top, width=60); self.d_add_med.grid(row=5, column=1, columnspan=2, pady=4)
        ttk.Label(top, text="Hospitals:").grid(row=6, column=0, sticky="w")
        self.d_add_hosp = ttk.Entry(top, width=60); self.d_add_hosp.grid(row=6, column=1, columnspan=2, pady=4)
        self.treat_var = tk.IntVar()
        ttk.Checkbutton(top, text="Treatable (OTC)", variable=self.treat_var).grid(row=7, column=1, sticky="w", pady=6)
        ttk.Button(top, text="Save Disease", command=self.save_disease).grid(row=7, column=2, sticky="e", padx=4)

    def search_disease(self):
        name = self.d_name.get().strip().lower()
        if not name:
            messagebox.showwarning("Input", "Enter disease name")
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT details, symptoms, treatable, medicines, hospitals, notes FROM diseases WHERE lower(name)=?", (name,))
            r = cur.fetchone()
            if not r:
                messagebox.showinfo("Not Found", "Disease not found in DB")
                return
            details, symptoms, treatable, medicines, hospitals, notes = r
            text = f"{name.title()}\n\nDetails: {details}\nSymptoms: {symptoms}\n"
            if treatable:
                text += f"Treatable: Yes\nMedicines: {medicines or '-'}\n"
            else:
                text += "Treatable: No (doctor required)\n"
                text += f"Hospitals: {hospitals or '-'}\n"
            if notes:
                text += f"Notes: {notes}\n"
            messagebox.showinfo("Disease Info", text)

    def save_disease(self):
        name = self.d_add_name.get().strip().lower()
        if not name:
            messagebox.showerror("Error", "Name required")
            return
        details = self.d_add_details.get().strip()
        symptoms = self.d_add_symp.get().strip()
        meds = self.d_add_med.get().strip()
        hosp = self.d_add_hosp.get().strip()
        treat = 1 if self.treat_var.get() else 0
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT id FROM diseases WHERE lower(name)=?", (name,))
            if cur.fetchone():
                cur.execute("UPDATE diseases SET details=?, symptoms=?, treatable=?, medicines=?, hospitals=? WHERE lower(name)=?",
                            (details, symptoms, treat, meds, hosp, name))
            else:
                cur.execute("INSERT INTO diseases(name, details, symptoms, treatable, medicines, hospitals, notes) VALUES(?,?,?,?,?,?,?)",
                            (name, details, symptoms, treat, meds, hosp, ""))
            con.commit()
        messagebox.showinfo("Saved", f"Disease '{name}' saved/updated")

    # ---------------------------
    # Reports Tab
    # ---------------------------
    def build_reports_tab(self):
        frm = self.tab_reports
        top = ttk.Frame(frm)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Selected Patient ID:").grid(row=0, column=0, sticky="w")
        self.r_pid_var = tk.StringVar()
        self.r_pid_label = ttk.Label(top, textvariable=self.r_pid_var)
        self.r_pid_label.grid(row=0, column=1, sticky="w")

        ttk.Button(top, text="Add Report for Selected Patient", command=self.add_report_dialog).grid(row=0, column=2, padx=8)

        # Reports table
        self.reports_table = ttk.Treeview(frm, columns=("id","month","bp","systolic","diastolic","sugar","uric"), show="headings", height=12)
        for c in ("id","month","bp","systolic","diastolic","sugar","uric"):
            self.reports_table.heading(c, text=c.upper())
            self.reports_table.column(c, width=100)
        self.reports_table.pack(fill="both", expand=True, padx=8, pady=8)

        # Buttons: refresh, export, graph, compare
        btns = ttk.Frame(frm)
        btns.pack(fill="x", padx=8, pady=4)
        ttk.Button(btns, text="Refresh", command=self.refresh_reports_table).pack(side="left", padx=4)
        ttk.Button(btns, text="Export CSV", command=self.export_reports_csv).pack(side="left", padx=4)
        ttk.Button(btns, text="Show Graph (SUGAR, URIC)", command=self.show_graph).pack(side="left", padx=4)
        ttk.Button(btns, text="Compare Latest vs Previous", command=self.compare_latest_previous).pack(side="left", padx=4)

    def add_report_dialog(self):
        pid = self.selected_patient()
        if not pid: return
        win = tk.Toplevel(self)
        win.title(f"Add Report - Patient {pid}")
        win.geometry("360x300")

        ttk.Label(win, text="Month (YYYY-MM):").pack(pady=4)
        e_month = ttk.Entry(win); e_month.insert(0, month_str()); e_month.pack(pady=4)

        ttk.Label(win, text="BP (120/80 or 120):").pack(pady=4)
        e_bp = ttk.Entry(win); e_bp.pack(pady=4)

        ttk.Label(win, text="Sugar (mg/dL):").pack(pady=4)
        e_sugar = ttk.Entry(win); e_sugar.pack(pady=4)

        ttk.Label(win, text="Uric Acid (mg/dL):").pack(pady=4)
        e_uric = ttk.Entry(win); e_uric.pack(pady=4)

        def save():
            m = e_month.get().strip() or month_str()
            bp_text = e_bp.get().strip()
            s_sys, s_dia = parse_bp(bp_text)
            sugar = None
            uric = None
            try:
                sugar = float(e_sugar.get().strip()) if e_sugar.get().strip() else None
            except:
                sugar = None
            try:
                uric = float(e_uric.get().strip()) if e_uric.get().strip() else None
            except:
                uric = None
            with get_conn() as con:
                con.execute("""INSERT INTO reports(patient_id, month, bp_systolic, bp_diastolic, sugar, uric_acid, created_at)
                               VALUES(?,?,?,?,?,?,?)""",
                               (pid, m, s_sys, s_dia, sugar, uric, now_str()))
                con.commit()
            messagebox.showinfo("Saved", "Report saved")
            win.destroy()
            self.r_pid_var.set(pid)
            self.refresh_reports_table()
        ttk.Button(win, text="Save Report", command=save).pack(pady=10)

    def refresh_reports_table(self):
        for r in self.reports_table.get_children():
            self.reports_table.delete(r)
        try:
            pid = int(self.r_pid_var.get())
        except:
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT id, month, (CASE WHEN bp_systolic IS NULL THEN '-' WHEN bp_diastolic IS NULL THEN bp_systolic || '' ELSE bp_systolic || '/' || bp_diastolic END) as bp, bp_systolic, bp_diastolic, sugar, uric_acid FROM reports WHERE patient_id=? ORDER BY month DESC", (pid,))
            for row in cur.fetchall():
                self.reports_table.insert("", "end", values=row)

    def export_reports_csv(self):
        pid = self.r_pid_var.get()
        if not pid:
            messagebox.showwarning("Select", "Select a patient first")
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT month, bp_systolic, bp_diastolic, sugar, uric_acid, created_at FROM reports WHERE patient_id=? ORDER BY month ASC", (pid,))
            rows = cur.fetchall()
        if not rows:
            messagebox.showinfo("No Data", "No reports to export")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not fname:
            return
        with open(fname, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Month","BP Systolic","BP Diastolic","Sugar","Uric Acid","Saved At"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Reports exported to {fname}")

    def show_graph(self):
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("No matplotlib", "matplotlib not installed. Install via pip to see graphs.")
            return
        pid = self.r_pid_var.get()
        if not pid:
            messagebox.showwarning("Select", "Select a patient first")
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT month, sugar, uric_acid FROM reports WHERE patient_id=? ORDER BY month ASC", (pid,))
            rows = cur.fetchall()
        if not rows:
            messagebox.showinfo("No Data", "Not enough data to plot")
            return
        months = [r[0] for r in rows]
        sugars = [r[1] if r[1] is not None else 0 for r in rows]
        urics = [r[2] if r[2] is not None else 0 for r in rows]
        plt.figure(figsize=(8,4))
        plt.plot(months, sugars, marker='o', label='Sugar')
        plt.plot(months, urics, marker='o', label='Uric Acid')
        plt.title(f"Patient {pid} - Trends")
        plt.xlabel("Month")
        plt.ylabel("Value")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def compare_latest_previous(self):
        pid = self.r_pid_var.get()
        if not pid:
            messagebox.showwarning("Select", "Select a patient first")
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT month, bp_systolic, bp_diastolic, sugar, uric_acid
                FROM reports WHERE patient_id=? ORDER BY month DESC LIMIT 2
            """, (pid,))
            rows = cur.fetchall()
        if len(rows) < 2:
            messagebox.showinfo("Need Data", "Need at least two months of data to compare")
            return
        (m1, s1, d1, su1, ua1), (m2, s2, d2, su2, ua2) = rows[0], rows[1]
        def cmp(c,p):
            if c is None or p is None: return "Insufficient"
            if c < p: return "Improved"
            if c > p: return "Degraded"
            return "No change"
        out = f"Comparing {m1} vs {m2}\nBP Sys: {s1} vs {s2} → {cmp(s1,s2)}\nBP Dia: {d1} vs {d2} → {cmp(d1,d2)}\nSugar: {su1} vs {su2} → {cmp(su1,su2)}\nUric: {ua1} vs {ua2} → {cmp(ua1,ua2)}"
        # alerts
        if s1 and d1 and (s1 >= 180 or d1 >= 120):
            out += "\n⚠️ Hypertensive crisis suspected. Visit doctor."
        if su1 and su1 >= 300:
            out += "\n⚠️ Very high sugar detected. Consult doctor."
        messagebox.showinfo("Comparison", out)

    # ---------------------------
    # Tools Tab
    # ---------------------------
    def build_tools_tab(self):
        frm = self.tab_tools
        left = ttk.Frame(frm)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # Reminders
        ttk.Label(left, text="Reminders").pack(anchor="w")
        ttk.Button(left, text="Set Reminder", command=self.set_reminder_dialog).pack(fill="x", pady=4)
        ttk.Button(left, text="Check Due Reminders", command=self.check_due_reminders).pack(fill="x", pady=4)

        # SOS
        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(left, text="Emergency SOS").pack(anchor="w")
        ttk.Button(left, text="Show Emergency Contacts", command=self.show_sos).pack(fill="x", pady=4)

        # Hospital list / finder
        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(left, text="Hospitals").pack(anchor="w")
        ttk.Button(left, text="Show Hospitals", command=self.show_hospitals).pack(fill="x", pady=4)

        # Export (also on reports tab)
        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(left, text="Export All Patients to CSV", command=self.export_all_patients).pack(fill="x", pady=4)

    def set_reminder_dialog(self):
        pid = self.selected_patient()
        if not pid: return
        med = simpledialog.askstring("Medicine", "Medicine name:")
        if not med: return
        dt = simpledialog.askstring("Remind At", "Enter datetime (YYYY-MM-DD HH:MM):")
        try:
            datetime.strptime(dt, "%Y-%m-%d %H:%M")
        except:
            messagebox.showerror("Error", "Invalid datetime format")
            return
        with get_conn() as con:
            con.execute("INSERT INTO reminders(user_id, patient_id, medicine, remind_at, created_at) VALUES(?,?,?,?,?)",
                        (None, pid, med, dt+":00", now_str()))
            con.commit()
        messagebox.showinfo("Saved", "Reminder saved")

    def check_due_reminders(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("""SELECT r.id, p.name, r.medicine, r.remind_at FROM reminders r
                           LEFT JOIN patients p ON p.id = r.patient_id
                           WHERE r.done=0 AND r.remind_at <= ? ORDER BY r.remind_at ASC""", (now,))
            rows = cur.fetchall()
        if not rows:
            messagebox.showinfo("No Reminders", "No due reminders")
            return
        out = ""
        ids = []
        for rid, pname, med, when in rows:
            out += f"{when} - {pname or 'Patient'}: Take {med}\n"
            ids.append(rid)
        # mark done
        with get_conn() as con:
            con.executemany("UPDATE reminders SET done=1 WHERE id=?", [(i,) for i in ids])
            con.commit()
        messagebox.showinfo("Due Reminders", out)

    def show_sos(self):
        text = "Emergency Contacts:\n108 - Ambulance\n102 - Police\nLocal Hospital: See hospital list"
        messagebox.showinfo("SOS", text)

    def show_hospitals(self):
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT name, city, contact FROM hospitals ORDER BY name")
            rows = cur.fetchall()
        out = "\n".join([f"{r[0]} ({r[1]}) - {r[2]}" for r in rows])
        messagebox.showinfo("Hospitals", out or "No hospitals in DB")

    def export_all_patients(self):
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not fname: return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT p.id, p.name, p.age, p.gender, p.contact, r.month, r.bp_systolic, r.bp_diastolic, r.sugar, r.uric_acid FROM patients p LEFT JOIN reports r ON p.id = r.patient_id ORDER BY p.id, r.month")
            rows = cur.fetchall()
        with open(fname, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["PatientID","Name","Age","Gender","Contact","Month","BP_Systolic","BP_Diastolic","Sugar","Uric"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"All patient data exported to {fname}")

    # ---------------------------
    # Login / Register / Logout
    # ---------------------------
    def open_login(self):
        win = tk.Toplevel(self)
        win.title("Login / Register")
        win.geometry("360x240")

        ttk.Label(win, text="Username:").pack(pady=6)
        e_user = ttk.Entry(win); e_user.pack(pady=4)
        ttk.Label(win, text="Password:").pack(pady=6)
        e_pass = ttk.Entry(win, show="*"); e_pass.pack(pady=4)

        def login_action():
            u = e_user.get().strip()
            p = e_pass.get().strip()
            if not u or not p:
                messagebox.showerror("Error", "Enter credentials")
                return
            with get_conn() as con:
                cur = con.cursor()
                cur.execute("SELECT id,username,role FROM users WHERE username=? AND password=?", (u,p))
                r = cur.fetchone()
            if r:
                self.current_user = r
                messagebox.showinfo("Login", f"Welcome {r[1]} ({r[2]})")
                win.destroy()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")

        def register_action():
            u = e_user.get().strip()
            p = e_pass.get().strip()
            if not u or not p:
                messagebox.showerror("Error", "Enter credentials")
                return
            with get_conn() as con:
                try:
                    con.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", (u,p,"patient"))
                    con.commit()
                    messagebox.showinfo("Registered", "User registered. Now login.")
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Username already exists")

        ttk.Button(win, text="Login", command=login_action).pack(pady=6)
        ttk.Button(win, text="Register", command=register_action).pack(pady=4)

    def logout(self):
        self.current_user = None
        messagebox.showinfo("Logged out", "You are logged out")

    # ---------------------------
    # Close / cleanup
    # ---------------------------
    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

# ---------------------------
# Run the app
# ---------------------------
def main():
    init_db()
    app = HealthcareApp()
    app.mainloop()

if __name__ == "__main__":
    main()
