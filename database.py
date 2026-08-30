"""
database.py
-----------
Capa de persistencia de Adivina_Estudio.

Usa SQLite (motor gratuito, sin servidor) como reemplazo local de
Supabase/Firebase, mencionados en el documento de planteamiento como
opciones de "Base de Datos & Autenticación" de nivel gratuito. El
esquema es compatible con una migración posterior a Postgres
(Supabase) casi sin cambios de lógica.
"""

import sqlite3
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "adivina_estudio.db")


def _hash_password(password: str) -> str:
    """Hash simple con sal fija para el prototipo.

    NOTA PEDAGÓGICA: para producción reemplazar por bcrypt/argon2.
    Se usa sha256 aquí para no depender de librerías externas y que
    el prototipo corra con solo `pip install streamlit`.
    """
    salt = "adivina_estudio_salt"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen. Llamar una vez al iniciar la app."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_usuario TEXT UNIQUE NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                puntos INTEGER NOT NULL DEFAULT 0,
                materia_preferida TEXT DEFAULT 'General',
                fecha_registro TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historial_adivinanzas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                adivinanza_id TEXT NOT NULL,
                acerto INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historial_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                materia TEXT NOT NULL,
                rol TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            """
        )


# --------------------------------------------------------------------
# Usuarios
# --------------------------------------------------------------------
def crear_usuario(nombre_usuario: str, correo: str, password: str) -> tuple[bool, str]:
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO usuarios (nombre_usuario, correo, password_hash, fecha_registro)
                   VALUES (?, ?, ?, ?)""",
                (nombre_usuario, correo, _hash_password(password), datetime.now().isoformat()),
            )
        return True, "Cuenta creada con éxito."
    except sqlite3.IntegrityError:
        return False, "El usuario o correo ya existe."


def validar_login(nombre_usuario: str, password: str):
    with get_connection() as conn:
        fila = conn.execute(
            "SELECT * FROM usuarios WHERE nombre_usuario = ?", (nombre_usuario,)
        ).fetchone()
    if fila is None:
        return None
    if fila["password_hash"] != _hash_password(password):
        return None
    return dict(fila)


def obtener_usuario(usuario_id: int):
    with get_connection() as conn:
        fila = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return dict(fila) if fila else None


def actualizar_preferencia(usuario_id: int, materia: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuarios SET materia_preferida = ? WHERE id = ?", (materia, usuario_id)
        )


def sumar_puntos(usuario_id: int, puntos: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuarios SET puntos = puntos + ? WHERE id = ?", (puntos, usuario_id)
        )


def tabla_posiciones(limite: int = 10):
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT nombre_usuario, puntos FROM usuarios ORDER BY puntos DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return [dict(f) for f in filas]


# --------------------------------------------------------------------
# Adivinanzas
# --------------------------------------------------------------------
def registrar_intento_adivinanza(usuario_id: int, adivinanza_id: str, acerto: bool):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO historial_adivinanzas (usuario_id, adivinanza_id, acerto, fecha)
               VALUES (?, ?, ?, ?)""",
            (usuario_id, adivinanza_id, int(acerto), datetime.now().isoformat()),
        )


def adivinanzas_resueltas(usuario_id: int) -> set:
    with get_connection() as conn:
        filas = conn.execute(
            """SELECT DISTINCT adivinanza_id FROM historial_adivinanzas
               WHERE usuario_id = ? AND acerto = 1""",
            (usuario_id,),
        ).fetchall()
    return {f["adivinanza_id"] for f in filas}


# --------------------------------------------------------------------
# Chat / Ghostie
# --------------------------------------------------------------------
def guardar_mensaje_chat(usuario_id: int, materia: str, rol: str, mensaje: str):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO historial_chat (usuario_id, materia, rol, mensaje, fecha)
               VALUES (?, ?, ?, ?, ?)""",
            (usuario_id, materia, rol, mensaje, datetime.now().isoformat()),
        )


def obtener_historial_chat(usuario_id: int, materia: str, limite: int = 30):
    with get_connection() as conn:
        filas = conn.execute(
            """SELECT rol, mensaje FROM historial_chat
               WHERE usuario_id = ? AND materia = ?
               ORDER BY id ASC LIMIT ?""",
            (usuario_id, materia, limite),
        ).fetchall()
    return [dict(f) for f in filas]
