from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import bcrypt

# Importamos todos los modelos para que la base de datos los reconozca al iniciar
from modelos import Base, Usuario, Clase, Inscripcion, Anuncio

# 1. Conexión a la base de datos
URL_BASE_DATOS = "postgresql://neondb_owner:npg_hEmXZcU01ofn@ep-frosty-grass-an7a2cs1-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
motor = create_engine(URL_BASE_DATOS)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

# Creamos las tablas que falten (incluyendo las nuevas de Clases y Anuncios)
Base.metadata.create_all(bind=motor)

# 2. Encender el servidor FastAPI
app = FastAPI(title="Servidor Bridgets")

# --- FUNCIONES DE SEGURIDAD Y BASE DE DATOS ---

def encriptar_contrasena(contrasena: str) -> str:
    contrasena_bytes = contrasena.encode('utf-8')
    sal = bcrypt.gensalt()
    hash_seguro = bcrypt.hashpw(contrasena_bytes, sal)
    return hash_seguro.decode('utf-8')

def verificar_contrasena(contrasena_plana: str, contrasena_encriptada: str) -> bool:
    contrasena_bytes = contrasena_plana.encode('utf-8')
    encriptada_bytes = contrasena_encriptada.encode('utf-8')
    return bcrypt.checkpw(contrasena_bytes, encriptada_bytes)

def obtener_bd():
    bd = SesionLocal()
    try:
        yield bd
    finally:
        bd.close()

# --- MOLDES PYDANTIC ---

class UsuarioNuevo(BaseModel):
    nombre_completo: str
    codigo_estudiante: str
    correo: str
    nombre_usuario: str
    contrasena: str
    rol: str
    materias: str = "" 
    conocimientos: str = "" 

class UsuarioLogin(BaseModel):
    nombre_usuario: str
    contrasena: str


# --- RUTAS DE LA APLICACIÓN ---

@app.get("/")
def ping_servidor():
    """Ruta básica para que el Splash Screen del cliente detecte que el servidor despertó."""
    return {"estado": "Servidor activo y listo"}

@app.post("/login/")
def iniciar_sesion(datos: UsuarioLogin, bd: Session = Depends(obtener_bd)):
    # A. Buscamos si el usuario existe
    usuario_db = bd.query(Usuario).filter(Usuario.nombre_usuario == datos.nombre_usuario).first()
    
    if not usuario_db:
         raise HTTPException(status_code=404, detail="El usuario no existe.")

    # B. Verificamos la contraseña usando bcrypt
    if not verificar_contrasena(datos.contrasena, usuario_db.contrasena): 
         raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    # C. Si todo coincide, damos luz verde
    return {
        "mensaje": "¡Inicio de sesión exitoso!", 
        "rol": usuario_db.rol,
        "usuario": usuario_db.nombre_usuario
    }

@app.post("/registro/")
def registrar_usuario(usuario: UsuarioNuevo, bd: Session = Depends(obtener_bd)):
    # 1. VERIFICACIONES DE FORMATO
    if len(usuario.codigo_estudiante) != 9 and usuario.rol == "estudiante":
        raise HTTPException(status_code=400, detail="El código de estudiante debe tener exactamente 9 caracteres.")
        
    if "@" not in usuario.correo or "." not in usuario.correo:
        raise HTTPException(status_code=400, detail="Por favor, ingresa un formato de correo electrónico válido.")
    
    # 2. VERIFICACIONES DE DUPLICADOS EN BASE DE DATOS
    if usuario.rol == "estudiante" and bd.query(Usuario).filter(Usuario.codigo_estudiante == usuario.codigo_estudiante).first():
         raise HTTPException(status_code=400, detail="Este código de estudiante ya se encuentra registrado.")

    if bd.query(Usuario).filter(Usuario.correo == usuario.correo).first():
         raise HTTPException(status_code=400, detail="Este correo electrónico ya está vinculado a otra cuenta.")

    if bd.query(Usuario).filter(Usuario.nombre_usuario == usuario.nombre_usuario).first():
         raise HTTPException(status_code=400, detail="Este nombre de usuario ya está en uso. Por favor, elige otro.")

    # 3. GUARDADO
    contrasena_segura = encriptar_contrasena(usuario.contrasena)    
    
    nuevo_usuario_bd = Usuario(
        nombre_completo=usuario.nombre_completo,
        codigo_estudiante=usuario.codigo_estudiante,
        correo=usuario.correo,
        nombre_usuario=usuario.nombre_usuario,
        contrasena=contrasena_segura,
        rol=usuario.rol,
        materias=usuario.materias,
        conocimientos=usuario.conocimientos
    )
    
    try:
        bd.add(nuevo_usuario_bd)
        bd.commit()
    except Exception as e:
        bd.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor al intentar crear la cuenta.")
    
    return {"mensaje": f"¡Cuenta creada con éxito para {usuario.nombre_usuario}!"}
