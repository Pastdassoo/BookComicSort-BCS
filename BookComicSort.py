import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import sqlite3
import os
import shutil
from PIL import Image
# Imports  ^
#          |
# DESIGN
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

# PFADE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sammlung.db")
IMAGE_DIR = os.path.join(BASE_DIR, "bilder")
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# FENSTER MIT BILD
class DetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title(f"Details: {data['name']}")
        self.geometry("500x780")
        self.attributes("-topmost", True)
        
        ctk.CTkLabel(self, text="Informationen", font=("Arial", 22, "bold")).pack(pady=15)
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields_map = [
            ("Datenbank-ID", "id"), ("Name", "name"), ("Nummer", "nummer"), 
            ("Marke/Serie", "marke"), ("Genre", "genre"), ("Verlag", "verlag"), 
            ("Jahr", "jahr"), ("Zustand", "zustand"), ("Erstausgabe", "erstausgabe"), 
            ("Lagerort", "ort"), ("Anzahl", "anzahl"), ("Preis (€)", "preis")
        ]
        
        info_frame = ctk.CTkFrame(container)
        info_frame.pack(side="top", fill="x", padx=10, pady=10)
        
        for i, (label_text, db_field) in enumerate(fields_map):
            ctk.CTkLabel(info_frame, text=f"{label_text}:", font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            val = data[db_field]  # <-- FIX: Direkt auf das korrekte Feld zugreifen
            if db_field == "preis" and val is not None:
                try: val = f"{float(val):.2f} €"
                except ValueError: pass
            ctk.CTkLabel(info_frame, text=str(val if val is not None else "")).grid(row=i, column=1, sticky="w", padx=5, pady=2)
            
        img_path = data["bildpfad"]
        if img_path and isinstance(img_path, str) and os.path.exists(os.path.join(BASE_DIR, img_path)):
            try:
                full_path = os.path.join(BASE_DIR, img_path)
                my_image = ctk.CTkImage(light_image=Image.open(full_path), dark_image=Image.open(full_path), size=(280, 280))
                img_label = ctk.CTkLabel(container, image=my_image, text="")
                img_label.pack(pady=15)
            except Exception:
                ctk.CTkLabel(container, text="[Bild konnte nicht geladen werden]").pack()
        else:
            ctk.CTkLabel(container, text="[Kein Bild vorhanden]", font=("Arial", 10, "italic")).pack(pady=20)
            
        ctk.CTkButton(self, text="Schließen", command=self.destroy).pack(pady=15)

# FENSTER EINSTELLEN
class EditWindow(ctk.CTkToplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.item_id = data["id"]
        self.current_img_path = data["bildpfad"] if data["bildpfad"] else ""
        
        self.title(f"Eintrag bearbeiten: {data['name']}")
        self.geometry("500x750")
        self.attributes("-topmost", True)
        
        ctk.CTkLabel(self, text="Eintrag bearbeiten", font=("Arial", 20, "bold")).pack(pady=10)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.field_config = [
            ("Name", "name"), ("Nummer", "nummer"), ("Marke / Serie", "marke"), 
            ("Genre", "genre"), ("Verlag", "verlag"), ("Jahr", "jahr"), 
            ("Zustand", "zustand"), ("Erstausgabe (Ja/Nein)", "erstausgabe"), 
            ("Lagerort", "ort"), ("Anzahl", "anzahl"), ("Preis (€)", "preis")
        ]
        self.fields = {}
        
        for label_text, db_field in self.field_config:
            ctk.CTkLabel(self.scroll_frame, text=label_text, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            entry = ctk.CTkEntry(self.scroll_frame, placeholder_text=label_text)
            val = data[db_field]  # <-- FIX: Direkt auf das korrekte Feld zugreifen
            entry.insert(0, str(val) if val is not None else "")
            entry.pack(fill="x", padx=10, pady=2)
            self.fields[db_field] = entry
            
        self.btn_img = ctk.CTkButton(self.scroll_frame, text="Bild ändern" if self.current_img_path else "Bild auswählen", command=self.select_image)
        self.btn_img.pack(pady=10)
        if self.current_img_path:
            self.btn_img.configure(text="Bild bereit")
            
        self.check_wunsch_var = tk.IntVar(value=int(data["wunschliste"] if data["wunschliste"] is not None else 0))
        ctk.CTkCheckBox(self.scroll_frame, text="Nur auf Wunschliste", variable=self.check_wunsch_var).pack(pady=5)
        
        ctk.CTkButton(self, text="Speichern", fg_color="#2e7d32", hover_color="#1b5e20", command=self.save_changes, font=("Arial", 14, "bold")).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self, text="Abbrechen", command=self.destroy).pack(pady=5)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Bilder", "*.jpg *.png *.jpeg *.heic")]) # Bild Dateien Arten / Types of Picture Files
        if path:
            filename = os.path.basename(path)
            dest = os.path.join(IMAGE_DIR, filename)
            if not os.path.exists(dest):
                shutil.copy(path, dest)
            self.current_img_path = os.path.relpath(dest, BASE_DIR)
            self.btn_img.configure(text="Bild bereit")

    def save_changes(self):
        try:
            name = self.fields["name"].get()
            if not name:
                messagebox.showwarning("Fehler", "Bitte gib einen Namen ein!")
                return
                
            anzahl_raw = self.fields["anzahl"].get() or "1"
            preis_raw = self.fields["preis"].get().replace(",", ".") or "0"
            
            try: anzahl = int(anzahl_raw)
            except ValueError: raise ValueError(f"Ungültige Anzahl '{anzahl_raw}'.")
                
            try: preis = float(preis_raw)
            except ValueError: raise ValueError(f"Ungültiger Preis '{preis_raw}'.")

            data = (
                name, self.fields["nummer"].get(), self.fields["marke"].get(),
                self.fields["genre"].get(), self.fields["verlag"].get(), self.fields["jahr"].get(), 
                self.fields["zustand"].get(), self.fields["erstausgabe"].get(), 
                self.fields["ort"].get(), anzahl, preis, self.current_img_path, 
                self.check_wunsch_var.get(), self.item_id
            )
            
            self.parent.db.cursor.execute("""
                UPDATE sammlung SET 
                name=?, nummer=?, marke=?, genre=?, verlag=?, jahr=?, 
                zustand=?, erstausgabe=?, ort=?, anzahl=?, preis=?, 
                bildpfad=?, wunschliste=? WHERE id=?
            """, data)
            self.parent.db.conn.commit()
            messagebox.showinfo("Erfolg", "Änderungen erfolgreich gespeichert!")
            self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler beim Bearbeiten", f"Der Eintrag konnte nicht geändert werden.\n\nGrund:\n{str(e)}")

# DATENBANK
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_table()
        self.update_table_structure()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sammlung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, nummer TEXT, marke TEXT, genre TEXT, verlag TEXT,
            jahr TEXT, zustand TEXT, erstausgabe TEXT,
            ort TEXT, anzahl INTEGER, preis REAL,
            bildpfad TEXT, wunschliste INTEGER
        )
        """)
        self.conn.commit()

    def update_table_structure(self):
        temp_conn = sqlite3.connect(DB_PATH)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("PRAGMA table_info(sammlung)")
        
        columns = [row[1].lower() for row in temp_cursor.fetchall()]
        temp_conn.close()

        if "genre" not in columns:
            try:
                self.cursor.execute("ALTER TABLE sammlung ADD COLUMN genre TEXT")
                self.conn.commit()
            except Exception: pass

    def get_filtered(self, wunschliste, search_term, search_by):
        mapping = {"Name": "name", "ID": "id", "Verlag": "verlag", "Genre": "genre"}
        col = mapping.get(search_by, "name")
        
        if col == "id":
            query = f"SELECT * FROM sammlung WHERE wunschliste = ? AND {col} LIKE ?"
            self.cursor.execute(query, (wunschliste, f"{search_term}%"))
        else:
            query = f"SELECT * FROM sammlung WHERE wunschliste = ? AND LOWER({col}) LIKE LOWER(?)"
            self.cursor.execute(query, (wunschliste, f"{search_term}%"))
        return self.cursor.fetchall()

# APP
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.title("Sammlung")
        self.geometry("1250x850")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkScrollableFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.setup_sidebar()
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.tab_sammlung = self.tabview.add("Sammlung")
        self.tab_wunsch = self.tabview.add("Wunschliste")
        self.setup_table(self.tab_sammlung, 0)
        self.setup_table(self.tab_wunsch, 1)
        
        self.style_table()
        self.refresh_data()

    def style_table(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2a2a", foreground="white", rowheight=28, fieldbackground="#2a2a2a", borderwidth=0, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=("Arial", 11, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", "#1f538d")])

    def setup_sidebar(self):
        ctk.CTkLabel(self.sidebar, text="Neu hinzufügen", font=("Arial", 20, "bold")).pack(pady=10)
        self.fields = {}
        
        self.field_inputs = [
            ("Name", "name"), ("Nummer", "nummer"), ("Marke / Serie", "marke"), 
            ("Genre", "genre"), ("Verlag", "verlag"), ("Jahr", "jahr"), 
            ("Zustand", "zustand"), ("Erstausgabe (Ja/Nein)", "erstausgabe"), 
            ("Lagerort", "ort"), ("Anzahl", "anzahl"), ("Preis (€)", "preis")
        ]
        
        for label_text, db_field in self.field_inputs:
            entry = ctk.CTkEntry(self.sidebar, placeholder_text=label_text)
            entry.pack(fill="x", padx=10, pady=3)
            self.fields[db_field] = entry
            
        self.current_img_path = ""
        self.btn_img = ctk.CTkButton(self.sidebar, text="Bild auswählen", command=self.select_image)
        self.btn_img.pack(pady=10)
        
        self.check_wunsch_var = tk.IntVar()
        ctk.CTkCheckBox(self.sidebar, text="Nur auf Wunschliste", variable=self.check_wunsch_var).pack(pady=5)
        
        ctk.CTkButton(self.sidebar, text="Speichern", fg_color="#2e7d32", hover_color="#1b5e20", command=self.save_entry, font=("Arial", 14, "bold")).pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.sidebar, text="Suchen nach:", font=("Arial", 14)).pack(pady=(20, 0))
        self.search_type = ctk.CTkOptionMenu(self.sidebar, values=["Name", "ID", "Verlag", "Genre"])
        self.search_type.pack(fill="x", padx=10, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_data())
        ctk.CTkEntry(self.sidebar, textvariable=self.search_var, placeholder_text="Tippen zum Suchen...").pack(fill="x", padx=10)
        
        ctk.CTkButton(self.sidebar, text="Liste drucken", command=self.export_html).pack(fill="x", padx=10, pady=15)
        
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color="#1f1f1f")
        self.stats_frame.pack(fill="x", padx=10, pady=20)
        self.lbl_total_items = ctk.CTkLabel(self.stats_frame, text="Einträge gesamt: 0", font=("Arial", 12, "bold"))
        self.lbl_total_items.pack(pady=5)
        self.lbl_total_value = ctk.CTkLabel(self.stats_frame, text="Gesamtwert: 0.00 €", font=("Arial", 12, "bold"))
        self.lbl_total_value.pack(pady=5)

    def setup_table(self, parent, tab_id):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("ID", "Name", "Nummer/Number", "Genre", "Verlag/publisher", "Preis/Cost's")
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        widths = {"ID": 60, "Name": 250, "Nummer": 80, "Genre": 150, "Verlag": 150, "Preis": 100}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 100), anchor="w" if col != "Preis" and col != "ID" else "center")
            
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        tree.bind("<Double-1>", lambda e: self.open_details(tree))
        tree.bind("<Button-3>", lambda e: self.show_context_menu(e, tree))
        
        if tab_id == 0: self.tree_sammlung = tree
        else: self.tree_wunsch = tree

    def open_details(self, tree):
        selected = tree.selection()
        if selected:
            item_id = tree.item(selected)['values'][0]
            self.db.cursor.execute("SELECT * FROM sammlung WHERE id = ?", (item_id,))
            data = self.db.cursor.fetchone()
            if data:
                DetailWindow(self, data)

    def save_entry(self):
        try:
            name = self.fields["name"].get()
            if not name:
                messagebox.showwarning("Fehler", "Bitte gib einen Namen ein!")
                return
                
            anzahl_raw = self.fields["anzahl"].get() or "1"
            preis_raw = self.fields["preis"].get().replace(",", ".") or "0"
            
            try: anzahl = int(anzahl_raw)
            except ValueError: raise ValueError(f"Ungültige Anzahl '{anzahl_raw}'.")
                
            try: preis = float(preis_raw)
            except ValueError: raise ValueError(f"Ungültiger Preis '{preis_raw}'.")

            data = (
                name, self.fields["nummer"].get(), self.fields["marke"].get(),
                self.fields["genre"].get(), self.fields["verlag"].get(), self.fields["jahr"].get(), 
                self.fields["zustand"].get(), self.fields["erstausgabe"].get(), 
                self.fields["ort"].get(), anzahl, preis, self.current_img_path, 
                self.check_wunsch_var.get()
            )
            
            self.db.cursor.execute("""
                INSERT INTO sammlung (name, nummer, marke, genre, verlag, jahr, zustand, erstausgabe, ort, anzahl, preis, bildpfad, wunschliste) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, data)
            self.db.conn.commit()
            
            messagebox.showinfo("Erfolg", "Gespeichert!")
            self.refresh_data()
            for e in self.fields.values(): e.delete(0, tk.END)
            self.current_img_path = ""
            self.btn_img.configure(text="Bild auswählen")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Der Eintrag konnte nicht gespeichert werden.\n\nGrund:\n{str(e)}")

    def show_context_menu(self, event, tree):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Eintrag bearbeiten", command=lambda: self.open_edit_window(tree))
            menu.add_command(label="Eintrag löschen", command=lambda: self.confirm_delete(tree))
            menu.post(event.x_root, event.y_root)

    def open_edit_window(self, tree):
        selected = tree.selection()
        if selected:
            item_id = tree.item(selected)['values'][0]
            self.db.cursor.execute("SELECT * FROM sammlung WHERE id = ?", (item_id,))
            data = self.db.cursor.fetchone()
            if data:
                EditWindow(self, data, self.refresh_data)
