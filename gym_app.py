
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime as dt

# ---- CONFIG ----
GYM_NAME = "Your Gym"  # <-- change this to your actual gym name

# ---- DB CONNECTION ----
try:
    import mysql.connector
except Exception as e:
    raise SystemExit("mysql-connector-python is required. Install with: pip install mysql-connector-python")

DB_CONFIG = {
    "host": "localhost",
    "user": "TYPE_YOUR_USERNAME_HERE",
    "password": "TYPE_YOUR_PASSWORD_HERE",
    "database": "gym_db",
    "autocommit": True,
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def run_query(sql, params=None, fetch=False):
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, params or ())
        if fetch:
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return cols, rows
        else:
            conn.commit()
            return None
    except mysql.connector.Error as e:
        messagebox.showerror("SQL Error", f"{e}\n\nQuery: {sql}")
        return None if not fetch else ([], [])
    finally:
        if conn:
            conn.close()

# ----- UTILITIES -----
def tree_clear(tree: ttk.Treeview):
    for r in tree.get_children():
        tree.delete(r)

def populate_tree(tree: ttk.Treeview, cols, rows):
    tree_clear(tree)
    tree["columns"] = cols
    tree.heading("#0", text="", anchor="w")
    tree.column("#0", width=0, stretch=False)
    for c in cols:
        tree.heading(c, text=c, anchor="w")
        tree.column(c, anchor="w", width=120, stretch=True)
    for row in rows:
        values = []
        for v in row:
            if isinstance(v, (dt.date, dt.datetime)):
                values.append(str(v))  # Python 3.10 friendly
            else:
                values.append("" if v is None else str(v))
        tree.insert("", "end", values=values)

def get_selected_row(tree: ttk.Treeview):
    sel = tree.selection()
    if not sel:
        return None
    return tree.item(sel[0])["values"]

def make_combo(parent, values, **grid):
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
    cb.grid(**grid)
    return var, cb

def make_entry(parent, **grid):
    var = tk.StringVar()
    e = ttk.Entry(parent, textvariable=var)
    e.grid(**grid)
    return var, e

def make_date_entry(parent, default_today=True, **grid):
    var = tk.StringVar()
    e = ttk.Entry(parent, textvariable=var)
    if default_today:
        e.insert(0, dt.date.today().isoformat())
    e.grid(**grid)
    return var, e

# ---- LOOKUP HELPERS ----
def fetch_trainer_choices():
    # Return list of tuples (trainer_id, name)
    _c, rows = run_query("SELECT trainer_id, name FROM trainer ORDER BY name", fetch=True)
    return rows

def fetch_plan_choices():
    # Return list of tuples (plan_id, plan_name)
    _c, rows = run_query("SELECT plan_id, plan_name FROM membership_plan ORDER BY plan_name", fetch=True)
    return rows

def find_member_name(member_id):
    c, r = run_query("SELECT name FROM member WHERE member_id=%s", (member_id,), fetch=True)
    return r[0][0] if r else ""

def find_latest_plan_for_member(member_id):
    sql = (
        "SELECT mp.plan_name "
        "FROM enrollment e "
        "JOIN membership_plan mp ON mp.plan_id = e.plan_id "
        "WHERE e.member_id=%s "
        "ORDER BY e.enrollment_date DESC "
        "LIMIT 1"
    )
    c, r = run_query(sql, (member_id,), fetch=True)
    return r[0][0] if r else ""

