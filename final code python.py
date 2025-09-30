import sqlite3
import sys
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

APP_TITLE = "💊 Python Project Healthcare (Full)"
DB_FILE = "healthcare_full.db"
DEFAULT_BG = "#e8f5e9"
DARK_BG = "#2e2e2e"
LANG_EN = "EN"
LANG_HI = "HI"

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

def get_conn():
    return sqlite3.connect(DB_FILE)

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def month_str():
    return datetime.now().strftime("%Y-%m")

def parse_bp(bp_text):
    if not bp_text:
        return None, None
    try:
        if "/" in bp_text:
            a, b = bp_text.split("/", 1)
            return int(a.strip()), int(b.strip())
        else:
            return int(bp_text.strip()), None
    except:
        return None, None

def init_db():
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'patient'
            );
        """)
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                bp_systolic INTEGER,
                bp_diastolic INTEGER,
                sugar REAL,
                uric_acid REAL,
                created_at TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diseases(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                details TEXT,
                symptoms TEXT,
                treatable INTEGER,
                medicines TEXT,
                hospitals TEXT,
                notes TEXT
            );
        """)
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
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO users(username, password, role) VALUES (?,?,?)", ("admin", "admin123", "admin"))
        cur.execute("SELECT COUNT(*) FROM hospitals")
        if cur.fetchone()[0] == 0:
            hospitals = [
                ("AIIMS Delhi", "Delhi", "011-2658xxxx"),
                ("Apollo Hospitals", "Chennai", "044-2829xxxx"),
                ("Fortis", "New Delhi", "011-4706xxxx"),
                ("Max Healthcare", "New Delhi", "011-4150xxxx"),
            ]
            cur.executemany("INSERT INTO hospitals(name, city, contact) VALUES(?,?,?)", hospitals)
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

def get_band_simple(val, bands, labels):
    if val is None:
        return "N/A"
    for idx, (low, high) in enumerate(bands):
        if low <= val <= high:
            return labels[idx]
    return labels[-1]

class HealthcareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x700")
        self.lang = LANG_EN
        self.dark = False
        self.current_user = None
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        toolbar = tk.Frame(self, bg=DEFAULT_BG)
        toolbar.pack(side="top", fill="x")
        self.title_label = tk.Label(toolbar, text=LANG_MAP["title"][self.lang],
                                    font=("Helvetica", 16, "bold"), bg=DEFAULT_BG)
        self.title_label.pack(side="left", padx=10, pady=8)
        self.lang_btn = ttk.Button(toolbar, text="हिंदी", width=8, command=self.toggle_language)
        self.lang_btn.pack(side="right", padx=6)
        self.mode_btn = ttk.Button(toolbar, text=LANG_MAP["mode"][self.lang], width=12,
                                   command=self.toggle_mode)
        self.mode_btn.pack(side="right", padx=6)
        self.logout_btn = ttk.Button(toolbar, text=LANG_MAP["logout"][self.lang], width=10,
                                     command=self.logout)
        self.logout_btn.pack(side="right", padx=6)
        self.login_btn = ttk.Button(toolbar, text=LANG_MAP["login"][self.lang], width=10,
                                    command=self.open_login)
        self.login_btn.pack(side="right", padx=6)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.tab_patient = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_patient, text="Patients")
        self.tab_disease = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_disease, text="Diseases")
        self.tab_reports = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reports, text="Reports")
        self.tab_tools = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tools, text="Tools")
        self.build_patients_tab()
        self.build_diseases_tab()
        self.build_reports_tab()
        self.build_tools_tab()
        self.apply_theme()
        self.update_language()

    # ------- Patients Tab -------
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
        ttk.Button(left, text="Delete Patient", command=self.delete_patient).grid(row=5, column=0, columnspan=2, pady=4)
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
        self.p_name.delete(0, "end"); self.p_age.delete(0, "end")
        self.p_gender.delete(0, "end"); self.p_contact.delete(0, "end")
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
    def delete_patient(self):
        pid = self.selected_patient()
        if not pid:
            return
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this patient and all their reports?")
        if not confirm:
            return
        with get_conn() as con:
            con.execute("DELETE FROM reports WHERE patient_id=?", (pid,))
            con.execute("DELETE FROM patients WHERE id=?", (pid,))
            con.commit()
        messagebox.showinfo("Deleted", "Patient and their reports deleted.")
        self.refresh_patients()
    def open_patient_reports(self):
        pid = self.selected_patient()
        if not pid: return
        self.notebook.select(self.tab_reports)
        self.r_pid_var.set(pid)
        self.refresh_reports_table()

    # ------- Reports Tab ------
    def build_reports_tab(self):
        frm = self.tab_reports
        top = ttk.Frame(frm)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Patient ID:").pack(side="left")
        self.r_pid_var = tk.IntVar()
        self.r_pid_entry = ttk.Entry(top, width=6, textvariable=self.r_pid_var)
        self.r_pid_entry.pack(side="left")
        ttk.Button(top, text="Load Reports", command=self.refresh_reports_table).pack(side="left", padx=6)
        main = ttk.Frame(frm)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        report_cols = ("id", "month", "bp_systolic", "bp_diastolic", "sugar", "uric_acid", "created_at")
        self.r_table = ttk.Treeview(main, columns=report_cols, show="headings", height=12)
        for c in report_cols:
            self.r_table.heading(c, text=c.upper())
            self.r_table.column(c, width=90)
        self.r_table.pack(side="left", fill="both", expand=True)
        btn_frame = ttk.Frame(main)
        btn_frame.pack(side="left", fill="y", padx=10)
        ttk.Button(btn_frame, text="Add Report", command=self.add_report_dialog).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Delete Report", command=self.delete_report).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Compare Reports", command=self.compare_reports).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Export CSV", command=self.export_reports_csv).pack(fill="x", pady=4)
        if MATPLOTLIB_AVAILABLE:
            ttk.Button(btn_frame, text="Show BP Chart", command=self.bp_chart_plot).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_reports_table).pack(fill="x", pady=4)
    def refresh_reports_table(self):
        pid = self.r_pid_var.get()
        for r in self.r_table.get_children():
            self.r_table.delete(r)
        if not pid:
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT id, month, bp_systolic, bp_diastolic, sugar, uric_acid, created_at FROM reports WHERE patient_id=? ORDER BY id DESC", (pid,))
            for row in cur.fetchall():
                self.r_table.insert("", "end", values=row)
    def selected_report(self):
        sel = self.r_table.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a report row first.")
            return None
        vals = self.r_table.item(sel[0], "values")
        return int(vals[0])
    def delete_report(self):
        rid = self.selected_report()
        if not rid:
            return
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this report?")
        if not confirm:
            return
        with get_conn() as con:
            con.execute("DELETE FROM reports WHERE id=?", (rid,))
            con.commit()
        messagebox.showinfo("Deleted", "Report deleted.")
        self.refresh_reports_table()
    def add_report_dialog(self):
        pid = self.r_pid_var.get()
        if not pid:
            messagebox.showwarning("Select", "No patient ID selected. Please enter patient ID and click Load Reports before adding.")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Add Patient Report")
        dialog.geometry("320x330")
        ttk.Label(dialog, text="Month (YYYY-MM):").pack(pady=5)
        month_entry = ttk.Entry(dialog, width=12)
        month_entry.pack()
        month_entry.insert(0, month_str())
        ttk.Label(dialog, text="BP (Systolic/Diastolic):").pack(pady=5)
        bp_entry = ttk.Entry(dialog, width=12)
        bp_entry.pack()
        ttk.Label(dialog, text="Sugar Level:").pack(pady=5)
        sugar_entry = ttk.Entry(dialog, width=12)
        sugar_entry.pack()
        ttk.Label(dialog, text="Uric Acid:").pack(pady=5)
        uric_entry = ttk.Entry(dialog, width=12)
        uric_entry.pack()
        def submit():
            month = month_entry.get().strip()
            bp    = bp_entry.get().strip()
            sugar = sugar_entry.get().strip()
            uric  = uric_entry.get().strip()
            try:
                bp_sys, bp_dia = parse_bp(bp)
                sugar_val = float(sugar) if sugar else None
                uric_val = float(uric) if uric else None
            except:
                messagebox.showerror("Error", "Enter BP, Sugar, Uric Acid as numbers!")
                return
            if not month or bp_sys is None:
                messagebox.showerror("Error", "Month and BP required.")
                return
            with get_conn() as con:
                con.execute(
                    "INSERT INTO reports(patient_id, month, bp_systolic, bp_diastolic, sugar, uric_acid, created_at) VALUES (?,?,?,?,?,?,?)",
                    (pid, month, bp_sys, bp_dia, sugar_val, uric_val, now_str())
                )
                con.commit()
            messagebox.showinfo("Saved", "Report added.")
            dialog.destroy()
            self.refresh_reports_table()
        ttk.Button(dialog, text="Submit", command=submit).pack(pady=12)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=2)
    def compare_reports(self):
        pid = self.r_pid_var.get()
        if not pid:
            messagebox.showwarning("Compare", "No patient selected.")
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT month, bp_systolic, bp_diastolic, sugar, uric_acid FROM reports WHERE patient_id=? ORDER BY month DESC", (pid,))
            rows = cur.fetchall()
        if len(rows) < 2:
            messagebox.showinfo("Compare", "Need at least 2 reports for comparison.")
            return
        latest = rows[0]
        prev = rows[1]
        # Band definitions
        bp_s_bands = [(-1000,89),(90,120),(121,139),(140,180),(181,1000)]
        bp_s_labels = ["Low","Good","Borderline","High","Extreme"]
        bp_d_bands = [(-1000,59),(60,80),(81,90),(91,120),(121,1000)]
        bp_d_labels = ["Low","Good","Borderline","High","Extreme"]
        sugar_bands = [(-1000,69),(70,100),(101,125),(126,200),(201,10000)]
        sugar_labels = ["Low","Good","Borderline","High","Extreme"]
        uric_bands = [(-1000,2),(3,7),(8,8),(9,12),(13,1000)]
        uric_labels = ["Low","Good","Borderline","High","Extreme"]
        final_report = f"Latest ({latest[0]}) vs Previous ({prev[0]})\n\n"
        metrics = [
            ("BP Systolic", prev[1], latest[1], bp_s_bands, bp_s_labels),
            ("BP Diastolic", prev[2], latest[2], bp_d_bands, bp_d_labels),
            ("Sugar", prev[3], latest[3], sugar_bands, sugar_labels),
            ("Uric Acid", prev[4], latest[4], uric_bands, uric_labels),
        ]
        for name, prev_v, latest_v, bands, labels in metrics:
            prev_band = get_band_simple(prev_v, bands, labels)
            latest_band = get_band_simple(latest_v, bands, labels)
            if prev_band == "N/A" or latest_band == "N/A":
                verdict = "N/A"
            elif latest_band == prev_band:
                verdict = "No Change"
            elif latest_band == "Good":
                verdict = "Improved"
            elif prev_band == "Good" and latest_band != "Good":
                verdict = "Degraded"
            elif labels.index(latest_band) > labels.index(prev_band):
                verdict = "Degraded"
            elif labels.index(latest_band) < labels.index(prev_band):
                verdict = "Improved"
            else:
                verdict = "No Change"
            final_report += f"{name:12}: {latest_v} ({latest_band}) vs {prev_v} ({prev_band})  → {verdict}\n"
        final_report += (
            "\nBP Systolic: 90-120 Good, 121-139 Borderline, 140-180 High\n"
            "BP Diastolic: 60-80 Good, 81-90 Borderline, 91-120 High\n"
            "Sugar(fasting): 70-100 Good, 101-125 Borderline, 126-200 High\n"
            "Uric Acid: 3-7 Good, 8 Borderline, 9-12 High"
        )
        messagebox.showinfo("Report Feedback & Comparison", final_report)
    def export_reports_csv(self):
        pid = self.r_pid_var.get()
        if not pid:
            messagebox.showwarning("Export", "No patient selected.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export Reports as CSV"
        )
        if not filename:
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM reports WHERE patient_id=? ORDER BY month DESC", (pid,))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow(row)
        messagebox.showinfo("CSV Export", f"Exported {len(rows)} reports to {filename}")
    def bp_chart_plot(self):
        pid = self.r_pid_var.get()
        if not pid or not MATPLOTLIB_AVAILABLE:
            messagebox.showwarning("Chart", "Matplotlib not available or no patient selected.")
            return
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT month, bp_systolic, bp_diastolic FROM reports WHERE patient_id=? ORDER BY month ASC", (pid,))
            data = cur.fetchall()
        if not data:
            messagebox.showwarning("Chart", "No data for chart.")
            return
        months = [r[0] for r in data]
        systolic = [r[1] for r in data]
        diastolic = [r[2] for r in data]
        plt.figure(figsize=(8,5))
        plt.plot(months, systolic, label="Systolic")
        plt.plot(months, diastolic, label="Diastolic")
        plt.xlabel("Month")
        plt.ylabel("Value")
        plt.title("Blood Pressure Trend")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    # ---- Diseases Tab ----
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

    # --- Tools tab & Symptom Checker ---
    def build_tools_tab(self):
        frm = self.tab_tools
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        notebook = ttk.Notebook(frm)
        notebook.grid(row=0, column=0, sticky="nsew")
        # Reminders
        tab_remind = ttk.Frame(notebook)
        notebook.add(tab_remind, text=LANG_MAP["reminders"][self.lang])
        ttk.Label(tab_remind, text="Add Medicine Reminder").pack(pady=3)
        self.remind_medicine = ttk.Entry(tab_remind, width=30)
        self.remind_medicine.pack()
        self.remind_time = ttk.Entry(tab_remind, width=30)
        self.remind_time.pack()
        ttk.Label(tab_remind, text="Remind At (YYYY-MM-DD HH:MM)").pack()
        ttk.Button(tab_remind, text="Add Reminder", command=self.add_reminder).pack(pady=3)
        ttk.Button(tab_remind, text="Show My Reminders", command=self.show_reminders).pack(pady=3)
        # Emergency
        tab_sos = ttk.Frame(notebook)
        notebook.add(tab_sos, text=LANG_MAP["sos"][self.lang])
        ttk.Label(tab_sos, text="Emergency Numbers:").pack(pady=2)
        ttk.Label(tab_sos, text="Police: 100\nAmbulance: 102\nFire: 101").pack(pady=2)
        ttk.Button(tab_sos, text="Show Nearby Hospitals", command=self.show_hospitals).pack(pady=3)
        # Hospitals
        tab_hosp = ttk.Frame(notebook)
        notebook.add(tab_hosp, text="Hospitals")
        ttk.Label(tab_hosp, text="List of Hospitals:").pack(pady=3)
        self.hospitals_text = tk.Text(tab_hosp, height=10, width=52)
        self.hospitals_text.pack()
        ttk.Button(tab_hosp, text="Refresh Hospital List", command=self.show_hospitals).pack(pady=3)
        # Symptom Checker
        tab_symp = ttk.Frame(notebook)
        notebook.add(tab_symp, text=LANG_MAP["symptom_checker"][self.lang])
        ttk.Label(tab_symp, text="Enter symptoms separated by comma, e.g. fever,cough,headache").pack(pady=6)
        self.symptom_entry = ttk.Entry(tab_symp, width=41)
        self.symptom_entry.pack(pady=3)
        ttk.Button(tab_symp, text="Check Possible Diseases", command=self.symptom_checker).pack(pady=3)
    def add_reminder(self):
        med = self.remind_medicine.get().strip()
        remind_at = self.remind_time.get().strip()
        if not med or not remind_at:
            messagebox.showerror("Error", "Medicine name and time required.")
            return
        with get_conn() as con:
            pid = None
            uid = 1
            con.execute("INSERT INTO reminders(user_id, patient_id, medicine, remind_at, created_at) VALUES (?,?,?,?,?)",
                        (uid, pid, med, remind_at, now_str()))
            con.commit()
        messagebox.showinfo("Reminder", "Medicine reminder saved.")
    def show_reminders(self):
        with get_conn() as con:
            cur = con.cursor()
            uid = 1
            cur.execute("SELECT medicine, remind_at, done FROM reminders WHERE user_id=? ORDER BY remind_at ASC", (uid,))
            rows = cur.fetchall()
        if not rows:
            messagebox.showinfo("Reminders", "No reminders.")
            return
        msg = ""
        for r in rows:
            msg += f"{r[0]} at {r[1]} - {'Done' if r[2] else 'Pending'}\n"
        messagebox.showinfo("Reminders", msg)
    def show_hospitals(self):
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT name, city, contact FROM hospitals")
            rows = cur.fetchall()
        self.hospitals_text.delete('1.0', tk.END)
        for r in rows:
            self.hospitals_text.insert(tk.END, f"{r[0]} - {r[1]} - {r[2]}\n")
    def symptom_checker(self):
        user_input = self.symptom_entry.get().strip().lower()
        if not user_input:
            messagebox.showwarning("No input", "Please enter at least one symptom.")
            return
        symptoms_provided = set([s.strip() for s in user_input.split(",") if s.strip()])
        if not symptoms_provided:
            messagebox.showwarning("No input", "Please enter valid symptoms.")
            return
        results = []
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT name, details, symptoms FROM diseases")
            for name, details, db_symptoms in cur.fetchall():
                if not db_symptoms:
                    continue
                db_symptom_set = set([s.strip().lower() for s in db_symptoms.split(",")])
                matched = symptoms_provided & db_symptom_set
                if matched:
                    results.append( (name, details, len(matched), matched, db_symptom_set) )
        if not results:
            messagebox.showinfo("Result", "No matching diseases found in database.")
            return
        results.sort(key=lambda x: (-x[2], x[0]))  # most matches first
        msg = ""
        for name, details, cnt, matched, db_symptoms in results:
            msg += f"{name.title()}: {details}\n"
            msg += f"  Matched: {', '.join(matched)} / All: {', '.join(db_symptoms)}\n"
        messagebox.showinfo("Likely Diseases", msg)

    # --- General UI helpers ---
    def toggle_language(self):
        self.lang = LANG_HI if self.lang == LANG_EN else LANG_EN
        self.update_language()
    def update_language(self):
        self.title_label.config(text=LANG_MAP["title"][self.lang])
        self.mode_btn.config(text=LANG_MAP["mode"][self.lang])
        self.logout_btn.config(text=LANG_MAP["logout"][self.lang])
        self.login_btn.config(text=LANG_MAP["login"][self.lang])
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
        self.configure(bg=bg)
        self.title_label.config(bg=bg, fg=fg)
        for child in self.winfo_children():
            try:
                child.config(bg=bg)
            except:
                pass
    def open_login(self):
        messagebox.showinfo("Info", "Implement Login dialog here (optional).")
    def logout(self):
        messagebox.showinfo("Info", "Implement Logout logic here (optional).")
    def on_close(self):
        self.destroy()

def main():
    init_db()
    app = HealthcareApp()
    app.mainloop()

if __name__ == "__main__":
    main()