# Löschen/delete
    def confirm_delete(self, tree):
        selected = tree.selection()
        if selected:
            item_id = tree.item(selected)['values'][0]
            if messagebox.askyesno("Löschen?", "Diesen Eintrag wirklich entfernen?"):
                self.db.cursor.execute("DELETE FROM sammlung WHERE id = ?", (item_id,))
                self.db.conn.commit()
                self.refresh_data()

    def refresh_data(self):
        search = self.search_var.get()
        by = self.search_type.get()
        for t in [self.tree_sammlung, self.tree_wunsch]:
            for i in t.get_children(): t.delete(i)
            
        for r in self.db.get_filtered(0, search, by):
            self.tree_sammlung.insert("", "end", values=(r["id"], r["name"], r["nummer"], r["genre"], r["verlag"], f"{float(r['preis']):.2f}€"))
        for r in self.db.get_filtered(1, search, by):
            self.tree_wunsch.insert("", "end", values=(r["id"], r["name"], r["nummer"], r["genre"], r["verlag"], f"{float(r['preis']):.2f}€"))
            
        try:
            self.db.cursor.execute("SELECT SUM(anzahl) as total_anz, SUM(preis * anzahl) as total_val FROM sammlung WHERE wunschliste = 0")
            stats = self.db.cursor.fetchone()
            total_items = stats["total_anz"] if stats and stats["total_anz"] is not None else 0
            total_value = stats["total_val"] if stats and stats["total_val"] is not None else 0.0
            self.lbl_total_items.configure(text=f"Einträge gesamt: {total_items}")
            self.lbl_total_value.configure(text=f"Gesamtwert: {total_value:.2f} €")
        except Exception: pass

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Bilder", "*.jpg *.png *.jpeg")])
        if path:
            filename = os.path.basename(path)
            dest = os.path.join(IMAGE_DIR, filename)
            if not os.path.exists(dest):
                shutil.copy(path, dest)
            self.current_img_path = os.path.relpath(dest, BASE_DIR)
            self.btn_img.configure(text="Bild auswählen")
