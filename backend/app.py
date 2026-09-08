import os, uuid, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, String, Integer, DateTime, ForeignKey, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
try: import magic
except: magic=None

BASE_DIR=Path(__file__).resolve().parent.parent
DB=os.getenv("DATABASE_URL",f"sqlite:///{BASE_DIR / 'medtrail.db'}")
if DB.startswith("postgres://"):
    DB="postgresql+psycopg://" + DB.removeprefix("postgres://")
ARGS={"check_same_thread":False} if DB.startswith("sqlite") else {}
engine=create_engine(DB,connect_args=ARGS,pool_pre_ping=True)
STORE=Path(os.getenv("STORAGE_DIR",str(BASE_DIR / "storage"))); STORE.mkdir(parents=True,exist_ok=True)
MAX=int(os.getenv("MAX_FILE_SIZE_MB","20"))*1024*1024
SECRET=os.getenv("JWT_SECRET")
EMAIL=os.getenv("DEMO_EMAIL","admin@medtrail.local"); PASSWORD=os.getenv("DEMO_PASSWORD")
if not SECRET or not PASSWORD:
    raise RuntimeError("JWT_SECRET e DEMO_PASSWORD devem estar configurados")
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto"); auth=HTTPBearer(auto_error=False)
ALLOW={".pdf":{"application/pdf"},".png":{"image/png"},".jpg":{"image/jpeg"},".jpeg":{"image/jpeg"},
".docx":{"application/zip","application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
".xlsx":{"application/zip","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}}

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__="users"; id:Mapped[int]=mapped_column(primary_key=True); email:Mapped[str]=mapped_column(String(255),unique=True); password:Mapped[str]=mapped_column(String(255)); role:Mapped[str]=mapped_column(String(30),default="admin")
class Patient(Base):
    __tablename__="patients"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(255)); external_id:Mapped[str]=mapped_column(String(100),unique=True); birth_date:Mapped[str|None]=mapped_column(String(20),nullable=True); sex:Mapped[str|None]=mapped_column(String(30),nullable=True)
class Document(Base):
    __tablename__="documents"; id:Mapped[int]=mapped_column(primary_key=True); patient_id:Mapped[int]=mapped_column(ForeignKey("patients.id")); original:Mapped[str]=mapped_column(String(255)); stored:Mapped[str]=mapped_column(String(255),unique=True); mime:Mapped[str]=mapped_column(String(120)); size:Mapped[int]=mapped_column(Integer); sha256:Mapped[str]=mapped_column(String(64)); module:Mapped[str]=mapped_column(String(80)); created:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Audit(Base):
    __tablename__="audit"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int|None]=mapped_column(Integer,nullable=True); action:Mapped[str]=mapped_column(String(100)); details:Mapped[str]=mapped_column(Text); created:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine)

with Session(engine) as s:
    if not s.scalar(select(User).where(User.email==EMAIL)): s.add(User(email=EMAIL,password=pwd.hash(PASSWORD)))
    if not s.scalar(select(Patient).where(Patient.external_id=="DEMO-001")): s.add(Patient(name="Paciente Demo MEDTRAIL",external_id="DEMO-001",birth_date="1972-11-07",sex="M"))
    s.commit()

app=FastAPI(title="MEDTRAIL API",version="1.0.0")
def user(c:HTTPAuthorizationCredentials=Depends(auth)):
    if not c: raise HTTPException(401,"Autenticação necessária")
    try: uid=int(jwt.decode(c.credentials,SECRET,algorithms=["HS256"])["sub"])
    except: raise HTTPException(401,"Token inválido")
    with Session(engine) as s:
        u=s.get(User,uid)
        if not u: raise HTTPException(401,"Utilizador inválido")
        return u
def tok(u): return jwt.encode({"sub":str(u.id),"exp":datetime.now(timezone.utc)+timedelta(hours=8)},SECRET,algorithm="HS256")

@app.get("/health")
def health(): return {"status":"ok","service":"MEDTRAIL"}
@app.get("/",response_class=HTMLResponse)
def home(): return FileResponse(BASE_DIR / "frontend" / "index.html")
@app.post("/api/login")
def login(data:dict):
    with Session(engine) as s:
        u=s.scalar(select(User).where(User.email==data.get("email")))
        if not u or not pwd.verify(data.get("password",""),u.password): raise HTTPException(401,"Credenciais inválidas")
        return {"access_token":tok(u),"token_type":"bearer"}
@app.get("/api/patients")
def patients(u=Depends(user)):
    with Session(engine) as s:
        return [{"id":p.id,"name":p.name,"external_id":p.external_id,"birth_date":p.birth_date,"sex":p.sex} for p in s.scalars(select(Patient).order_by(Patient.id.desc()))]
@app.post("/api/upload")
async def upload(patient_id:int=Form(...),module:str=Form("GENERAL"),file:UploadFile=File(...),u=Depends(user)):
    name=Path(file.filename or "").name; ext=Path(name).suffix.lower()
    if ext not in ALLOW: raise HTTPException(400,"Tipo de ficheiro não permitido")
    with Session(engine) as s:
        if not s.get(Patient,patient_id): raise HTTPException(404,"Paciente não encontrado")
    stored=uuid.uuid4().hex+".upload"; dest=STORE/stored; total=0; sha=hashlib.sha256()
    try:
        with open(dest,"wb") as out:
            while True:
                b=await file.read(1024*1024)
                if not b: break
                total+=len(b)
                if total>MAX: raise HTTPException(413,"Ficheiro excede o limite")
                sha.update(b); out.write(b)
        detected=magic.from_file(str(dest),mime=True) if magic else (file.content_type or "")
        head=dest.read_bytes()[:16]
        sig=((ext==".pdf" and head.startswith(b"%PDF")) or (ext==".png" and head.startswith(b"\x89PNG")) or (ext in {".jpg",".jpeg"} and head.startswith(b"\xff\xd8\xff")) or (ext in {".docx",".xlsx"} and head.startswith(b"PK")))
        if detected not in ALLOW[ext] or not sig:
            dest.unlink(missing_ok=True); raise HTTPException(400,"Conteúdo não corresponde ao tipo permitido")
        with Session(engine) as s:
            d=Document(patient_id=patient_id,original=name,stored=stored,mime=detected,size=total,sha256=sha.hexdigest(),module=module[:80])
            s.add(d); s.add(Audit(user_id=u.id,action="upload",details=f"document={name};patient={patient_id};module={module}")); s.commit(); s.refresh(d)
            return {"id":d.id,"filename":name,"size":total,"sha256":d.sha256,"module":module}
    except:
        if dest.exists(): dest.unlink()
        raise
@app.get("/api/documents")
def documents(patient_id:int|None=None,u=Depends(user)):
    with Session(engine) as s:
        q=select(Document).order_by(Document.id.desc())
        if patient_id: q=q.where(Document.patient_id==patient_id)
        return [{"id":d.id,"patient_id":d.patient_id,"filename":d.original,"size":d.size,"module":d.module,"created":d.created.isoformat()} for d in s.scalars(q)]
@app.get("/api/documents/{id}")
def download(id:int,u=Depends(user)):
    with Session(engine) as s:
        d=s.get(Document,id)
        if not d: raise HTTPException(404,"Documento não encontrado")
        p=STORE/d.stored
        if not p.exists(): raise HTTPException(404,"Ficheiro não encontrado")
        return FileResponse(p,media_type=d.mime,filename=d.original)
