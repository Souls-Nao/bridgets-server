from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- USUARIOS ---
class UsuarioBase(BaseModel):
    nombre_completo: str
    correo: EmailStr
    nombre_usuario: str
    codigo_estudiante: Optional[str] = None
    rol: str

class UsuarioCreate(UsuarioBase):
    contrasena: str

class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[EmailStr] = None
    nombre_usuario: Optional[str] = None
    contrasena: Optional[str] = None

class UsuarioResponse(UsuarioBase):
    id: int
    class Config:
        from_attributes = True

class LoginData(BaseModel):
    usuario_o_correo: str
    contrasena: str

# --- CLASES ---
class ClaseBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    horario: Optional[str] = None
    color_hex: Optional[str] = "#FFFFFF"

class ClaseCreate(ClaseBase):
    tutor_id: int

class ClaseResponse(ClaseBase):
    id: int
    codigo_acceso: str
    tutor_id: int
    class Config:
        from_attributes = True

class InscripcionCreate(BaseModel):
    codigo_acceso: str
    estudiante_id: int

# --- ANUNCIOS ---
class AnuncioBase(BaseModel):
    contenido: str

class AnuncioCreate(AnuncioBase):
    pass

class AnuncioResponse(AnuncioBase):
    id: int
    fecha_creacion: datetime
    clase_id: int
    class Config:
        from_attributes = True

# --- NOTAS ---
class NotaBase(BaseModel):
    titulo: str
    contenido_formato: str
    clase_id: Optional[int] = None

class NotaCreate(NotaBase):
    estudiante_id: int

class NotaResponse(NotaBase):
    id: int
    fecha_creacion: datetime
    estudiante_id: int
    class Config:
        from_attributes = True
