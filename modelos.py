from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text # Importamos Text para descripciones largas

class Base(DeclarativeBase):
    pass

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String(100))
    codigo_estudiante: Mapped[str] = mapped_column(String(9), unique=True)
    correo: Mapped[str] = mapped_column(String(100), unique=True)
    nombre_usuario: Mapped[str] = mapped_column(String(50), unique=True)
    contrasena: Mapped[str] = mapped_column(String(255))
    
    # --- NUEVOS CAMPOS ---
    rol: Mapped[str] = mapped_column(String(20)) # "estudiante" o "tutor"
    materias: Mapped[str | None] = mapped_column(Text, nullable=True)
    conocimientos: Mapped[str | None] = mapped_column(Text, nullable=True)