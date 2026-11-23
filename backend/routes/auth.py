from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g
from mysql.connector.errors import IntegrityError

from config import JWTConfig
from middleware import generar_token, token_required
from models import ejecutar, hash_password, verificar_password, validar_registro

auth_bp = Blueprint('auth', __name__)


# REGISTRO
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    errores, datos = validar_registro(request.get_json(silent=True))
    if errores:
        return jsonify({'error': 'Datos inválidos', 'errores': errores}), 400

    try:
        resultado = ejecutar(
            "INSERT INTO usuarios (username, email, password_hash, rol) VALUES (%s, %s, %s, 'usuario')",
            (datos['username'], datos['email'], hash_password(datos['password'])),
            commit=True)
    except IntegrityError as e:
        campo = 'email' if 'email' in str(e) else 'username'
        mensaje = ('Ese correo ya está registrado' if campo == 'email'
                   else 'Ese nombre de usuario ya existe')
        return jsonify({'error': 'Datos inválidos', 'errores': {campo: mensaje}}), 409

    return jsonify({'mensaje': 'Usuario registrado exitosamente',
                    'id': resultado['lastrowid']}), 201


# LOGIN
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get('username') or '').strip()
    password = str(data.get('password') or '')

    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son obligatorios'}), 400

    usuario = ejecutar("SELECT * FROM usuarios WHERE username = %s",
                       (username,), fetch='one')

    if not usuario or not verificar_password(password, usuario['password_hash']):
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401
    if not usuario['activo']:
        return jsonify({'error': 'La cuenta está desactivada'}), 403

    token = generar_token(usuario)
    return jsonify({
        'mensaje': 'Inicio de sesión exitoso',
        'token': token,
        'expira_en': int(JWTConfig.EXPIRATION.total_seconds()),
        'usuario': {'id': usuario['id'], 'username': usuario['username'],
                    'email': usuario['email'], 'rol': usuario['rol']}
    }), 200


# LOGOUT (revoca el token: lo mete a la blacklist)
@auth_bp.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    expira = datetime.fromtimestamp(g.usuario['exp'], timezone.utc).replace(tzinfo=None)
    ejecutar("INSERT IGNORE INTO tokens_revocados (jti, expira) VALUES (%s, %s)",
             (g.usuario['jti'], expira), commit=True)
    return jsonify({'mensaje': 'Sesión cerrada exitosamente'}), 200


# DATOS DEL USUARIO ACTUAL
@auth_bp.route('/api/auth/me', methods=['GET'])
@token_required
def me():
    return jsonify({'usuario': {'id': g.usuario['usuario_id'],
                                'username': g.usuario['username'],
                                'rol': g.usuario['rol']}}), 200
