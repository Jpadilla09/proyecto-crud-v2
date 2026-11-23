from math import ceil

from flask import Blueprint, jsonify, request
from mysql.connector.errors import IntegrityError

from middleware import token_required, admin_required
from models import ejecutar, validar_estudiante

estudiantes_bp = Blueprint('estudiantes', __name__)

# Columnas permitidas para ordenar (lista blanca: evita inyección SQL)
ORDENABLES = ['id', 'nombre', 'apellido', 'email', 'edad', 'carrera', 'fecha_creacion']
COLUMNAS = 'id, nombre, apellido, email, edad, carrera, fecha_creacion'


def error_validacion(errores):
    return jsonify({'error': 'Datos inválidos', 'errores': errores}), 400


def error_email_duplicado():
    return jsonify({'error': 'Datos inválidos',
                    'errores': {'email': 'Ese correo ya está registrado'}}), 409


# READ - Listar con paginación, búsqueda y ordenamiento
@estudiantes_bp.route('/api/estudiantes', methods=['GET'])
@token_required
def listar_estudiantes():
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 5, type=int), 1), 50)
    search = request.args.get('search', '').strip()

    sort_by = request.args.get('sort_by', 'id')
    if sort_by not in ORDENABLES:
        sort_by = 'id'
    order = 'DESC' if request.args.get('order', 'ASC').upper() == 'DESC' else 'ASC'

    where, params = '', []
    if search:
        like = f'%{search}%'
        where = 'WHERE nombre LIKE %s OR apellido LIKE %s OR email LIKE %s OR carrera LIKE %s'
        params = [like, like, like, like]

    total = ejecutar(f'SELECT COUNT(*) AS total FROM estudiantes {where}',
                     params, fetch='one')['total']
    total_pages = max(ceil(total / per_page), 1)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    filas = ejecutar(
        f'SELECT {COLUMNAS} FROM estudiantes {where} '
        f'ORDER BY {sort_by} {order} LIMIT %s OFFSET %s',
        params + [per_page, offset], fetch='all')

    return jsonify({
        'estudiantes': filas,
        'paginacion': {
            'page': page,
            'per_page': per_page,
            'total_items': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    }), 200


# READ - Estadísticas para el dashboard
@estudiantes_bp.route('/api/estudiantes/estadisticas', methods=['GET'])
@token_required
def estadisticas():
    resumen = ejecutar(
        'SELECT COUNT(*) AS total, AVG(edad) AS promedio, MIN(edad) AS minima, '
        'MAX(edad) AS maxima FROM estudiantes', fetch='one')
    carreras = ejecutar(
        'SELECT carrera, COUNT(*) AS total FROM estudiantes '
        'GROUP BY carrera ORDER BY total DESC, carrera LIMIT 5', fetch='all')

    return jsonify({
        'total_estudiantes': resumen['total'],
        'edad_promedio': round(float(resumen['promedio']), 1) if resumen['promedio'] is not None else 0,
        'edad_minima': resumen['minima'] or 0,
        'edad_maxima': resumen['maxima'] or 0,
        'por_carrera': carreras
    }), 200


# READ - Un estudiante por ID
@estudiantes_bp.route('/api/estudiantes/<int:id>', methods=['GET'])
@token_required
def obtener_estudiante(id):
    estudiante = ejecutar(f'SELECT {COLUMNAS} FROM estudiantes WHERE id = %s',
                          (id,), fetch='one')
    if estudiante:
        return jsonify(estudiante), 200
    return jsonify({'error': 'Estudiante no encontrado'}), 404


# CREATE - Solo admin
@estudiantes_bp.route('/api/estudiantes', methods=['POST'])
@admin_required
def crear_estudiante():
    errores, datos = validar_estudiante(request.get_json(silent=True))
    if errores:
        return error_validacion(errores)

    try:
        resultado = ejecutar(
            'INSERT INTO estudiantes (nombre, apellido, email, edad, carrera) '
            'VALUES (%s, %s, %s, %s, %s)',
            (datos['nombre'], datos['apellido'], datos['email'],
             datos['edad'], datos['carrera']), commit=True)
    except IntegrityError:
        return error_email_duplicado()

    return jsonify({'mensaje': 'Estudiante creado exitosamente',
                    'id': resultado['lastrowid']}), 201


# UPDATE - Solo admin
@estudiantes_bp.route('/api/estudiantes/<int:id>', methods=['PUT'])
@admin_required
def actualizar_estudiante(id):
    errores, datos = validar_estudiante(request.get_json(silent=True))
    if errores:
        return error_validacion(errores)

    existe = ejecutar('SELECT id FROM estudiantes WHERE id = %s', (id,), fetch='one')
    if not existe:
        return jsonify({'error': 'Estudiante no encontrado'}), 404

    try:
        ejecutar(
            'UPDATE estudiantes SET nombre=%s, apellido=%s, email=%s, edad=%s, carrera=%s '
            'WHERE id=%s',
            (datos['nombre'], datos['apellido'], datos['email'],
             datos['edad'], datos['carrera'], id), commit=True)
    except IntegrityError:
        return error_email_duplicado()

    return jsonify({'mensaje': 'Estudiante actualizado exitosamente'}), 200


# DELETE - Solo admin
@estudiantes_bp.route('/api/estudiantes/<int:id>', methods=['DELETE'])
@admin_required
def eliminar_estudiante(id):
    resultado = ejecutar('DELETE FROM estudiantes WHERE id = %s', (id,), commit=True)
    if resultado['rowcount'] > 0:
        return jsonify({'mensaje': 'Estudiante eliminado exitosamente'}), 200
    return jsonify({'error': 'Estudiante no encontrado'}), 404
