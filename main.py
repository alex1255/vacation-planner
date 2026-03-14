from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3, json, os
from typing import Optional

app = FastAPI()
DB = "/data/vacation.db"

def get_db():
    os.makedirs("/data", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vacations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            type_id TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            note TEXT
        );
    """)
    # Default categories
    existing = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing == 0:
        conn.executemany("INSERT INTO categories VALUES (?,?,?)", [
            ("urlaub", "Urlaub", "#4ade80"),
            ("homeoffice", "Homeoffice", "#60a5fa"),
            ("krank", "Krank", "#f59e0b"),
            ("sonstiges", "Sonstiges", "#f472b6"),
        ])
    # Default employees
    existing = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if existing == 0:
        conn.executemany("INSERT INTO employees (name) VALUES (?)", [
            ("Anna Schmidt",), ("Max Müller",), ("Lisa Weber",)
        ])
    conn.commit()
    conn.close()

init_db()

# --- Models ---
class Employee(BaseModel):
    name: str

class Category(BaseModel):
    id: str
    name: str
    color: str

class Vacation(BaseModel):
    employee_id: int
    type_id: str
    start_date: str
    end_date: str
    note: Optional[str] = ""

# --- Employees ---
@app.get("/api/employees")
def get_employees():
    conn = get_db()
    rows = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/employees")
def add_employee(emp: Employee):
    conn = get_db()
    cur = conn.execute("INSERT INTO employees (name) VALUES (?)", (emp.name,))
    conn.commit()
    id = cur.lastrowid
    conn.close()
    return {"id": id, "name": emp.name}

@app.delete("/api/employees/{id}")
def delete_employee(id: int):
    conn = get_db()
    conn.execute("DELETE FROM vacations WHERE employee_id=?", (id,))
    conn.execute("DELETE FROM employees WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# --- Categories ---
@app.get("/api/categories")
def get_categories():
    conn = get_db()
    rows = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/categories")
def add_category(cat: Category):
    conn = get_db()
    conn.execute("INSERT INTO categories VALUES (?,?,?)", (cat.id, cat.name, cat.color))
    conn.commit()
    conn.close()
    return dict(cat)

@app.put("/api/categories/{id}")
def update_category(id: str, cat: Category):
    conn = get_db()
    conn.execute("UPDATE categories SET name=?, color=? WHERE id=?", (cat.name, cat.color, id))
    conn.commit()
    conn.close()
    return dict(cat)

@app.delete("/api/categories/{id}")
def delete_category(id: str):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# --- Vacations ---
@app.get("/api/vacations")
def get_vacations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM vacations ORDER BY start_date").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/vacations")
def add_vacation(v: Vacation):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO vacations (employee_id, type_id, start_date, end_date, note) VALUES (?,?,?,?,?)",
        (v.employee_id, v.type_id, v.start_date, v.end_date, v.note)
    )
    conn.commit()
    id = cur.lastrowid
    conn.close()
    return {"id": id, **v.dict()}

@app.put("/api/vacations/{id}")
def update_vacation(id: int, v: Vacation):
    conn = get_db()
    conn.execute(
        "UPDATE vacations SET employee_id=?, type_id=?, start_date=?, end_date=?, note=? WHERE id=?",
        (v.employee_id, v.type_id, v.start_date, v.end_date, v.note, id)
    )
    conn.commit()
    conn.close()
    return {"id": id, **v.dict()}

@app.delete("/api/vacations/{id}")
def delete_vacation(id: int):
    conn = get_db()
    conn.execute("DELETE FROM vacations WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# Serve frontend
app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")