# ---- BASE FRAME CLASS ----
class BaseModule(ttk.Frame):
    table = ""
    pkey = ""  # name of primary key column; for composite, override delete/update

    def __init__(self, master, title=None):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self._build_common_ui(title or self.table.capitalize())
        self.build_form(self.frm_form)
        self.refresh()

    # Common layout scaffolding
    def _build_common_ui(self, title):
        # form
        self.frm_form = ttk.LabelFrame(self, text=f"{title} Form", padding=10)
        self.frm_form.pack(fill="x")
        # buttons
        self.frm_btns = ttk.Frame(self)
        self.frm_btns.pack(fill="x", pady=(8, 8))
        self.btn_add = ttk.Button(self.frm_btns, text="Add", command=self.add_record)
        self.btn_update = ttk.Button(self.frm_btns, text="Update Selected", command=self.update_record)
        self.btn_delete = ttk.Button(self.frm_btns, text="Delete Selected", command=self.delete_record)
        self.btn_clear = ttk.Button(self.frm_btns, text="Clear Form", command=self.clear_form)
        for i, b in enumerate([self.btn_add, self.btn_update, self.btn_delete, self.btn_clear]):
            b.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        # table
        self.tree = ttk.Treeview(self, show="headings", height=12)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        # search
        self.frm_search = ttk.LabelFrame(self, text="Search", padding=10)
        self.frm_search.pack(fill="x", pady=(8,0))
        self.search_var = tk.StringVar()
        ttk.Entry(self.frm_search, textvariable=self.search_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(self.frm_search, text="Search", command=self.search).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.frm_search, text="Show All", command=self.refresh).grid(row=0, column=2, padx=5, pady=5)

    # --- hooks to override per module ---
    def build_form(self, parent: ttk.LabelFrame):
        pass

    def form_values(self, for_update=False):
        return {}

    def set_form(self, data: dict):
        pass

    # generic insert/update builders
    def build_insert(self, data: dict):
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {self.table} ({fields}) VALUES ({placeholders})"
        return sql, list(data.values())

    def build_update(self, data: dict, pk_value):
        fields = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {self.table} SET {fields} WHERE {self.pkey}=%s"
        params = list(data.values()) + [pk_value]
        return sql, params

    # --- CRUD button handlers ---
    def add_record(self):
        data = self.form_values(for_update=False)
        if data is None:
            return
        sql, params = self.build_insert(data)
        run_query(sql, params)
        self.refresh()
        self.clear_form()

    def update_record(self):
        sel = get_selected_row(self.tree)
        if not sel:
            messagebox.showinfo("Update", "Please select a row in the table.")
            return
        pk_index = self.columns.index(self.pkey)
        pk_val = sel[pk_index]
        data = self.form_values(for_update=True)
        if data is None:
            return
        sql, params = self.build_update(data, pk_val)
        run_query(sql, params)
        self.refresh()

    def delete_record(self):
        sel = get_selected_row(self.tree)
        if not sel:
            messagebox.showinfo("Delete", "Please select a row in the table.")
            return
        pk_index = self.columns.index(self.pkey)
        pk_val = sel[pk_index]
        if messagebox.askyesno("Confirm", f"Delete {self.table} record {self.pkey}={pk_val}?"):
            run_query(f"DELETE FROM {self.table} WHERE {self.pkey}=%s", (pk_val,))
            self.refresh()
            self.clear_form()

    def refresh(self):
        cols, rows = run_query(f"SELECT * FROM {self.table}", fetch=True)
        self.columns = cols
        populate_tree(self.tree, cols, rows)
        # allow modules to update choice lists after refresh
        if hasattr(self, "refresh_choices"):
            try:
                self.refresh_choices()
            except Exception:
                pass

    def search(self):
        q = self.search_var.get().strip()
        if not q:
            self.refresh()
            return
        cols, _rows = run_query(f"SELECT * FROM {self.table} LIMIT 1", fetch=True)
        like_cols = []
        for c in cols:
            if c.endswith("_id"):
                continue
            like_cols.append(f"CAST({c} AS CHAR) LIKE %s")
        if not like_cols:
            self.refresh()
            return
        sql = f"SELECT * FROM {self.table} WHERE " + " OR ".join(like_cols)
        params = ["%" + q + "%"] * len(like_cols)
        cols, rows = run_query(sql, params, fetch=True)
        self.columns = cols
        populate_tree(self.tree, cols, rows)

    def on_select(self, _evt):
        sel = get_selected_row(self.tree)
        if not sel:
            return
        data = dict(zip(self.columns, sel))
        self.set_form(data)

    def clear_form(self):
        for child in self.frm_form.winfo_children():
            if isinstance(child, ttk.Entry):
                child.delete(0, "end")
            if isinstance(child, ttk.Combobox):
                child.set("")

# ---- MODULES ----

