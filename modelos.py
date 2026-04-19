from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from conexion import Base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String)
    codigo_estudiante = Column(String, unique=True, nullable=True)
    correo = Column(String, unique=True)
    nombre_usuario = Column(String, unique=True)
    contrasena = Column(String)
    rol = Column(String) # 'estudiante' o 'tutor'
    
    # Datos extra de tutor
    materias = Column(String, nullable=True) 
    conocimientos = Column(String, nullable=True)

    # Relaciones (Conexiones con otras tablas)
    clases_creadas = relationship("Clase", back_populates="tutor")
    inscripciones = relationship("Inscripcion", back_populates="estudiante")

class Clase(Base):
    __tablename__ = "clases"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    descripcion = Column(String)
    horario = Column(String)
    codigo_acceso = Column(String, unique=True, index=True) # Código de 6 letras para unirse
    color_hex = Column(String, default="#1E4C7A") # Color para la tarjeta
    tutor_id = Column(Integer, ForeignKey("usuarios.id"))

    # Relaciones
    tutor = relationship("Usuario", back_populates="clases_creadas")
    inscritos = relationship("Inscripcion", back_populates="clase")
    anuncios = relationship("Anuncio", back_populates="clase")

class Inscripcion(Base):
    """Tabla intermedia para saber qué estudiante está en qué clase"""
    __tablename__ = "inscripciones"
    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("usuarios.id"))
    clase_id = Column(Integer, ForeignKey("clases.id"))

    estudiante = relationship("Usuario", back_populates="inscripciones")
    clase = relationship("Clase", back_populates="inscritos")

class Anuncio(Base):
    __tablename__ = "anuncios"
    id = Column(Integer, primary_key=True, index=True)
    contenido = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    clase_id = Column(Integer, ForeignKey("clases.id"))
    autor_id = Column(Integer, ForeignKey("usuarios.id")) # Quien lo publicó

    clase = relationship("Clase", back_populates="anuncios")
