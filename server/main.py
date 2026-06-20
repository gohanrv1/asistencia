"""
Servidor de Asistencia — FastAPI + SQLite
Ejecutar: uvicorn main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, os, hashlib, secrets, time
from datetime import datetime

app = FastAPI(title="Asistencia API", version="1.0")

# ── CORS (permite conexión desde el HTML) ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # En producción pon tu dominio aquí
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "asistencia.db")
API_KEY  = os.environ.get("API_KEY", "cambia_esta_clave_secreta")

# ── Base de datos ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS persons (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            role        TEXT DEFAULT '',
            project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            date        TEXT NOT NULL,
            notes       TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attendance (
            event_id    TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            person_id   TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
            present     INTEGER NOT NULL DEFAULT 0,
            updated_at  TEXT NOT NULL,
            PRIMARY KEY (event_id, person_id)
        );
        CREATE TABLE IF NOT EXISTS sync_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT NOT NULL,
            payload     TEXT NOT NULL,
            synced_at   TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ── Autenticación simple por API Key ─────────────────────────────────────────
def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return x_api_key

# ── Modelos Pydantic ──────────────────────────────────────────────────────────
class ProjectIn(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    created_at: Optional[str] = None

class PersonIn(BaseModel):
    id: str
    name: str
    role: Optional[str] = ""
    project_id: str
    created_at: Optional[str] = None

class EventIn(BaseModel):
    id: str
    name: str
    project_id: str
    date: str
    notes: Optional[str] = ""
    created_at: Optional[str] = None

class AttendanceRecord(BaseModel):
    person_id: str
    present: bool

class AttendanceBulk(BaseModel):
    records: List[AttendanceRecord]

class SyncPayload(BaseModel):
    projects:   List[ProjectIn]  = []
    persons:    List[PersonIn]   = []
    events:     List[EventIn]    = []
    attendance: dict             = {}   # { event_id: { person_id: bool } }

# ── Helper ────────────────────────────────────────────────────────────────────
def now():
    return datetime.utcnow().isoformat() + "Z"

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "time": now()}

# ── SYNC (endpoint principal — sube todo lo pendiente de una vez) ─────────────
@app.post("/sync", dependencies=[Depends(verify_key)])
def sync(payload: SyncPayload):
    """
    Recibe todo lo que el cliente tiene pendiente:
    proyectos, personas, eventos y asistencias.
    Hace upsert de todo y devuelve el estado completo del servidor.
    """
    conn = get_db()
    try:
        # Proyectos
        for p in payload.projects:
            conn.execute("""
                INSERT INTO projects(id,name,description,created_at)
                VALUES(?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description
            """, (p.id, p.name, p.description or "", p.created_at or now()))

        # Personas
        for p in payload.persons:
            conn.execute("""
                INSERT INTO persons(id,name,role,project_id,created_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, role=excluded.role
            """, (p.id, p.name, p.role or "", p.project_id, p.created_at or now()))

        # Eventos
        for e in payload.events:
            conn.execute("""
                INSERT INTO events(id,name,project_id,date,notes,created_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, date=excluded.date, notes=excluded.notes
            """, (e.id, e.name, e.project_id, e.date, e.notes or "", e.created_at or now()))

        # Asistencia
        for event_id, records in payload.attendance.items():
            for person_id, present in records.items():
                conn.execute("""
                    INSERT INTO attendance(event_id,person_id,present,updated_at)
                    VALUES(?,?,?,?)
                    ON CONFLICT(event_id,person_id) DO UPDATE SET present=excluded.present, updated_at=excluded.updated_at
                """, (event_id, person_id, 1 if present else 0, now()))

        conn.commit()
        return {"ok": True, "synced_at": now()}

    except Exception as ex:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        conn.close()

# ── PULL — devuelve todo el estado del servidor ───────────────────────────────
@app.get("/data", dependencies=[Depends(verify_key)])
def get_all_data():
    conn = get_db()
    projects  = [dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall()]
    persons   = [dict(r) for r in conn.execute("SELECT * FROM persons  ORDER BY created_at").fetchall()]
    events    = [dict(r) for r in conn.execute("SELECT * FROM events   ORDER BY date DESC").fetchall()]
    att_rows  = conn.execute("SELECT * FROM attendance").fetchall()
    conn.close()

    attendance = {}
    for row in att_rows:
        eid = row["event_id"]
        if eid not in attendance:
            attendance[eid] = {}
        attendance[eid][row["person_id"]] = bool(row["present"])

    return {"projects": projects, "persons": persons, "events": events, "attendance": attendance}

# ── Proyectos ─────────────────────────────────────────────────────────────────
@app.get("/projects", dependencies=[Depends(verify_key)])
def list_projects():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall()]
    conn.close()
    return rows

@app.delete("/projects/{pid}", dependencies=[Depends(verify_key)])
def delete_project(pid: str):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Personas ──────────────────────────────────────────────────────────────────
@app.get("/projects/{pid}/persons", dependencies=[Depends(verify_key)])
def list_persons(pid: str):
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM persons WHERE project_id=?", (pid,)).fetchall()]
    conn.close()
    return rows

@app.delete("/persons/{person_id}", dependencies=[Depends(verify_key)])
def delete_person(person_id: str):
    conn = get_db()
    conn.execute("DELETE FROM persons WHERE id=?", (person_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Eventos ───────────────────────────────────────────────────────────────────
@app.get("/projects/{pid}/events", dependencies=[Depends(verify_key)])
def list_events(pid: str):
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM events WHERE project_id=? ORDER BY date DESC", (pid,)).fetchall()]
    conn.close()
    return rows

@app.delete("/events/{eid}", dependencies=[Depends(verify_key)])
def delete_event(eid: str):
    conn = get_db()
    conn.execute("DELETE FROM events WHERE id=?", (eid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Asistencia de un evento ───────────────────────────────────────────────────
@app.get("/events/{eid}/attendance", dependencies=[Depends(verify_key)])
def get_attendance(eid: str):
    conn = get_db()
    rows = conn.execute("SELECT * FROM attendance WHERE event_id=?", (eid,)).fetchall()
    conn.close()
    return {r["person_id"]: bool(r["present"]) for r in rows}

# ── Servir el HTML desde /static ──────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