class MembersModule(BaseModule):
    table = "member"
    pkey = "member_id"

    def build_form(self, f):
        ttk.Label(f, text="Name").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.name_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="DoB (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.dob_var, _ = make_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Gender").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.gender_var, _ = make_combo(f, ["Male","Female","Other"], row=1, column=1, sticky="w", padx=5, pady=4)
        ttk.Label(f, text="Contact Info").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.contact_var, _ = make_entry(f, row=1, column=3, sticky="ew", padx=5, pady=4)

        ttk.Label(f, text="Trainer").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.trainer_var, self.trainer_cb = make_combo(f, [], row=2, column=1, sticky="ew", padx=5, pady=4)
        self.trainer_map = {}  # display -> id

        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def refresh_choices(self):
        rows = fetch_trainer_choices()
        display = [""] + [f"{tid} - {name}" for tid, name in rows]
        self.trainer_map = {f"{tid} - {name}": tid for tid, name in rows}
        self.trainer_cb["values"] = display

    def form_values(self, for_update=False):
        name = self.name_var.get().strip()
        dob = self.dob_var.get().strip()
        gender = self.gender_var.get().strip()
        contact = self.contact_var.get().strip()
        trainer_disp = self.trainer_var.get().strip()
        if not (name and dob and gender):
            messagebox.showwarning("Validation", "Name, DoB and Gender are required.")
            return None
        trainer_id = self.trainer_map.get(trainer_disp) if trainer_disp else None
        data = {
            "name": name,
            "DoB": dob,
            "gender": gender,
            "contact_info": contact if contact else None,
            "trainer_id": trainer_id,
        }
        return data

    def set_form(self, data):
        self.name_var.set(data.get("name",""))
        self.dob_var.set(data.get("DoB",""))
        self.gender_var.set(data.get("gender",""))
        self.contact_var.set(data.get("contact_info",""))
        # set trainer display
        tid = data.get("trainer_id")
        if tid in (None, "", "None"):
            self.trainer_var.set("")
        else:
            for disp, idv in self.trainer_map.items():
                if idv == tid:
                    self.trainer_var.set(disp); break


    def refresh(self):
        sql = "SELECT m.*, fn_calculate_member_age(m.DoB) AS age FROM member m"
        cols, rows = run_query(sql, fetch=True)
        self.columns = cols
        populate_tree(self.tree, cols, rows)
        if hasattr(self, 'refresh_choices'):
            try:
                self.refresh_choices()
            except:
                pass
class TrainersModule(BaseModule):
    table = "trainer"
    pkey = "trainer_id"

    def build_form(self, f):
        ttk.Label(f, text="Name").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.name_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Contact Info").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.contact_var, _ = make_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)
        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def form_values(self, for_update=False):
        name = self.name_var.get().strip()
        contact = self.contact_var.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required.")
            return None
        return {
            "name": name,
            "contact_info": contact if contact else None,
        }

    def set_form(self, data):
        self.name_var.set(data.get("name",""))
        self.contact_var.set(data.get("contact_info",""))

class PlansModule(BaseModule):
    table = "membership_plan"
    pkey = "plan_id"

    def build_form(self, f):
        ttk.Label(f, text="Plan Name").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.plan_name_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Duration (months)").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.duration_var, _ = make_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Fee").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.fee_var, _ = make_entry(f, row=1, column=1, sticky="ew", padx=5, pady=4)
        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def form_values(self, for_update=False):
        name = self.plan_name_var.get().strip()
        duration = self.duration_var.get().strip()
        fee = self.fee_var.get().strip()
        if not (name and duration and fee):
            messagebox.showwarning("Validation", "All fields are required.")
            return None
        try:
            duration_i = int(duration)
            fee_f = float(fee)
        except ValueError:
            messagebox.showwarning("Validation", "Duration must be int, Fee must be number.")
            return None
        return {"plan_name": name, "duration": duration_i, "fee": fee_f}

    def set_form(self, data):
        self.plan_name_var.set(data.get("plan_name",""))
        self.duration_var.set(str(data.get("duration","")))
        self.fee_var.set(str(data.get("fee","")))

