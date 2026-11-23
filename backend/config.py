import mysql.connector
from mysql.connector import Error
from datetime import timedelta


class DatabaseConfig:
    # IMPORTANTE: cambia estos datos por los de TU MySQL
    HOST = 'localhost'
    PORT = 3307            # Puerto de MySQL (3306 por defecto; en este XAMPP es 3307)
    USER = 'root'
    PASSWORD = ''          # Contraseña de MySQL (vacía si no tiene, como en XAMPP)
    DATABASE = 'universidad_db'

    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(
                host=DatabaseConfig.HOST,
                port=DatabaseConfig.PORT,
                user=DatabaseConfig.USER,
                password=DatabaseConfig.PASSWORD,
                database=DatabaseConfig.DATABASE
            )
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
        return None


class JWTConfig:
    SECRET_KEY = 'cambia-esta-clave-por-una-frase-larga-y-secreta-123'
    ALGORITHM = 'HS256'
    EXPIRATION = timedelta(hours=1)   # El token dura 1 hora


class AdminConfig:
    # Usuario administrador que se crea automáticamente la primera vez
    USERNAME = 'admin'
    EMAIL = 'admin@universidad.edu'
    PASSWORD = 'admin123'
