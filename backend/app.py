from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from routes.auth import auth_bp
from routes.estudiantes import estudiantes_bp
from models import init_db

app = Flask(__name__)
CORS(app)  # Permite peticiones desde el frontend (incluye el header Authorization)

app.register_blueprint(auth_bp)
app.register_blueprint(estudiantes_bp)


@app.route('/')
def index():
    return jsonify({'mensaje': 'API de Estudiantes v2 - Universidad Libre'}), 200


# Respuestas de error siempre en JSON
@app.errorhandler(ConnectionError)
def error_conexion(e):
    return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500


@app.errorhandler(Exception)
def error_general(e):
    if isinstance(e, HTTPException):
        return jsonify({'error': e.description}), e.code
    print(f'Error interno: {e}')
    return jsonify({'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    print('Inicializando base de datos...')
    try:
        init_db()
        print('Tablas creadas/verificadas')
    except Exception as e:
        print(f'No se pudo inicializar la base de datos: {e}')
        print('Revisa que MySQL esté encendido y que config.py tenga el puerto y la contraseña correctos.')
        raise SystemExit(1)

    print('Servidor iniciado en http://localhost:5000')
    app.run(debug=True, use_reloader=False, port=5000)