class EnrollmentModule(BaseModule):
    table = "enrollment"
    pkey = "member_id"  # composite in DB

    def _composite_selected(self):
        sel = get_selected_row(self.tree)
        if not sel:
            return None
        d = dict(zip(self.columns, sel))
        return d.get("member_id"), d.get("plan_id")

    def build_form(self, f):
        ttk.Label(f, text="Member ID").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.member_id_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)

        ttk.Label(f, text="Plan").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.plan_var, self.plan_cb = make_combo(f, [], row=0, column=3, sticky="ew", padx=5, pady=4)
        self.plan_map = {}  # display -> id

        ttk.Label(f, text="Enrollment Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.date_var, _ = make_date_entry(f, row=1, column=1, sticky="ew", padx=5, pady=4)
        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def refresh_choices(self):
        rows = fetch_plan_choices()
        display = [""] + [f"{pid} - {pname}" for pid, pname in rows]
        self.plan_map = {f"{pid} - {pname}": pid for pid, pname in rows}
        self.plan_cb["values"] = display

    def build_insert(self, data):
        sql = "INSERT INTO enrollment (member_id, plan_id, enrollment_date) VALUES (%s, %s, %s)"
        return sql, [data["member_id"], data["plan_id"], data["enrollment_date"]]

    def build_update(self, data, _pk_value):
        ids = self._composite_selected()
        if not ids:
            messagebox.showinfo("Update", "Select a row first.")
            return "", []
        mid, pid = ids
        sql = "UPDATE enrollment SET plan_id=%s, enrollment_date=%s WHERE member_id=%s AND plan_id=%s"
        params = [data["plan_id"], data["enrollment_date"], mid, pid]
        return sql, params

    def delete_record(self):
        ids = self._composite_selected()
        if not ids:
            messagebox.showinfo("Delete", "Please select a row.")
            return
        mid, pid = ids
        if messagebox.askyesno("Confirm", f"Delete enrollment member_id={mid} plan_id={pid}?"):
            run_query("DELETE FROM enrollment WHERE member_id=%s AND plan_id=%s", (mid, pid))
            self.refresh()
            self.clear_form()

    def form_values(self, for_update=False):
        try:
            mid = int(self.member_id_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Member ID must be integer.")
            return None
        plan_disp = self.plan_var.get().strip()
        if not plan_disp:
            messagebox.showwarning("Validation", "Please choose a plan.")
            return None
        pid = self.plan_map.get(plan_disp)
        date = self.date_var.get().strip()
        if not date:
            messagebox.showwarning("Validation", "Enrollment date is required.")
            return None
        return {"member_id": mid, "plan_id": pid, "enrollment_date": date}

    def set_form(self, data):
        self.member_id_var.set(str(data.get("member_id","")))
        # set plan combobox display
        pid = data.get("plan_id")
        if pid in (None, "", "None"):
            self.plan_var.set("")
        else:
            for disp, idv in self.plan_map.items():
                if idv == pid:
                    self.plan_var.set(disp); break
        self.date_var.set(str(data.get("enrollment_date","")))


    def add_record(self):
        data = self.form_values(for_update=False)
        if data is None:
            return

        sql, params = self.build_insert(data)
        run_query(sql, params)
        self.refresh()

        # Trigger popup
        mid = data["member_id"]
        c, r = run_query("""
            SELECT SUM(mp.fee)
            FROM enrollment e
            JOIN membership_plan mp ON e.plan_id = mp.plan_id
            WHERE e.member_id=%s
        """, (mid,), fetch=True)

        total = r[0][0] if r and r[0][0] is not None else 0

        win = tk.Toplevel(self)
        win.title("Trigger Executed")
        tk.Label(
            win,
            text=f"ENROLLMENT TRIGGER EXECUTED\n\n"
                f"Member ID: {mid}\n"
                f"Updated Total Fee: ₹ {total}",
            font=("Arial", 12)
        ).pack(padx=20, pady=20)
        win.after(4000, win.destroy)

        # ✅ NEW: Refresh Pending Payments Tab Automatically
        try:
            self.master.master.tab_objects["Pending Payments"].refresh()
        except:
            pass

        self.clear_form()


        
class PaymentsModule(BaseModule):
    table = "payment"
    pkey = "payment_id"

    def build_form(self, f):
        ttk.Label(f, text="Member ID").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.member_id_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Amount").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.amount_var, _ = make_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Payment Date (YYYY-MM-DD HH:MM:SS)").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.date_var, _ = make_entry(f, row=1, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Mode").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.mode_var, _ = make_combo(f, ["Cash", "UPI", "Card"], row=1, column=3, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Status").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.status_var, _ = make_combo(f, ["Pending", "Completed", "Failed"], row=2, column=1, sticky="ew", padx=5, pady=4)
        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

        # extra button for receipt
        self.btn_receipt = ttk.Button(self.frm_btns, text="Generate Receipt (PDF)", command=self.generate_receipt)
        self.btn_receipt.grid(row=0, column=4, padx=5, pady=5, sticky="w")

    def form_values(self, for_update=False):
        try:
            mid = int(self.member_id_var.get().strip())
            amt = float(self.amount_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Member ID must be int and Amount must be number.")
            return None
        date = self.date_var.get().strip() or dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mode = self.mode_var.get().strip()
        status = self.status_var.get().strip()
        if not (mode and status):
            messagebox.showwarning("Validation", "Mode and Status are required.")
            return None
        return {
            "member_id": mid,
            "amount": amt,
            "payment_date": date,
            "payment_mode": mode,
            "status": status,
        }

    def set_form(self, data):
        self.member_id_var.set(str(data.get("member_id","")))
        self.amount_var.set(str(data.get("amount","")))
        self.date_var.set(str(data.get("payment_date","")))
        self.mode_var.set(data.get("payment_mode",""))
        self.status_var.set(data.get("status",""))

    def generate_receipt(self):
        sel = get_selected_row(self.tree)
        if not sel:
            messagebox.showinfo("Receipt", "Select a payment row first.")
            return
        d = dict(zip(self.columns, sel))
        payment_id = d.get("payment_id")
        member_id = d.get("member_id")
        amount = d.get("amount")
        pdate = d.get("payment_date")
        mode = d.get("payment_mode")
        status = d.get("status")

        member_name = find_member_name(member_id)
        plan_name = find_latest_plan_for_member(member_id)

        # Ask where to save
        default_name = f"receipt_{payment_id}.pdf"
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 initialfile=default_name,
                                                 filetypes=[("PDF files","*.pdf"),("All files","*.*")])
        if not file_path:
            return

        # Try to generate PDF with reportlab
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas

            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            y = height - 30*mm

            def line(text, dy=8*mm, size=12, bold=False):
                nonlocal y
                c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
                c.drawString(20*mm, y, text)
                y -= dy

            # Header
            line(GYM_NAME, size=16, bold=True, dy=10*mm)
            line("Payment Receipt", size=14, bold=True, dy=12*mm)

            # Details
            line(f"Receipt No: {payment_id}")
            line(f"Member: {member_name} (ID: {member_id})")
            if plan_name:
                line(f"Plan: {plan_name}")
            line(f"Amount: ₹ {amount}")
            line(f"Payment Date: {pdate}")
            line(f"Mode: {mode}")
            line(f"Status: {status}")
            line("")
            line("Signature: ____________________", dy=15*mm)

            c.showPage()
            c.save()
            messagebox.showinfo("Receipt", f"Receipt saved to:\n{file_path}\n\n(If it didn't open, install reportlab: pip install reportlab)")
        except Exception as e:
            # Fallback to TXT if reportlab not available
            txt_path = file_path.rsplit(".",1)[0] + ".txt"
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"{GYM_NAME}\n")
                    f.write(f"Payment Receipt\n")
                    f.write(f"Receipt No: {payment_id}\n")
                    f.write(f"Member: {member_name} (ID: {member_id})\n")
                    if plan_name:
                        f.write(f"Plan: {plan_name}\n")
                    f.write(f"Amount: ₹ {amount}\n")
                    f.write(f"Payment Date: {pdate}\n")
                    f.write(f"Mode: {mode}\n")
                    f.write(f"Status: {status}\n")
                    f.write("\nSignature: ____________________\n")
                messagebox.showinfo("Receipt", f"PDF generation failed ({e}).\nSaved a TXT receipt instead:\n{txt_path}\nInstall reportlab for PDF: pip install reportlab")
            except Exception as e2:
                messagebox.showerror("Receipt", f"Could not save receipt. Error: {e2}")

