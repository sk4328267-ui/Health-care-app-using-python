#!/usr/bin/env python3
# python_project_healthcare_full.py
# Final combined Healthcare App with patient & report deletion

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
DEFAULT_BG = "#e8f5e9"
DARK_BG = "#2e2e2e"
LANG_EN = "EN"
LANG_HI = "HI"

LANG_MAP = {
    "title": {LANG_EN: "Python Project Healthcare", LANG_HI: "पायथन हेल्थकेयर प्रोजेक्ट"},
    "add_patient": {LANG_EN: "Add Patient", LANG_HI: "रोगी जोड़ें"},
    "add_report": {LANG_EN: "Add Report", LANG_HI: "रिपोर्ट जोड़ें"},
    "view_reports": {LANG_EN: "View Reports", LANG_HI: "रिपोर्ट देखें"},
    "delete_patient": {LANG_EN: "Delete Patient", LANG_HI: "रोगी हटाएँ"},
    "delete_report": {LANG_EN: "Delete Report", LANG_HI: "रिपोर्ट हटाएँ"},
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
        # users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'patient'
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
        # reports
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
        # diseases
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
        # hospitals
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
        # admin
        cur.execute("SELECT id FROM users WHERE username='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", ("admin","admin123","admin"))
        # hospitals
        cur.execute("SELECT COUNT(*) FROM hospitals")
        if cur.fetchone()[0]==0:
            hospitals = [("AIIMS Delhi","Delhi","91-11-26588500"),
                         ("Apollo Hospitals","Chennai","+918062972774"),
                         ("Fortis","New Delhi","9205010100"),
                         ("Max Healthcare","New Delhi","+91 9268880303")]
            cur.executemany("INSERT INTO hospitals(name,city,contact) VALUES(?,?,?)",hospitals)
        # diseases
        cur.execute("SELECT COUNT(*) FROM diseases")
        if cur.fetchone()[0]==0:
            defaults = [
                ("fever","Temporary rise in body temperature","fever,chills,headache",1,"Paracetamol, Ibuprofen","","Consult if >3 days"),
                ("diabetes","Chronic high blood sugar","thirst,urination,fatigue",0,"","AIIMS Delhi, Apollo","Long-term care"),
                ("hypertension","High blood pressure","headache,breathlessness",0,"","Cardiology Centers","Monitor regularly"),
                ("common cold","Viral URTI","sneezing,cough,sore throat",1,"Antihistamines, Decongestants","","Usually self-limited"),
                ("malaria","Mosquito-borne parasitic infection","fever,chills",1,"ACT, Chloroquine","Infectious Disease Hospitals","Diagnose with test"),
                ("asthma","Chronic airway inflammation","wheezing,shortness of breath",0,"Inhalers (Salbutamol)","Pulmonology Centers","Doctor plan needed"),
                ("covid-19","Viral infection SARS-CoV-2","fever,cough,loss of smell",0,"Supportive care","COVID Hospitals","Test and isolate"),
                ("dengue","Mosquito-borne viral infection","fever,joint pain,rash",0,"Supportive care (hydration)","Dengue care units","Avoid NSAIDs"),
                ("tuberculosis","Bacterial lung infection","cough,weight loss,fever",0,"DOTS therapy","TB Centers","Long supervised treatment"),
                ("migraine","Neurological headaches","throbbing headache,nausea",1,"Pain relievers, Triptans","","Avoid triggers"),
            ]
            cur.executemany("INSERT INTO diseases(name,details,symptoms,treatable,medicines,hospitals,notes) VALUES(?,?,?,?,?,?,?)",defaults)
        con.commit()

# ---------------------------
# Utils
# ---------------------------
def now_str(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def month_str(): return datetime.now().strftime("%Y-%m")
def parse_bp(bp_text):
    if not bp_text: return None,None
    try:
        if "/" in bp_text:
            a,b = bp_text.split("/",1)
            return int(a.strip()),int(b.strip())
        else:
            return int(bp_text.strip()),None
    except: return None,None

# ---------------------------
# App
# ---------------------------
class HealthcareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x620")
        self.lang = LANG_EN
        self.dark = False
        self.current_user = None
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=DEFAULT_BG)
        toolbar.pack(side="top", fill="x")
        self.title_label = tk.Label(toolbar,text=LANG_MAP["title"][self.lang],font=("Helvetica",16,"bold"),bg=DEFAULT_BG)
        self.title_label.pack(side="left",padx=10,pady=8)
        self.lang_btn = ttk.Button(toolbar,text="हिंदी",width=8,command=self.toggle_language); self.lang_btn.pack(side="right",padx=6)
        self.mode_btn = ttk.Button(toolbar,text=LANG_MAP["mode"][self.lang],width=12,command=self.toggle_mode); self.mode_btn.pack(side="right",padx=6)
        self.logout_btn = ttk.Button(toolbar,text=LANG_MAP["logout"][self.lang],width=10,command=self.logout); self.logout_btn.pack(side="right",padx=6)
        self.login_btn = ttk.Button(toolbar,text=LANG_MAP["login"][self.lang],width=10,command=self.open_login); self.login_btn.pack(side="right",padx=6)

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both",expand=True,padx=12,pady=12)
        self.tab_patient = ttk.Frame(self.notebook); self.notebook.add(self.tab_patient,text="Patients")
        self.tab_disease = ttk.Frame(self.notebook); self.notebook.add(self.tab_disease,text="Diseases")
        self.tab_reports = ttk.Frame(self.notebook); self.notebook.add(self.tab_reports,text="Reports")
        self.tab_tools = ttk.Frame(self.notebook); self.notebook.add(self.tab_tools,text="Tools")

        self.build_patients_tab()
        self.build_diseases_tab()
        self.build_reports_tab()
        self.build_tools_tab()
        self.apply_theme()
        self.update_language()

    # ---------------------------
    # Theme & Language
    # ---------------------------
    def toggle_language(self):
        self.lang = LANG_HI if self.lang==LANG_EN else LANG_EN
        self.update_language()
    def update_language(self):
        self.title_label.config(text=LANG_MAP["title"][self.lang])
        self.mode_btn.config(text=LANG_MAP["mode"][self.lang])
        self.logout_btn.config(text=LANG_MAP["logout"][self.lang])
        self.login_btn.config(text=LANG_MAP["login"][self.lang])
    def toggle_mode(self):
        self.dark = not self.dark; self.apply_theme()
    def apply_theme(self):
        bg = DARK_BG if self.dark else DEFAULT_BG
        fg = "white" if self.dark else "black"
        style = ttk.Style()
        if sys.platform=="win32": style.theme_use('clam')
        style.configure("TButton",padding=6)
        self.configure(bg=bg)
        self.title_label.config(bg=bg,fg=fg)
        for child in self.winfo_children():
            try: child.config(bg=bg)
            except: pass

    # ---------------------------
    # Patients Tab
    # ---------------------------
    def build_patients_tab(self):
        frm = self.tab_patient
        left = ttk.Frame(frm); left.pack(side="left",fill="y",padx=8,pady=8)
        ttk.Label(left,text="Name:").grid(row=0,column=0,sticky="w",pady=4); self.p_name = ttk.Entry(left,width=25); self.p_name.grid(row=0,column=1,pady=4)
        ttk.Label(left,text="Age:").grid(row=1,column=0,sticky="w",pady=4); self.p_age = ttk.Entry(left,width=25); self.p_age.grid(row=1,column=1,pady=4)
        ttk.Label(left,text="Gender:").grid(row=2,column=0,sticky="w",pady=4); self.p_gender = ttk.Entry(left,width=25); self.p_gender.grid(row=2,column=1,pady=4)
        ttk.Label(left,text="Contact:").grid(row=3,column=0,sticky="w",pady=4); self.p_contact = ttk.Entry(left,width=25); self.p_contact.grid(row=3,column=1,pady=4)
        ttk.Button(left,text="Add Patient",command=self.add_patient).grid(row=4,column=0,columnspan=2,pady=4)
        ttk.Button(left,text="Delete Patient",command=self.delete_patient).grid(row=5,column=0,columnspan=2,pady=4)

        # Right
        right = ttk.Frame(frm); right.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        cols = ("id","name","age","gender","contact")
        self.p_table = ttk.Treeview(right,columns=cols,show="headings",height=15)
        for c in cols:
            self.p_table.heading(c,text=c.upper())
            self.p_table.column(c,width=100)
        self.p_table.pack(fill="both",expand=True)
        self.p_table.bind("<Double-1>",lambda e:self.open_patient_reports())
        ttk.Button(right,text="Refresh List",command=self.refresh_patients).pack(pady=6)
        self.refresh_patients()

    def add_patient(self):
        name=self.p_name.get().strip()
        age=self.p_age.get().strip()
        gender=self.p_gender.get().strip()
        contact=self.p_contact.get().strip()
        if not name: messagebox.showerror("Error","Name required"); return
        try: age=int(age)
        except: age=None
        with get_conn() as con:
            con.execute("INSERT INTO patients(name,age,gender,contact,created_at) VALUES(?,?,?,?,?)",(name,age,gender,contact,now_str())); con.commit()
        messagebox.showinfo("Saved",f"Patient {name} added")
        self.p_name.delete(0,"end"); self.p_age.delete(0,"end"); self.p_gender.delete(0,"end"); self.p_contact.delete(0,"end")
        self.refresh_patients()

    def selected_patient(self):
        sel=self.p_table.selection()
        if not sel: messagebox.showwarning("Select","Select a patient first"); return None
        vals=self.p_table.item(sel[0],"values"); return int(vals[0])

    def refresh_patients(self):
        for r in self.p_table.get_children(): self.p_table.delete(r)
        with get_conn() as con:
            cur=con.cursor(); cur.execute("SELECT id,name,age,gender,contact FROM patients ORDER BY id DESC")
            for row in cur.fetchall(): self.p_table.insert("", "end", values=row)

    def delete_patient(self):
        pid=self.selected_patient()
        if not pid: return
        if not messagebox.askyesno("Confirm","Delete patient and all reports?"): return
        with get_conn() as con:
            con.execute("DELETE FROM reports WHERE patient_id=?",(pid,))
            con.execute("DELETE FROM patients WHERE id=?",(pid,))
            con.commit()
        messagebox.showinfo("Deleted","Patient and reports deleted")
        self.refresh_patients()

    def open_patient_reports(self):
        pid=self.selected_patient()
        if not pid: return
        self.notebook.select(self.tab_reports)
        self.r_pid_var.set(pid)
        self.refresh_reports_table()

    # ---------------------------
    # Reports Tab
    # ---------------------------
    def build_reports_tab(self):
        frm=self.tab_reports
        top=ttk.Frame(frm); top.pack(fill="x",padx=8,pady=8)
        ttk.Label(top,text="Selected Patient ID:").grid(row=0,column=0,sticky="w")
        self.r_pid_var=tk.StringVar(); self.r_pid_label=ttk.Label(top,textvariable=self.r_pid_var); self.r_pid_label.grid(row=0,column=1,sticky="w")
        ttk.Button(top,text="Add Report",command=self.add_report_dialog).grid(row=0,column=2,padx=8)
        ttk.Button(top,text="Delete Report",command=self.delete_report).grid(row=0,column=3,padx=8)

        self.reports_table=ttk.Treeview(frm,columns=("id","month","bp","systolic","diastolic","sugar","uric"),show="headings",height=12)
        for c in ("id","month","bp","systolic","diastolic","sugar","uric"):
            self.reports_table.heading(c,text=c.upper())
            self.reports_table.column(c,width=100)
        self.reports_table.pack(fill="both",expand=True,padx=8,pady=8)

    def add_report_dialog(self):
        pid=self.selected_patient()
        if not pid: return
        win=tk.Toplevel(self); win.title(f"Add Report - Patient {pid}"); win.geometry("360x300")
        ttk.Label(win,text="Month (YYYY-MM):").pack(pady=4); e_month=ttk.Entry(win); e_month.insert(0,month_str()); e_month.pack(pady=4)
        ttk.Label(win,text="BP (120/80 or 120):").pack(pady=4); e_bp=ttk.Entry(win); e_bp.pack(pady=4)
        ttk.Label(win,text="Sugar (mg/dL):").pack(pady=4); e_sugar=ttk.Entry(win); e_sugar.pack(pady=4)
        ttk.Label(win,text="Uric Acid (mg/dL):").pack(pady=4); e_uric=ttk.Entry(win); e_uric.pack(pady=4)

        def save():
            m=e_month.get().strip() or month_str()
            bp_text=e_bp.get().strip(); s_sys,s_dia=parse_bp(bp_text)
            sugar=None; uric=None
            try: sugar=float(e_sugar.get().strip()) if e_sugar.get().strip() else None
            except: sugar=None
            try: uric=float(e_uric.get().strip()) if e_uric.get().strip() else None
            except: uric=None
            with get_conn() as con:
                con.execute("INSERT INTO reports(patient_id,month,bp_systolic,bp_diastolic,sugar,uric_acid,created_at) VALUES(?,?,?,?,?,?,?)",
                            (pid,m,s_sys,s_dia,sugar,uric,now_str())); con.commit()
            messagebox.showinfo("Saved","Report saved"); win.destroy(); self.r_pid_var.set(pid); self.refresh_reports_table()
        ttk.Button(win,text="Save Report",command=save).pack(pady=10)

    def refresh_reports_table(self):
        for r in self.reports_table.get_children(): self.reports_table.delete(r)
        try: pid=int(self.r_pid_var.get())
        except: return
        with get_conn() as con:
            cur=con.cursor()
            cur.execute("""SELECT id, month,
                        CASE WHEN bp_systolic IS NULL THEN '' ELSE (bp_systolic || '/' || IFNULL(bp_diastolic,'')) END AS bp,
                        bp_systolic, bp_diastolic, sugar, uric_acid
                        FROM reports WHERE patient_id=? ORDER BY month DESC""",(pid,))
            for row in cur.fetchall(): self.reports_table.insert("", "end", values=row)

    def selected_report(self):
        sel=self.reports_table.selection()
        if not sel: messagebox.showwarning("Select","Select a report first"); return None
        vals=self.reports_table.item(sel[0],"values"); return int(vals[0])

    def delete_report(self):
        rid=self.selected_report()
        if not rid: return
        if not messagebox.askyesno("Confirm","Delete this report?"): return
        with get_conn() as con:
            con.execute("DELETE FROM reports WHERE id=?",(rid,)); con.commit()
        messagebox.showinfo("Deleted","Report deleted")
        self.refresh_reports_table()

    # ---------------------------
    # Diseases Tab
    # ---------------------------
    def build_diseases_tab(self):
        frm=self.tab_disease
        self.d_table=ttk.Treeview(frm,columns=("id","name","details","symptoms","treatable","medicines","hospitals","notes"),show="headings",height=20)
        for c in ("id","name","details","symptoms","treatable","medicines","hospitals","notes"):
            self.d_table.heading(c,text=c.upper()); self.d_table.column(c,width=120)
        self.d_table.pack(fill="both",expand=True,padx=8,pady=8)
        ttk.Button(frm,text="Refresh Diseases",command=self.refresh_diseases).pack(pady=4)
        self.refresh_diseases()

    def refresh_diseases(self):
        for r in self.d_table.get_children(): self.d_table.delete(r)
        with get_conn() as con:
            cur=con.cursor(); cur.execute("SELECT * FROM diseases ORDER BY id"); [self.d_table.insert("", "end", values=row) for row in cur.fetchall()]

    # ---------------------------
    # Tools Tab
    # ---------------------------
    def build_tools_tab(self):
        frm=self.tab_tools
        ttk.Button(frm,text="Export All Patients & Reports (CSV)",command=self.export_all_patients).pack(pady=8)

    def export_all_patients(self):
        file=f"patients_reports_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        with get_conn() as con:
            cur=con.cursor()
            cur.execute("""SELECT p.id, p.name, p.age, p.gender, p.contact, r.month, r.bp_systolic, r.bp_diastolic, r.sugar, r.uric_acid
                           FROM patients p LEFT JOIN reports r ON p.id = r.patient_id ORDER BY p.id, r.month""")
            rows=cur.fetchall()
            with open(file,"w",newline="",encoding="utf-8") as f:
                writer=csv.writer(f)
                writer.writerow(["Patient ID","Name","Age","Gender","Contact","Month","BP Systolic","BP Diastolic","Sugar","Uric Acid"])
                for row in rows: writer.writerow(row)
        messagebox.showinfo("Exported",f"Exported to {file}")

    # ---------------------------
    # Login / Logout
    # ---------------------------
    def open_login(self):
        win=tk.Toplevel(self); win.title("Login"); win.geometry("280x180")
        ttk.Label(win,text="Username:").pack(pady=4); e_user=ttk.Entry(win); e_user.pack(pady=4)
        ttk.Label(win,text="Password:").pack(pady=4); e_pass=ttk.Entry(win,show="*"); e_pass.pack(pady=4)
        def do_login():
            u=e_user.get().strip(); p=e_pass.get().strip()
            with get_conn() as con:
                cur=con.cursor(); cur.execute("SELECT id,role FROM users WHERE username=? AND password=?",(u,p))
                res=cur.fetchone()
                if res: self.current_user=res; messagebox.showinfo("Login","Login successful"); win.destroy()
                else: messagebox.showerror("Error","Invalid credentials")
        ttk.Button(win,text="Login",command=do_login).pack(pady=8)
    def logout(self): self.current_user=None; messagebox.showinfo("Logout","Logged out")
    # ---------------------------
    def on_close(self): self.destroy()

# ---------------------------
# Run App
# ---------------------------
if __name__=="__main__":
    init_db()
    app=HealthcareApp()
    app.mainloop()
