from sqlalchemy import Column, Integer, String, Float
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Datos de Registro ---
    nombre = Column(String, index=True)
    apellido = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # Hash
    
    # --- Datos de Perfil ---
    ocupacion = Column(String, nullable=True)
    profesion = Column(String, nullable=True)
    habilidades = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    
    # --- Geolocalización y Foto ---
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    foto = Column(String, nullable=True) # <--- ¡ESTE CAMPO ES EL IMPORTANTE!

class Solicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    profesion = Column(String)
    especificacion = Column(String)
    sueldo = Column(String)
    usuario_id = Column(Integer)
    foto_usuario = Column(String, nullable=True) # <--- Y ESTE TAMBIÉN

class Postulacion(Base):
    __tablename__ = "postulaciones"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer)
    usuario_id = Column(Integer)
    estado = Column(String, default="pendiente")