class PendingPaymentsModule(ttk.Frame):
    def __init__(self, master, title=None):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self, show="headings", height=14)
        self.tree.pack(fill="both", expand=True)

        self.btn_mark = ttk.Button(self, text="Mark Selected as Paid", command=self.mark_as_paid)
        self.btn_mark.pack(pady=10)

        self.refresh()

    def refresh(self):
        sql = """
        SELECT p.payment_id, p.member_id, m.name AS member_name, p.amount,
               p.payment_date, p.payment_mode, p.status
        FROM payment p
        JOIN member m ON p.member_id = m.member_id
        WHERE LOWER(p.status) = 'pending'
        """
        cols, rows = run_query(sql, fetch=True)
        tree_clear(self.tree)
        self.tree["columns"] = cols
        self.tree.column("#0", width=0, stretch=False)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140)
        for row in rows:
            self.tree.insert("", "end", values=row)

    def mark_as_paid(self):
        sel = get_selected_row(self.tree)
        if not sel:
            messagebox.showinfo("Select Payment", "Please select a payment first.")
            return

        payment_id = sel[0]   # first column is payment_id

        # Payment Mode Selection Popup
        win = tk.Toplevel(self)
        win.title("Complete Payment")
        win.geometry("300x200")
        
        tk.Label(win, text="Select Payment Mode:", font=("Arial", 11)).pack(pady=10)

        mode_var = tk.StringVar(value="Cash")
        modes = ["Cash", "Card", "UPI"]
        for m in modes:
            ttk.Radiobutton(win, text=m, variable=mode_var, value=m).pack(anchor="w", padx=20)

        def confirm():
            mode = mode_var.get()
            run_query("""
                UPDATE payment 
                SET status='Completed', payment_mode=%s, payment_date=NOW()
                WHERE payment_id=%s
            """, (mode, payment_id))
            messagebox.showinfo("Payment Updated", f"Payment marked Completed using {mode}.")
            win.destroy()
            self.refresh()
            # Refresh Payments Tab also, if opened
            try:
                self.master.master.tab_objects["Payments"].refresh()
            except:
                pass

        ttk.Button(win, text="Confirm", command=confirm).pack(pady=15)



