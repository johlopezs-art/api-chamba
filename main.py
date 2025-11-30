from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from database import engine, get_db
import models, schemas
from repository import UserRepository

# 1. Crear las tablas en la BD si no existen
models.Base.metadata.create_all(bind=engine)

# 2. Iniciar la APP
app = FastAPI(title="ChambaNow API Completa")

# --- CONFIGURACIÓN DE CORS ---
origins = [
    "http://localhost",
    "http://localhost:8100",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. AUTENTICACIÓN Y USUARIOS
# ==========================================

@app.post("/login", response_model=schemas.UsuarioResponse)
def login(datos: schemas.LoginRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    usuario = repo.verify_login(datos.email, datos.password)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciales incorrectas"
        )
    return usuario

@app.post("/usuarios/", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_user_by_email(usuario.email):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    return repo.create_user(usuario)

@app.get("/usuarios/{user_id}", response_model=schemas.UsuarioResponse)
def obtener_usuario(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    usuario = repo.get_user_by_id(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@app.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    exito = repo.delete_user(user_id)
    if not exito:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return None

# ==========================================
# 2. PERFIL PROFESIONAL
# ==========================================

@app.put("/perfil/{user_id}", response_model=schemas.UsuarioResponse)
def actualizar_perfil_completo(user_id: int, perfil: schemas.PerfilUpdate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    usuario = repo.update_profile(user_id, perfil)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@app.patch("/perfil/{user_id}", response_model=schemas.UsuarioResponse)
def actualizar_perfil_parcial(user_id: int, perfil: schemas.PerfilUpdate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    usuario = repo.patch_profile(user_id, perfil)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ==========================================
# 3. SOLICITUDES DE TRABAJO (OFERTAS)
# ==========================================

@app.post("/solicitudes/", response_model=schemas.SolicitudResponse)
def crear_solicitud(solicitud: schemas.SolicitudCreate, db: Session = Depends(get_db)):
    usuario_creador = db.query(models.Usuario).filter(models.Usuario.id == solicitud.usuario_id).first()
    
    nueva_solicitud = models.Solicitud(
        **solicitud.dict(), 
        foto_usuario=usuario_creador.foto if usuario_creador else None
    )
    
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return nueva_solicitud

@app.get("/solicitudes/", response_model=List[schemas.SolicitudResponse])
def listar_solicitudes(db: Session = Depends(get_db)):
    return db.query(models.Solicitud).all()

@app.get("/solicitudes/{id}", response_model=schemas.SolicitudResponse)
def obtener_solicitud_detalle(id: int, db: Session = Depends(get_db)):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud

# ==========================================
# 4. BANDEJA DE POSTULACIONES
# ==========================================

@app.post("/postular/", status_code=status.HTTP_201_CREATED)
def postular_trabajo(postulacion: schemas.PostulacionCreate, db: Session = Depends(get_db)):
    # 1. Obtener la solicitud para validar el dueño
    solicitud_obj = db.query(models.Solicitud).filter(models.Solicitud.id == postulacion.solicitud_id).first()
    
    if not solicitud_obj:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # --- VALIDACIÓN NUEVA: NO AUTO-POSTULARSE ---
    if solicitud_obj.usuario_id == postulacion.usuario_id:
        raise HTTPException(status_code=400, detail="No puedes postular a tu propia oferta.")

    # 2. Verificar si ya postuló antes
    existe = db.query(models.Postulacion).filter(
        models.Postulacion.solicitud_id == postulacion.solicitud_id,
        models.Postulacion.usuario_id == postulacion.usuario_id
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Ya has postulado a este trabajo")

    # 3. Crear postulación
    nueva = models.Postulacion(
        solicitud_id=postulacion.solicitud_id, 
        usuario_id=postulacion.usuario_id,
        estado="pendiente"
    )
    db.add(nueva)
    db.commit()
    return {"mensaje": "Postulación exitosa"}

@app.get("/mis-postulaciones/{usuario_id}")
def ver_mis_postulaciones(usuario_id: int, db: Session = Depends(get_db)):
    resultados = []
    postulaciones = db.query(models.Postulacion).filter(models.Postulacion.usuario_id == usuario_id).all()
    
    for p in postulaciones:
        trabajo = db.query(models.Solicitud).filter(models.Solicitud.id == p.solicitud_id).first()
        
        if trabajo:
            dueno = db.query(models.Usuario).filter(models.Usuario.id == trabajo.usuario_id).first()
            
            resultados.append({
                "id": p.id,
                "solicitud_titulo": trabajo.titulo,
                "estado": p.estado,
                "email_contacto": dueno.email if (dueno and p.estado == 'aceptada') else None,
                "nombre_contacto": f"{dueno.nombre} {dueno.apellido}" if (dueno and p.estado == 'aceptada') else None
            })
    return resultados

@app.get("/mis-solicitudes-creadas/{usuario_id}")
def ver_mis_creaciones_y_postulantes(usuario_id: int, db: Session = Depends(get_db)):
    resultados = []
    mis_trabajos = db.query(models.Solicitud).filter(models.Solicitud.usuario_id == usuario_id).all()
    
    for trabajo in mis_trabajos:
        postulantes_db = db.query(models.Postulacion).filter(models.Postulacion.solicitud_id == trabajo.id).all()
        lista_postulantes = []
        
        for p in postulantes_db:
            datos_usuario = db.query(models.Usuario).filter(models.Usuario.id == p.usuario_id).first()
            
            if datos_usuario:
                lista_postulantes.append({
                    "postulacion_id": p.id,
                    "nombre": f"{datos_usuario.nombre} {datos_usuario.apellido}",
                    "profesion": datos_usuario.profesion,
                    "email": datos_usuario.email,
                    "foto": datos_usuario.foto,
                    "estado": p.estado
                })
            
        resultados.append({
            "solicitud_id": trabajo.id,
            "titulo": trabajo.titulo,
            "postulantes": lista_postulantes
        })
    return resultados

@app.put("/postulaciones/{id}/estado")
def cambiar_estado_postulacion(id: int, estado: str, db: Session = Depends(get_db)):
    postulacion = db.query(models.Postulacion).filter(models.Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    
    postulacion.estado = estado
    db.commit()
    return {"mensaje": f"Postulación marcada como {estado}"}