import re
import bcrypt
from config import DatabaseConfig, AdminConfig

# ---------------------------------------------------------------
# Expresiones regulares para validar datos
# ---------------------------------------------------------------
RE_NOMBRE = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]{2,50}$')
RE_EMAIL = re.compile(r'^[\w.+-]+@[\w-]+(\.[\w-]+)+$')
RE_USERNAME = re.compile(r'^[A-Za-z0-9_]{3,30}$')


# ---------------------------------------------------------------
# Acceso a la base de datos
# ---------------------------------------------------------------
def ejecutar(query, params=None, fetch=None, commit=False):
    """
    Ejecuta una consulta SQL con parámetros (evita inyección SQL).
      fetch='one'  -> devuelve una fila (dict) o None
      fetch='all'  -> devuelve una lista de filas
      fetch=None   -> devuelve {'lastrowid': ..., 'rowcount': ...}
    """
    connection = DatabaseConfig.get_connection()
    if connection is None:
        raise ConnectionError('No se pudo conectar a la base de datos')

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch == 'one':
            resultado = cursor.fetchone()
        elif fetch == 'all':
            resultado = cursor.fetchall()
        else:
            resultado = {'lastrowid': cursor.lastrowid, 'rowcount': cursor.rowcount}
        if commit:
            connection.commit()
        return resultado
    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------
# Contraseñas (bcrypt)
# ---------------------------------------------------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except ValueError:
        return False


# ---------------------------------------------------------------
# Validaciones (devuelven: errores por campo, datos limpios)
# ---------------------------------------------------------------
def validar_estudiante(data):
    errores = {}
    if not isinstance(data, dict):
        return {'general': 'Se esperaba un JSON con los datos del estudiante'}, {}

    nombre = str(data.get('nombre') or '').strip()
    apellido = str(data.get('apellido') or '').strip()
    email = str(data.get('email') or '').strip().lower()
    carrera = str(data.get('carrera') or '').strip()
    edad = data.get('edad')

    if not RE_NOMBRE.match(nombre):
        errores['nombre'] = 'El nombre solo puede tener letras y espacios (2 a 50 caracteres)'
    if not RE_NOMBRE.match(apellido):
        errores['apellido'] = 'El apellido solo puede tener letras y espacios (2 a 50 caracteres)'
    if len(email) > 100 or not RE_EMAIL.match(email):
        errores['email'] = 'Ingresa un correo electrónico válido'
    if not (3 <= len(carrera) <= 100):
        errores['carrera'] = 'La carrera debe tener entre 3 y 100 caracteres'

    try:
        if isinstance(edad, (bool, float)):
            raise ValueError
        edad = int(edad)
        if edad < 15 or edad > 100:
            errores['edad'] = 'La edad debe estar entre 15 y 100 años'
    except (TypeError, ValueError):
        errores['edad'] = 'La edad debe ser un número entero'

    limpio = {'nombre': nombre, 'apellido': apellido, 'email': email,
              'edad': edad, 'carrera': carrera}
    return errores, limpio


def validar_registro(data):
    errores = {}
    if not isinstance(data, dict):
        return {'general': 'Se esperaba un JSON con los datos del usuario'}, {}

    username = str(data.get('username') or '').strip()
    email = str(data.get('email') or '').strip().lower()
    password = str(data.get('password') or '')

    if not RE_USERNAME.match(username):
        errores['username'] = 'El usuario debe tener 3 a 30 caracteres (letras, números o guion bajo)'
    if len(email) > 100 or not RE_EMAIL.match(email):
        errores['email'] = 'Ingresa un correo electrónico válido'
    if len(password) < 6 or len(password.encode('utf-8')) > 72:
        errores['password'] = 'La contraseña debe tener entre 6 y 72 caracteres'
    elif not (re.search(r'[A-Za-z]', password) and re.search(r'\d', password)):
        errores['password'] = 'La contraseña debe incluir al menos una letra y un número'

    return errores, {'username': username, 'email': email, 'password': password}


# ---------------------------------------------------------------
# Creación de tablas y usuario administrador
# ---------------------------------------------------------------
def init_db():
    """Crea las tablas si no existen y el usuario admin si falta."""
    ejecutar('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(30) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            rol ENUM('admin','usuario') NOT NULL DEFAULT 'usuario',
            activo TINYINT(1) NOT NULL DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''', commit=True)

    ejecutar('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            apellido VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            edad INT NOT NULL,
            carrera VARCHAR(100) NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_apellido (apellido),
            INDEX idx_carrera (carrera)
        )''', commit=True)

    ejecutar('''
        CREATE TABLE IF NOT EXISTS tokens_revocados (
            id INT AUTO_INCREMENT PRIMARY KEY,
            jti VARCHAR(64) NOT NULL UNIQUE,
            expira DATETIME NOT NULL,
            fecha_revocacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''', commit=True)

    ejecutar('''
        CREATE TABLE IF NOT EXISTS auditoria_estudiantes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            estudiante_id INT NOT NULL,
            accion VARCHAR(10) NOT NULL,
            detalle VARCHAR(255),
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''', commit=True)

    # Limpiar tokens revocados que ya expiraron
    ejecutar("DELETE FROM tokens_revocados WHERE expira < UTC_TIMESTAMP()", commit=True)

    # Crear el administrador si no existe
    admin = ejecutar("SELECT id FROM usuarios WHERE username = %s",
                     (AdminConfig.USERNAME,), fetch='one')
    if admin is None:
        ejecutar(
            "INSERT INTO usuarios (username, email, password_hash, rol) VALUES (%s, %s, %s, 'admin')",
            (AdminConfig.USERNAME, AdminConfig.EMAIL, hash_password(AdminConfig.PASSWORD)),
            commit=True)
