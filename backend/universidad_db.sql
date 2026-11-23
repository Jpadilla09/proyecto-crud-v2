-- =====================================================================
-- Sistema de Gestión de Estudiantes - Versión 2
-- OJO: este script BORRA y vuelve a crear las tablas (deja todo limpio).
-- El usuario administrador (admin / admin123) lo crea app.py al iniciar.
-- =====================================================================
CREATE DATABASE IF NOT EXISTS universidad_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE universidad_db;

DROP TABLE IF EXISTS auditoria_estudiantes;
DROP TABLE IF EXISTS tokens_revocados;
DROP TABLE IF EXISTS estudiantes;
DROP TABLE IF EXISTS usuarios;

-- ---------- Usuarios (login y roles) ----------
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('admin','usuario') NOT NULL DEFAULT 'usuario',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Estudiantes (con índices) ----------
CREATE TABLE estudiantes (
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
);

-- ---------- Tokens revocados (blacklist del logout) ----------
CREATE TABLE tokens_revocados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jti VARCHAR(64) NOT NULL UNIQUE,
    expira DATETIME NOT NULL,
    fecha_revocacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Auditoría ----------
CREATE TABLE auditoria_estudiantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    accion VARCHAR(10) NOT NULL,
    detalle VARCHAR(255),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Triggers de auditoría ----------
CREATE TRIGGER trg_estudiantes_insert AFTER INSERT ON estudiantes
FOR EACH ROW
    INSERT INTO auditoria_estudiantes (estudiante_id, accion, detalle)
    VALUES (NEW.id, 'INSERT', CONCAT('Creado: ', NEW.nombre, ' ', NEW.apellido));

CREATE TRIGGER trg_estudiantes_update AFTER UPDATE ON estudiantes
FOR EACH ROW
    INSERT INTO auditoria_estudiantes (estudiante_id, accion, detalle)
    VALUES (NEW.id, 'UPDATE', CONCAT('Antes: ', OLD.nombre, ' ', OLD.apellido, ' | Ahora: ', NEW.nombre, ' ', NEW.apellido));

CREATE TRIGGER trg_estudiantes_delete AFTER DELETE ON estudiantes
FOR EACH ROW
    INSERT INTO auditoria_estudiantes (estudiante_id, accion, detalle)
    VALUES (OLD.id, 'DELETE', CONCAT('Eliminado: ', OLD.nombre, ' ', OLD.apellido));

-- ---------- Vistas de estadísticas ----------
CREATE OR REPLACE VIEW vista_estadisticas AS
SELECT COUNT(*) AS total_estudiantes,
       ROUND(AVG(edad), 1) AS edad_promedio,
       MIN(edad) AS edad_minima,
       MAX(edad) AS edad_maxima
FROM estudiantes;

CREATE OR REPLACE VIEW vista_estudiantes_por_carrera AS
SELECT carrera, COUNT(*) AS total
FROM estudiantes
GROUP BY carrera
ORDER BY total DESC;

-- ---------- Datos de ejemplo ----------
INSERT INTO estudiantes (nombre, apellido, email, edad, carrera) VALUES
('Juan', 'Pérez', 'juan.perez@universidad.edu', 20, 'Ingeniería de Sistemas'),
('María', 'González', 'maria.gonzalez@universidad.edu', 22, 'Ingeniería Industrial'),
('Carlos', 'Rodríguez', 'carlos.rodriguez@universidad.edu', 21, 'Ingeniería Electrónica'),
('Ana', 'Martínez', 'ana.martinez@universidad.edu', 19, 'Ingeniería de Sistemas'),
('Luis', 'Ramírez', 'luis.ramirez@universidad.edu', 23, 'Derecho'),
('Sofía', 'Torres', 'sofia.torres@universidad.edu', 20, 'Psicología'),
('Andrés', 'Vargas', 'andres.vargas@universidad.edu', 24, 'Ingeniería Industrial'),
('Laura', 'Gómez', 'laura.gomez@universidad.edu', 21, 'Medicina');
