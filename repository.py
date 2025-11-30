from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas

# Configuración para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    # --- VERIFICAR LOGIN (Nuevo) ---
    def verify_login(self, email: str, password: str):
        # 1. Buscar usuario por email
        user = self.get_user_by_email(email)
        if not user:
            return None # El usuario no existe
        
        # 2. Verificar si la contraseña coincide con el hash
        if not pwd_context.verify(password, user.password):
            return None # Contraseña incorrecta
            
        return user # Login exitoso, retornamos el usuario

    # --- LEER (GET) ---
    def get_user_by_email(self, email: str):
        return self.db.query(models.Usuario).filter(models.Usuario.email == email).first()

    def get_user_by_id(self, user_id: int):
        return self.db.query(models.Usuario).filter(models.Usuario.id == user_id).first()

    # --- CREAR (POST) ---
    def create_user(self, user: schemas.UsuarioCreate):
        hashed_password = self.get_password_hash(user.password)
        db_user = models.Usuario(
            nombre=user.nombre,
            apellido=user.apellido,
            email=user.email,
            password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    # --- ACTUALIZAR COMPLETO (PUT) ---
    def update_profile(self, user_id: int, profile: schemas.PerfilUpdate):
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        # Reemplaza todo (si viene null, se pone null)
        db_user.ocupacion = profile.ocupacion
        db_user.profesion = profile.profesion
        db_user.habilidades = profile.habilidades
        db_user.latitud = profile.latitud
        db_user.longitud = profile.longitud
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    # --- ACTUALIZAR PARCIAL (PATCH) ---
    def patch_profile(self, user_id: int, profile: schemas.PerfilUpdate):
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        # Solo actualiza los campos que enviaron valor
        update_data = profile.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_user, key, value)
            
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    # --- BORRAR (DELETE) ---
    def delete_user(self, user_id: int):
        db_user = self.get_user_by_id(user_id)
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
            return True
        return False