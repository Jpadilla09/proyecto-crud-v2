# Sistema de Gestión de Estudiantes – Versión 2

Universidad Libre Seccional Pereira – Programación II, Sistemas Distribuidos.
**Frontend (HTML/CSS/JS) → API REST (Flask) → Persistencia (MySQL)**

## Funcionalidades
- Registro e inicio de sesión con **JWT** (el token expira en 1 hora) y contraseñas con **bcrypt**.
- **Logout real**: el token se guarda en una lista de revocados (blacklist).
- **Roles**: `admin` (CRUD completo) y `usuario` (solo lectura).
- **Validaciones** en frontend y backend (regex, email único, edad 15–100, longitudes) con mensajes por campo.
- **Paginación** del lado del servidor, **búsqueda en tiempo real** y **ordenamiento** ASC/DESC.
- **Estadísticas** (total, edad promedio/mínima/máxima, carreras principales).
- Notificaciones tipo *toast* y diseño responsive.
- Base de datos con índices, **triggers de auditoría** y **vistas** de estadísticas.

## Estructura
```
proyecto-crud-v2/
├── backend/
│   ├── app.py                 # Aplicación Flask
│   ├── config.py              # BD (host, puerto, usuario) y JWT
│   ├── models.py              # Validaciones, bcrypt, acceso a BD, init_db
│   ├── middleware.py          # token_required / admin_required
│   ├── routes/auth.py         # register, login, logout, me
│   ├── routes/estudiantes.py  # CRUD + paginación + estadísticas
│   ├── requirements.txt
│   └── universidad_db.sql     # Tablas, triggers, vistas y datos de ejemplo
├── evidencias/                # Capturas de las pruebas
└── frontend/
    ├── index.html
    ├── css/styles.css
    └── js/app.js
```

## Cómo ejecutarlo
1. Iniciar MySQL (XAMPP) y ejecutar `backend/universidad_db.sql` en phpMyAdmin (pestaña SQL).
   **Ojo:** el script borra y recrea las tablas.
   Si lo importas por consola de Windows usa `--default-character-set=utf8mb4` para que las tildes no se dañen.
2. Revisar `backend/config.py`: `PORT` (3306 por defecto; 3307 en mi equipo), `USER` y `PASSWORD`.
3. En `backend/`:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
4. En `frontend/`:
   ```
   python -m http.server 8000
   ```
   y abrir http://localhost:8000
5. Usuario administrador de prueba: **admin / admin123** (se crea automáticamente al iniciar el backend).

## Endpoints
| Método | Ruta | Acceso | Descripción |
|--------|------|--------|-------------|
| POST | /api/auth/register | público | Crear cuenta (rol usuario) |
| POST | /api/auth/login | público | Devuelve el token JWT |
| POST | /api/auth/logout | token | Revoca el token |
| GET | /api/auth/me | token | Datos del usuario actual |
| GET | /api/estudiantes?page=&per_page=&search=&sort_by=&order= | token | Lista paginada |
| GET | /api/estudiantes/estadisticas | token | Estadísticas |
| GET | /api/estudiantes/<id> | token | Un estudiante |
| POST | /api/estudiantes | admin | Crear |
| PUT | /api/estudiantes/<id> | admin | Actualizar |
| DELETE | /api/estudiantes/<id> | admin | Eliminar |

## Seguridad
- Consultas SQL parametrizadas (sin inyección SQL) y columnas de orden en lista blanca.
- El frontend escribe los datos con `textContent` (sin inyección de HTML).
- **Antes de usarlo en producción** cambia `SECRET_KEY` en `config.py`.

## Evidencias de las pruebas
| Archivo | Qué muestra |
|---------|-------------|
| 01_admin_dashboard.png | Inicio de sesión como admin, estadísticas, formulario y tabla paginada |
| 02_crear_estudiante.png | Estudiante creado (el contador pasa de 8 a 9) |
| 03_validaciones_campos.png | Validación en vivo: campos en rojo con su mensaje |
| 04_validaciones_aviso.png | Aviso "Corrige los campos marcados en rojo" al intentar guardar |
| 05_editar_estudiante.png | Aviso de actualización exitosa y dato modificado |
| 06_eliminar_estudiante.png | Aviso de eliminación exitosa (el contador baja a 8) |
| 07_busqueda.png | Búsqueda en tiempo real ("derecho") |
| 08_orden_y_paginacion.png | Orden por edad descendente y 10 filas por página |
| 09_registro_usuario.png | Registro de una cuenta nueva |
| 10_rol_usuario_solo_lectura.png | Rol `usuario`: sin formulario ni botones de editar/eliminar |
