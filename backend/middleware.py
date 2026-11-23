import uuid
from datetime import datetime, timezone
from functools import wraps

import jwt
from flask import request, jsonify, g

from config import JWTConfig
from models import ejecutar


def generar_token(usuario):
    """Crea un token JWT que expira en 1 hora."""
    ahora = datetime.now(timezone.utc)
    payload = {
        'usuario_id': usuario['id'],
        'username': usuario['username'],
        'rol': usuario['rol'],
        'iat': ahora,
        'exp': ahora + JWTConfig.EXPIRATION,
        'jti': str(uuid.uuid4()),       # identificador único (para la blacklist)
    }
    return jwt.encode(payload, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)


def token_required(f):
    """Protege una ruta: exige un token válido, vigente y no revocado."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        partes = request.headers.get('Authorization', '').split()
        if len(partes) != 2 or partes[0].lower() != 'bearer':
            return jsonify({'error': 'Token de autenticación requerido'}), 401

        try:
            payload = jwt.decode(partes[1], JWTConfig.SECRET_KEY,
                                 algorithms=[JWTConfig.ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'El token ha expirado, inicia sesión de nuevo'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        revocado = ejecutar("SELECT id FROM tokens_revocados WHERE jti = %s",
                            (payload.get('jti'),), fetch='one')
        if revocado:
            return jsonify({'error': 'El token fue revocado (sesión cerrada)'}), 401

        g.usuario = payload
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Protege una ruta: además del token, exige rol admin."""
    @wraps(f)
    @token_required
    def wrapper(*args, **kwargs):
        if g.usuario.get('rol') != 'admin':
            return jsonify({'error': 'Acceso denegado: se requiere rol administrador'}), 403
        return f(*args, **kwargs)
    return wrapper