# HTML Dokumente erstellen / HTML File
    def export_html(self):
        self.db.cursor.execute("SELECT name, nummer, genre, verlag, preis, wunschliste FROM sammlung ORDER BY wunschliste ASC, name ASC")
        data = self.db.cursor.fetchall()
        
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>Übersicht</title>
    <style> 
        body { font-family: 'Nirmala Text', Lora, 'Cascadia Mono SemiLight'; background-color: #F7F0F0; color: #663357; margin: 40px; }
        
        h1 { font-size: 26px; font-weight: 600; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; margin-bottom: 20px; color: #111111; }
       
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
       
        th { background-color: #f7f2f7; color: #555255; text-align: left; padding: 12px; font-size: 14px; font-weight: 600; border-bottom: 2px solid #e0e0e0; }
        
        td { padding: 12px; font-size: 14px; border-bottom: 1px solid #eeeeee; color: #444444; }
      
        tr:nth-child(even) { background-color: #fafafa; }
      
        tr:hover { background-color: #f1f1f1; }
        .status-besitz { color: #2e7d32; font-weight: bold; }
        .status-wunsch { color: #c62828; font-weight: bold; }
        .btn-group { margin-bottom: 25px; background: #fafafa; padding: 15px; border-radius: 6px; border: 1px solid #eaeaea; }
        .btn-action { background-color: #212121; color: white; border: none; padding: 11px 22px; font-size: 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; font-weight: 600; }
        .btn-action:hover { background-color: #454282; }
       
        @media print {
            body { margin: 20px; color: #010200; }
            .btn-group { display: none !important; }
            tr { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div id="buttons" class="btn-group">
        <button class="btn-action" onclick="window.print()">Drucken / PDF speichern 🖨️</button>
    </div>

    <h1>Übersicht</h1>
    <table>
        <tr>
            <th>Status</th>
            <th>Name</th>
            <th>Nr.</th>
            <th>Genre</th>
            <th>Verlag</th>
            <th>Preis</th>
        </tr>"""
        
        for r in data:
            status_text = "Sammlung" if r["wunschliste"] == 0 else "Wunschliste"
            status_class = "status-besitz" if r["wunschliste"] == 0 else "status-wunsch"
            html += f"""
        <tr>
            <td class='{status_class}'>{status_text}</td>
            <td>{r["name"]}</td>
            <td>{r["nummer"] if r["nummer"] else '-'}</td>
            <td>{r["genre"] if r["genre"] else '-'}</td>
            <td>{r["verlag"] if r["verlag"] else '-'}</td>
            <td>{float(r["preis"]):.2f} €</td>
        </tr>"""
            
        html += """
    </table>
</body>
</html>"""
        
        path = os.path.join(BASE_DIR, "liste_aktuell.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        os.startfile(path)

if __name__ == "__main__":
    app = App()
    app.mainloop()


