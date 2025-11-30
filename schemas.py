from pydantic import BaseModel, EmailStr
from typing import Optional

# --- Esquema Base (datos comunes) ---
class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr

# --- Datos para CREAR cuenta (Registro) ---
class UsuarioCreate(UsuarioBase):
    password: str

# --- Datos para LOGIN (Nuevo) ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Datos para ACTUALIZAR Perfil (Opcionales) ---
class PerfilUpdate(BaseModel):
    ocupacion: Optional[str] = None
    profesion: Optional[str] = None
    habilidades: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

# --- Datos de RESPUESTA (Lo que se devuelve al frontend) ---
class UsuarioResponse(UsuarioBase):
    id: int
    ocupacion: Optional[str] = None
    profesion: Optional[str] = None
    habilidades: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    class Config:
        from_attributes = True

class SolicitudCreate(BaseModel):
    titulo: str
    profesion: str
    especificacion: str
    sueldo: str
    usuario_id: int

class SolicitudResponse(SolicitudCreate):
    id: int
    class Config:
        from_attributes = True

class PostulacionCreate(BaseModel):
    solicitud_id: int
    usuario_id: int

class PostulacionResponse(BaseModel):
    id: int
    solicitud_titulo: str
    estado: str
    # Datos para contacto (solo si es necesario)
    email_contacto: Optional[str] = None
    nombre_contacto: Optional[str] = None