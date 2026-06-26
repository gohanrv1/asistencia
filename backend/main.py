from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Text, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, computed_field
from typing import List, Optional
from datetime import datetime
import uuid
import os
import csv
import io
import shutil
import time

# ── Base de datos ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./asistencia.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tabla asociativa muchos a muchos para Proyectos y Personas
project_person = Table(
    "project_person",
    Base.metadata,
    Column("project_id", String, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("person_id", String, ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
)

# ── Modelos ORM ───────────────────────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"
    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at  = Column(DateTime, default=datetime.utcnow)
    persons     = relationship("Person", secondary=project_person, back_populates="projects")
    events      = relationship("Event",  back_populates="project", cascade="all, delete-orphan")

class Person(Base):
    __tablename__ = "persons"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombres    = Column(String, nullable=False)
    apellidos  = Column(String, nullable=False)
    cedula     = Column(String, nullable=False)
    cargo      = Column(String, nullable=False)
    correo     = Column(String, default="")
    celular    = Column(String, default="")
    projects   = relationship("Project", secondary=project_person, back_populates="persons")

class Event(Base):
    __tablename__ = "events"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name       = Column(String, nullable=False)
    date       = Column(String, nullable=False)
    notes      = Column(Text, default="")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    responsible_id = Column(String, ForeignKey("persons.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project    = relationship("Project", back_populates="events")
    attendance = relationship("Attendance", back_populates="event", cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = "attendance"
    id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id  = Column(String, ForeignKey("events.id"), nullable=False)
    person_id = Column(String, nullable=False)
    present   = Column(Boolean, default=False)
    signature = Column(Text, default="")
    updated_at= Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    event     = relationship("Event", back_populates="attendance")

# Verificación e inicialización de base de datos
# Usar checkfirst=True para evitar errores con múltiples workers
try:
    print("🔍 Inicializando base de datos...")
    # Crear tablas si no existen (checkfirst=True evita errores si ya existen)
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    # Verificar que el esquema es correcto
    with engine.connect() as conn:
        conn.execute(text("SELECT cedula FROM persons LIMIT 1"))
    print("✅ Base de datos OK")
except Exception as e:
    error_msg = str(e)
    if "no such column" in error_msg or "no such table" in error_msg:
        print(f"⚠️  Esquema desactualizado, recreando...")
        try:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine, checkfirst=True)
            print("✅ Base de datos recreada correctamente")
        except Exception as recreate_error:
            print(f"❌ Error al recrear: {str(recreate_error)[:200]}")
            # Continuar de todas formas - las tablas probablemente existen
    else:
        print(f"✅ Base de datos inicializada (algunas tablas ya existían)")

# ── App FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Asistencia API", 
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup Event ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("🚀 Aplicación FastAPI iniciada correctamente")
    print("📊 Endpoints disponibles en /docs")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Cerrando aplicación FastAPI...")

# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint para Easypanel/Docker"""
    return {"status": "ok", "service": "asistencia", "timestamp": datetime.utcnow().isoformat()}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Utilidad: ruta real del archivo sqlite ──────────────────────────────────
def resolve_sqlite_path():
    # soporta valores como sqlite:///./asistencia.db o sqlite:////absolute/path/asistencia.db
    if DATABASE_URL.startswith('sqlite:///'):
        path = DATABASE_URL.split('sqlite:///')[-1]
    elif DATABASE_URL.startswith('sqlite:'):
        path = DATABASE_URL.split('sqlite:')[-1]
    else:
        path = DATABASE_URL
    # si es relativo, relativizar respecto a este archivo
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    return os.path.abspath(path)

# ── Schemas Pydantic ──────────────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""

class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    class Config: from_attributes = True

class PersonCreate(BaseModel):
    id: Optional[str] = None
    nombres: str
    apellidos: str
    cedula: str
    cargo: str
    correo: Optional[str] = ""
    celular: Optional[str] = ""
    project_id: Optional[str] = None

class PersonOut(BaseModel):
    id: str
    nombres: str
    apellidos: str
    cedula: str
    cargo: str
    correo: str
    celular: str

    @computed_field
    @property
    def name(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @computed_field
    @property
    def role(self) -> str:
        return self.cargo

    class Config: from_attributes = True

class EventCreate(BaseModel):
    id: Optional[str] = None
    name: str
    date: str
    notes: Optional[str] = ""
    project_id: str
    responsible_id: Optional[str] = None

class EventOut(BaseModel):
    id: str
    name: str
    date: str
    notes: str
    project_id: str
    responsible_id: Optional[str]
    created_at: datetime
    class Config: from_attributes = True

class AttendanceRecord(BaseModel):
    person_id: str
    present: bool
    signature: Optional[str] = None

class AttendanceBulk(BaseModel):
    records: List[AttendanceRecord]

class ProjectPersonSync(BaseModel):
    project_id: str
    person_id: str

class SyncPayload(BaseModel):
    """Payload de sincronización offline → servidor"""
    projects:      List[ProjectCreate]      = []
    persons:       List[PersonCreate]       = []
    events:        List[EventCreate]        = []
    attendance:    dict                     = {}   # { event_id: { person_id: bool } }
    assignments:   List[ProjectPersonSync]  = []
    unassignments: List[ProjectPersonSync]  = []

# ── Endpoints: Proyectos ──────────────────────────────────────────────────────
@app.get("/api/projects", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()

@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    proj = Project(id=data.id or str(uuid.uuid4()), name=data.name, description=data.description or "")
    db.add(proj); db.commit(); db.refresh(proj)
    return proj

@app.get("/api/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj: raise HTTPException(404, "Proyecto no encontrado")
    return proj

@app.put("/api/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, data: ProjectCreate, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj: raise HTTPException(404, "Proyecto no encontrado")
    proj.name = data.name; proj.description = data.description or ""
    db.commit(); db.refresh(proj)
    return proj

@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj: raise HTTPException(404, "Proyecto no encontrado")
    db.delete(proj); db.commit()

# ── Endpoints: Personas ───────────────────────────────────────────────────────
@app.get("/api/persons", response_model=List[PersonOut])
def list_all_persons(db: Session = Depends(get_db)):
    return db.query(Person).all()

@app.get("/api/projects/{project_id}/persons", response_model=List[PersonOut])
def list_persons(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Proyecto no encontrado")
    return proj.persons

@app.post("/api/persons", response_model=PersonOut, status_code=201)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.cedula == data.cedula).first()
    if not person:
        person = Person(
            id=data.id or str(uuid.uuid4()),
            nombres=data.nombres,
            apellidos=data.apellidos,
            cedula=data.cedula,
            cargo=data.cargo,
            correo=data.correo or "",
            celular=data.celular or ""
        )
        db.add(person)
    
    if data.project_id:
        proj = db.query(Project).filter(Project.id == data.project_id).first()
        if not proj:
            raise HTTPException(404, "Proyecto no encontrado")
        if person not in proj.persons:
            proj.persons.append(person)
            
    db.commit()
    db.refresh(person)
    return person

@app.delete("/api/persons/{person_id}", status_code=204)
def delete_person(person_id: str, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person: raise HTTPException(404, "Persona no encontrada")
    db.delete(person); db.commit()

@app.post("/api/projects/{project_id}/persons/{person_id}", status_code=200)
def assign_person_to_project(project_id: str, person_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    person = db.query(Person).filter(Person.id == person_id).first()
    if not proj or not person:
        raise HTTPException(404, "Proyecto o persona no encontrado")
    if person not in proj.persons:
        proj.persons.append(person)
        db.commit()
    return {"ok": True}

@app.delete("/api/projects/{project_id}/persons/{person_id}", status_code=204)
def unassign_person_from_project(project_id: str, person_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    person = db.query(Person).filter(Person.id == person_id).first()
    if not proj or not person:
        raise HTTPException(404, "Proyecto o persona no encontrado")
    if person in proj.persons:
        proj.persons.remove(person)
        db.commit()

@app.get("/api/project-persons")
def list_project_persons(db: Session = Depends(get_db)):
    associations = db.query(project_person).all()
    return [{"project_id": a.project_id, "person_id": a.person_id} for a in associations]

@app.get("/api/persons/template")
def download_csv_template():
    csv_content = "nombres,apellidos,cedula,cargo,correo,celular\nJuan,Perez,12345678,Gerente,juan@example.com,555-1234\nMaria,Gomez,87654321,Analista,,555-5678\n"
    output = io.StringIO()
    output.write(csv_content)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.read().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantilla_personas.csv"}
    )

@app.post("/api/projects/{project_id}/persons/upload-csv")
def upload_csv(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Proyecto no encontrado")
    
    try:
        content = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        raise HTTPException(400, f"Error al procesar el archivo CSV: {str(e)}")
    
    created_count = 0
    assigned_count = 0
    
    for row in reader:
        nombres = row.get("nombres", "").strip()
        apellidos = row.get("apellidos", "").strip()
        cedula = row.get("cedula", "").strip()
        cargo = row.get("cargo", "").strip()
        
        if not nombres or not apellidos or not cedula or not cargo:
            continue
            
        correo = row.get("correo", "").strip()
        celular = row.get("celular", "").strip()
        
        person = db.query(Person).filter(Person.cedula == cedula).first()
        if not person:
            person = Person(
                id=str(uuid.uuid4()),
                nombres=nombres,
                apellidos=apellidos,
                cedula=cedula,
                cargo=cargo,
                correo=correo,
                celular=celular
            )
            db.add(person)
            created_count += 1
            
        if person not in proj.persons:
            proj.persons.append(person)
            assigned_count += 1
            
    db.commit()
    return {"ok": True, "created": created_count, "assigned": assigned_count}

# ── Endpoints: Eventos ────────────────────────────────────────────────────────
@app.get("/api/events", response_model=List[EventOut])
def list_events(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Event)
    if project_id: q = q.filter(Event.project_id == project_id)
    return q.order_by(Event.date.desc()).all()

@app.post("/api/events", response_model=EventOut, status_code=201)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    if not db.query(Project).filter(Project.id == data.project_id).first():
        raise HTTPException(404, "Proyecto no encontrado")
    ev = Event(id=data.id or str(uuid.uuid4()), name=data.name, date=data.date, notes=data.notes or "", project_id=data.project_id, responsible_id=data.responsible_id)
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev: raise HTTPException(404, "Evento no encontrado")
    db.delete(ev); db.commit()

# ── Endpoints: Asistencia ─────────────────────────────────────────────────────
@app.get("/api/events/{event_id}/attendance")
def get_attendance(event_id: str, db: Session = Depends(get_db)):
    records = db.query(Attendance).filter(Attendance.event_id == event_id).all()
    # return present status and signature if exists
    out = {}
    for r in records:
        out[r.person_id] = {"present": r.present, "signature": r.signature if getattr(r, 'signature', None) else None}
    return out

@app.post("/api/events/{event_id}/attendance")
def save_attendance(event_id: str, data: AttendanceBulk, db: Session = Depends(get_db)):
    if not db.query(Event).filter(Event.id == event_id).first():
        raise HTTPException(404, "Evento no encontrado")
    for rec in data.records:
        existing = db.query(Attendance).filter(
            Attendance.event_id == event_id,
            Attendance.person_id == rec.person_id
        ).first()
        if existing:
            existing.present = rec.present
            existing.signature = rec.signature or existing.signature
            existing.updated_at = datetime.utcnow()
        else:
            db.add(Attendance(event_id=event_id, person_id=rec.person_id, present=rec.present, signature=rec.signature or ""))
    db.commit()
    return {"ok": True}

# ── Endpoint: Sincronización offline ─────────────────────────────────────────
@app.post("/api/sync")
def sync_offline(payload: SyncPayload, db: Session = Depends(get_db)):
    """
    Recibe todos los cambios pendientes del cliente offline
    y los aplica en orden: proyectos → personas → eventos → asistencia.
    Usa upsert (insertar si no existe, ignorar si ya existe).
    """
    synced = {"projects": 0, "persons": 0, "events": 0, "attendance": 0, "assignments": 0, "unassignments": 0}

    for p in payload.projects:
        if not db.query(Project).filter(Project.id == p.id).first():
            db.add(Project(id=p.id, name=p.name, description=p.description or ""))
            synced["projects"] += 1

    db.flush()

    for p in payload.persons:
        person = db.query(Person).filter(Person.id == p.id).first()
        if not person:
            person = Person(
                id=p.id,
                nombres=p.nombres,
                apellidos=p.apellidos,
                cedula=p.cedula,
                cargo=p.cargo,
                correo=p.correo or "",
                celular=p.celular or ""
            )
            db.add(person)
            synced["persons"] += 1
        
        if p.project_id:
            proj = db.query(Project).filter(Project.id == p.project_id).first()
            if proj and person not in proj.persons:
                proj.persons.append(person)

    db.flush()

    for e in payload.events:
        if not db.query(Event).filter(Event.id == e.id).first():
            if db.query(Project).filter(Project.id == e.project_id).first():
                db.add(Event(id=e.id, name=e.name, date=e.date, notes=e.notes or "", project_id=e.project_id))
                synced["events"] += 1

    db.flush()

    for assoc in payload.assignments:
        proj = db.query(Project).filter(Project.id == assoc.project_id).first()
        person = db.query(Person).filter(Person.id == assoc.person_id).first()
        if proj and person and person not in proj.persons:
            proj.persons.append(person)
            synced["assignments"] += 1

    for assoc in payload.unassignments:
        proj = db.query(Project).filter(Project.id == assoc.project_id).first()
        person = db.query(Person).filter(Person.id == assoc.person_id).first()
        if proj and person and person in proj.persons:
            proj.persons.remove(person)
            synced["unassignments"] += 1

    db.flush()

    for event_id, records in payload.attendance.items():
        for person_id, present_val in records.items():
            # support either boolean or dict { present: bool, signature: str }
            if isinstance(present_val, dict):
                present = present_val.get('present', False)
                signature = present_val.get('signature')
            else:
                present = bool(present_val)
                signature = None

            existing = db.query(Attendance).filter(
                Attendance.event_id == event_id,
                Attendance.person_id == person_id
            ).first()
            if existing:
                existing.present = present
                if signature:
                    existing.signature = signature
            else:
                db.add(Attendance(event_id=event_id, person_id=person_id, present=present, signature=signature or ""))
            synced["attendance"] += 1

    db.commit()
    return {"ok": True, "synced": synced}


# ── Endpoint: Estadísticas simples para dashboard ─────────────────────────────
@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    projects = db.query(Project).count()
    persons = db.query(Person).count()
    events = db.query(Event).count()
    total_att = db.query(Attendance).count()
    total_present = db.query(Attendance).filter(Attendance.present == True).count()
    attendance_pct = round((total_present / total_att * 100), 1) if total_att else 0

    # últimos 5 eventos con porcentaje de asistencia
    recent = []
    evs = db.query(Event).order_by(Event.date.desc()).limit(5).all()
    for e in evs:
        present = db.query(Attendance).filter(Attendance.event_id == e.id, Attendance.present == True).count()
        # número esperado = número de personas asignadas al proyecto
        proj = db.query(Project).filter(Project.id == e.project_id).first()
        total_expected = len(proj.persons) if proj else 0
        pct = round((present / total_expected * 100), 1) if total_expected else 0
        resp = None
        if e.responsible_id:
            r = db.query(Person).filter(Person.id == e.responsible_id).first()
            if r: resp = f"{r.nombres} {r.apellidos}".strip()
        recent.append({"id": e.id, "name": e.name, "date": e.date, "present": present, "expected": total_expected, "pct": pct, "responsible": resp})

    return {
        "projects": projects,
        "persons": persons,
        "events": events,
        "attendance_records": total_att,
        "attendance_present": total_present,
        "attendance_pct": attendance_pct,
        "recent_events": recent
    }


# ── Endpoints: Backup / Restore de la base de datos (descargar / subir) ──────
@app.get("/api/db/download")
def download_db():
    db_file = resolve_sqlite_path()
    if not os.path.exists(db_file):
        raise HTTPException(404, "Archivo de base de datos no encontrado")
    return FileResponse(path=db_file, filename=os.path.basename(db_file), media_type='application/octet-stream')


@app.post("/api/db/upload")
def upload_db(file: UploadFile = File(...)):
    db_file = resolve_sqlite_path()
    tmp_path = db_file + ".upload.tmp"
    try:
        # Guardar carga temporal
        with open(tmp_path, 'wb') as out_f:
            shutil.copyfileobj(file.file, out_f)

        # Preparar backup path variable
        bak_path = None

        # Hacer backup del actual
        if os.path.exists(db_file):
            bak_path = f"{db_file}.bak-{int(time.time())}"
            shutil.copy2(db_file, bak_path)

        # Reemplazar
        try:
            # Declarar globals antes de usar engine
            global engine, SessionLocal
            # Cerrar conexiones activas antes de reemplazar
            try:
                engine.dispose()
            except Exception:
                pass
            os.replace(tmp_path, db_file)
        except Exception as e:
            raise HTTPException(500, f"No se pudo reemplazar la base de datos: {str(e)}")

        # Recrear engine y session local para usar la nueva base
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Asegurar que esquema esperado exista
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except Exception:
            pass

        return {"ok": True, "message": "Base de datos restaurada. Backup creado.", "backup": bak_path if os.path.exists(db_file) else None}
    finally:
        try:
            file.file.close()
        except Exception:
            pass

# ── Servir frontend estático ──────────────────────────────────────────────────
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
print(f"🔍 Buscando frontend en: {frontend_path}")
print(f"🔍 Frontend existe: {os.path.exists(frontend_path)}")

if os.path.exists(frontend_path):
    print(f"✅ Montando frontend desde {frontend_path}")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"⚠️  Advertencia: No se encontró el directorio frontend en {frontend_path}")
    
    # Fallback: servir un mensaje simple en la raíz
    @app.get("/")
    def root():
        return {
            "app": "Asistencia API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "api": "/api"
        }

