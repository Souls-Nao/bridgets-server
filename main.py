from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import not_
from typing import List
import bcrypt
import random
import string

import modelos
import schemas
from conexion import engine, get_db

# Crear tablas en la BD si no existen
modelos.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bridgets API", version="1.0")

# --- FUNCIONES AUXILIARES ---
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generar_codigo_clase(db: Session) -> str:
    caracteres = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(random.choices(caracteres, k=6))
        if not db.query(modelos.Clase).filter(modelos.Clase.codigo_acceso == codigo).first():
            return codigo

# --- RUTAS DE VALIDACIÓN EN TIEMPO REAL ---
@app.get("/verificar/correo/{correo}")
def verificar_correo(correo: str, db: Session = Depends(get_db)):
    existe = db.query(modelos.Usuario).filter(modelos.Usuario.correo == correo).first()
    return {"disponible": not existe}

@app.get("/verificar/usuario/{nombre_usuario}")
def verificar_usuario(nombre_usuario: str, db: Session = Depends(get_db)):
    existe = db.query(modelos.Usuario).filter(modelos.Usuario.nombre_usuario == nombre_usuario).first()
    return {"disponible": not existe}

@app.get("/verificar/codigo/{codigo}")
def verificar_codigo(codigo: str, db: Session = Depends(get_db)):
    existe = db.query(modelos.Usuario).filter(modelos.Usuario.codigo_estudiante == codigo).first()
    return {"disponible": not existe}

# --- RUTAS DE USUARIOS Y AUTENTICACIÓN ---
@app.post("/usuarios/", response_model=schemas.UsuarioResponse)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Verificaciones extra por seguridad
    if db.query(modelos.Usuario).filter((modelos.Usuario.correo == usuario.correo) | (modelos.Usuario.nombre_usuario == usuario.nombre_usuario)).first():
        raise HTTPException(status_code=400, detail="Correo o usuario ya registrado")
    
    nuevo_usuario = modelos.Usuario(
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        nombre_usuario=usuario.nombre_usuario,
        codigo_estudiante=usuario.codigo_estudiante,
        rol=usuario.rol,
        contrasena=hash_password(usuario.contrasena)
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@app.post("/login/", response_model=schemas.UsuarioResponse)
def login(credenciales: schemas.LoginData, db: Session = Depends(get_db)):
    usuario = db.query(modelos.Usuario).filter(
        (modelos.Usuario.correo == credenciales.usuario_o_correo) | 
        (modelos.Usuario.nombre_usuario == credenciales.usuario_o_correo)
    ).first()
    
    if not usuario or not verify_password(credenciales.contrasena, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    return usuario

@app.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioResponse)
def actualizar_usuario(usuario_id: int, datos: schemas.UsuarioUpdate, db: Session = Depends(get_db)):
    usuario = db.query(modelos.Usuario).filter(modelos.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if datos.nombre_completo: usuario.nombre_completo = datos.nombre_completo
    if datos.correo: usuario.correo = datos.correo
    if datos.nombre_usuario: usuario.nombre_usuario = datos.nombre_usuario
    if datos.contrasena: usuario.contrasena = hash_password(datos.contrasena)
    
    db.commit()
    db.refresh(usuario)
    return usuario

# --- RUTAS DE CLASES ---
@app.post("/clases/", response_model=schemas.ClaseResponse)
def crear_clase(clase: schemas.ClaseCreate, db: Session = Depends(get_db)):
    tutor = db.query(modelos.Usuario).filter(modelos.Usuario.id == clase.tutor_id, modelos.Usuario.rol == 'tutor').first()
    if not tutor:
        raise HTTPException(status_code=403, detail="Solo los tutores pueden crear clases")
    
    nueva_clase = modelos.Clase(
        **clase.model_dump(exclude={'tutor_id'}),
        tutor_id=clase.tutor_id,
        codigo_acceso=generar_codigo_clase(db)
    )
    db.add(nueva_clase)
    db.commit()
    db.refresh(nueva_clase)
    return nueva_clase

@app.get("/clases/usuario/{usuario_id}", response_model=List[schemas.ClaseResponse])
def obtener_clases_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(modelos.Usuario).filter(modelos.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.rol == 'tutor':
        return usuario.clases_impartidas
    else:
        return [inscripcion.clase for inscripcion in usuario.inscripciones]

@app.post("/clases/inscribir/")
def inscribir_clase(datos: schemas.InscripcionCreate, db: Session = Depends(get_db)):
    clase = db.query(modelos.Clase).filter(modelos.Clase.codigo_acceso == datos.codigo_acceso).first()
    if not clase:
        raise HTTPException(status_code=404, detail="Código de clase inválido")
    
    inscripcion_existente = db.query(modelos.Inscripcion).filter(
        modelos.Inscripcion.estudiante_id == datos.estudiante_id,
        modelos.Inscripcion.clase_id == clase.id
    ).first()
    
    if inscripcion_existente:
        raise HTTPException(status_code=400, detail="Ya estás inscrito en esta clase")
        
    nueva_inscripcion = modelos.Inscripcion(estudiante_id=datos.estudiante_id, clase_id=clase.id)
    db.add(nueva_inscripcion)
    db.commit()
    return {"mensaje": "Inscripción exitosa", "clase_id": clase.id}

@app.get("/clases/buscar/", response_model=List[schemas.ClaseResponse])
def buscar_clases(usuario_id: int, q: str, db: Session = Depends(get_db)):
    # Obtener IDs de las clases a las que el usuario ya está inscrito
    subquery = db.query(modelos.Inscripcion.clase_id).filter(modelos.Inscripcion.estudiante_id == usuario_id)
    
    # Buscar clases por nombre o por nombre del tutor, excluyendo las ya inscritas
    clases = db.query(modelos.Clase).join(modelos.Usuario).filter(
        (modelos.Clase.nombre.ilike(f"%{q}%") | modelos.Usuario.nombre_completo.ilike(f"%{q}%")) &
        modelos.Clase.id.not_in(subquery)
    ).all()
    
    return clases

# --- RUTAS DE ANUNCIOS ---
@app.get("/clases/{clase_id}/anuncios/", response_model=List[schemas.AnuncioResponse])
def obtener_anuncios(clase_id: int, db: Session = Depends(get_db)):
    anuncios = db.query(modelos.Anuncio).filter(modelos.Anuncio.clase_id == clase_id).order_by(modelos.Anuncio.fecha_creacion.desc()).all()
    return anuncios

@app.post("/clases/{clase_id}/anuncios/", response_model=schemas.AnuncioResponse)
def crear_anuncio(clase_id: int, anuncio: schemas.AnuncioCreate, db: Session = Depends(get_db)):
    nuevo_anuncio = modelos.Anuncio(**anuncio.model_dump(), clase_id=clase_id)
    db.add(nuevo_anuncio)
    db.commit()
    db.refresh(nuevo_anuncio)
    return nuevo_anuncio

# --- RUTAS DE NOTAS ---
@app.post("/notas/", response_model=schemas.NotaResponse)
def crear_nota(nota: schemas.NotaCreate, db: Session = Depends(get_db)):
    nueva_nota = modelos.Nota(**nota.model_dump())
    db.add(nueva_nota)
    db.commit()
    db.refresh(nueva_nota)
    return nueva_nota

@app.get("/notas/usuario/{usuario_id}", response_model=List[schemas.NotaResponse])
def obtener_notas(usuario_id: int, db: Session = Depends(get_db)):
    notas = db.query(modelos.Nota).filter(modelos.Nota.estudiante_id == usuario_id).order_by(modelos.Nota.fecha_creacion.desc()).all()
    return notas