class AttendanceModule(BaseModule):
    table = "attendance"
    pkey = "attendance_id"

    def build_form(self, f):
        ttk.Label(f, text="Member ID").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.member_id_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.date_var, _ = make_date_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Status").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.status_var, _ = make_combo(f, ["Present", "Absent"], row=1, column=1, sticky="ew", padx=5, pady=4)
        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def form_values(self, for_update=False):
        try:
            mid = int(self.member_id_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Member ID must be integer.")
            return None
        date = self.date_var.get().strip()
        status = self.status_var.get().strip()
        if not status:
            messagebox.showwarning("Validation", "Status is required.")
            return None
        return {"member_id": mid, "date": date, "status": status}

    def set_form(self, data):
        self.member_id_var.set(str(data.get("member_id","")))
        self.date_var.set(str(data.get("date","")))
        self.status_var.set(data.get("status",""))

class EquipmentModule(BaseModule):
    table = "equipment"
    pkey = "equipment_id"

    def build_form(self, f):
        ttk.Label(f, text="Equipment Name").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.name_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Purchase Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.pdate_var, _ = make_date_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)

        ttk.Label(f, text="Condition").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.cond_var, _ = make_combo(f, ["Good","Okay","Bad"], row=1, column=1, sticky="ew", padx=5, pady=4)

        ttk.Label(f, text="Responsible Trainer").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.trainer_var, self.trainer_cb = make_combo(f, [], row=1, column=3, sticky="ew", padx=5, pady=4)
        self.trainer_map = {}

        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def refresh_choices(self):
        rows = fetch_trainer_choices()
        display = [""] + [f"{tid} - {name}" for tid, name in rows]
        self.trainer_map = {f"{tid} - {name}": tid for tid, name in rows}
        self.trainer_cb["values"] = display

    def form_values(self, for_update=False):
        name = self.name_var.get().strip()
        pdate = self.pdate_var.get().strip()
        cond = self.cond_var.get().strip() or None
        trainer_disp = self.trainer_var.get().strip()
        tid = self.trainer_map.get(trainer_disp) if trainer_disp else None
        if tid is None:
            messagebox.showwarning("Validation", "Please select a Responsible Trainer.")
            return None
        if not (name and pdate):
            messagebox.showwarning("Validation", "Name and Purchase Date are required.")
            return None
        return {"equipment_name": name, "purchase_date": pdate, "condition_of_equipment": cond, "trainer_id": tid}

    def set_form(self, data):
        self.name_var.set(data.get("equipment_name",""))
        self.pdate_var.set(str(data.get("purchase_date","")))
        self.cond_var.set("" if data.get("condition_of_equipment") in (None,"") else data.get("condition_of_equipment"))
        tid = data.get("trainer_id")
        if tid in (None, "", "None"):
            self.trainer_var.set("")
        else:
            for disp, idv in self.trainer_map.items():
                if idv == tid:
                    self.trainer_var.set(disp); break

class SpecializationModule(BaseModule):
    table = "trainer_specialization"
    pkey = "trainer_id"  # composite with specialization_name

    def _composite_selected(self):
        sel = get_selected_row(self.tree)
        if not sel:
            return None
        d = dict(zip(self.columns, sel))
        return d.get("trainer_id"), d.get("specialization_name")

    def build_form(self, f):
        ttk.Label(f, text="Trainer ID").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.tid_var, _ = make_entry(f, row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(f, text="Specialization Name").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.spec_var, _ = make_entry(f, row=0, column=3, sticky="ew", padx=5, pady=4)
        for i in range(4):
            f.grid_columnconfigure(i, weight=1)

    def build_insert(self, data):
        sql = "INSERT INTO trainer_specialization (trainer_id, specialization_name) VALUES (%s, %s)"
        return sql, [data["trainer_id"], data["specialization_name"]]

    def build_update(self, data, _pk_value):
        ids = self._composite_selected()
        if not ids:
            messagebox.showinfo("Update", "Select a row first.")
            return "", []
        tid, old_spec = ids
        sql = "UPDATE trainer_specialization SET specialization_name=%s WHERE trainer_id=%s AND specialization_name=%s"
        params = [data["specialization_name"], tid, old_spec]
        return sql, params

    def delete_record(self):
        ids = self._composite_selected()
        if not ids:
            messagebox.showinfo("Delete", "Please select a row.")
            return
        tid, spec = ids
        if messagebox.askyesno("Confirm", f"Delete specialization '{spec}' for trainer {tid}?"):
            run_query("DELETE FROM trainer_specialization WHERE trainer_id=%s AND specialization_name=%s",
                      (tid, spec))
            self.refresh()
            self.clear_form()

    def form_values(self, for_update=False):
        try:
            tid = int(self.tid_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Trainer ID must be integer.")
            return None
        spec = self.spec_var.get().strip()
        if not spec:
            messagebox.showwarning("Validation", "Specialization is required.")
            return None
        return {"trainer_id": tid, "specialization_name": spec}

    def set_form(self, data):
        self.tid_var.set(str(data.get("trainer_id","")))
        self.spec_var.set(data.get("specialization_name",""))

# ---- APP ----
class GymApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gym Management System - Tkinter + MySQL")
        self.geometry("1200x760")
        try:
            self.style = ttk.Style(self)
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Store references so we can refresh Enrollment tab dynamically
        self.tab_objects = {}

        tabs = [
            ("Members", MembersModule),
            ("Trainers", TrainersModule),
            ("Plans", PlansModule),
            ("Enrollment", EnrollmentModule),
            ("Payments", PaymentsModule),
            ("Pending Payments", PendingPaymentsModule),   # ✅ NEW TAB
            ("Attendance", AttendanceModule),
            ("Equipment", EquipmentModule),
        ("Trainer Specialization", SpecializationModule),
]


        for name, cls in tabs:
            frame = cls(nb, title=name)
            self.tab_objects[name] = frame
            nb.add(frame, text=name)

        # ⬇️ NEW: When switching tabs, auto-refresh Enrollment
        def on_tab_changed(event):
            tab_name = nb.tab(nb.select(), "text")
            if tab_name == "Enrollment":
                try:
                    self.tab_objects["Enrollment"].refresh()
                except:
                    pass

        nb.bind("<<NotebookTabChanged>>", on_tab_changed)

        # bottom status bar
        status = ttk.Label(self, text="Connected to MySQL: {user}@{host}/{db}".format(
            user=DB_CONFIG["user"], host=DB_CONFIG["host"], db=DB_CONFIG["database"]
        ), anchor="w")
        status.pack(fill="x")


def main():
    app = GymApp()
    app.mainloop()

if __name__ == "__main__":
    main()
