const API = 'http://localhost:5000/api';

// ---------------- Estado ----------------
let token = localStorage.getItem('token');
let usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
const estado = { page: 1, per_page: 5, search: '', sort_by: 'id', order: 'ASC' };

// ---------------- Referencias al DOM ----------------
const $ = (id) => document.getElementById(id);
const authSection = $('auth-section');
const appSection = $('app-section');
const form = $('estudiante-form');
const tbody = $('estudiantes-tbody');

// ---------------- Utilidades ----------------
function toast(mensaje, tipo = 'info') {
    const div = document.createElement('div');
    div.className = `toast toast-${tipo}`;
    div.textContent = mensaje;
    $('toast-container').appendChild(div);
    setTimeout(() => div.remove(), 3500);
}

function esAdmin() {
    return usuario && usuario.rol === 'admin';
}

// Llama a la API agregando el token. Devuelve { ok, status, data }.
async function api(ruta, opciones = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let respuesta;
    try {
        respuesta = await fetch(API + ruta, { ...opciones, headers });
    } catch (e) {
        toast('No se pudo conectar con el servidor. ¿Está encendido el backend?', 'error');
        throw e;
    }

    let data = {};
    try { data = await respuesta.json(); } catch (e) { /* respuesta sin JSON */ }

    // Token vencido o revocado: volver al login
    if (respuesta.status === 401 && token && !ruta.startsWith('/auth/login')) {
        cerrarSesionLocal();
        toast(data.error || 'Tu sesión expiró. Inicia sesión de nuevo.', 'error');
    }
    return { ok: respuesta.ok, status: respuesta.status, data };
}

// ---------------- Validaciones del lado del cliente ----------------
const RE_NOMBRE = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]{2,50}$/;
const RE_EMAIL = /^[\w.+-]+@[\w-]+(\.[\w-]+)+$/;
const RE_USERNAME = /^[A-Za-z0-9_]{3,30}$/;

const validadores = {
    nombre: (v) => RE_NOMBRE.test(v.trim()) ? '' : 'Solo letras y espacios (2 a 50 caracteres)',
    apellido: (v) => RE_NOMBRE.test(v.trim()) ? '' : 'Solo letras y espacios (2 a 50 caracteres)',
    email: (v) => RE_EMAIL.test(v.trim()) ? '' : 'Ingresa un correo electrónico válido',
    edad: (v) => {
        if (!/^\d+$/.test(String(v).trim())) return 'La edad debe ser un número entero';
        const n = parseInt(v, 10);
        return (n >= 15 && n <= 100) ? '' : 'La edad debe estar entre 15 y 100 años';
    },
    carrera: (v) => (v.trim().length >= 3 && v.trim().length <= 100) ? '' : 'La carrera debe tener entre 3 y 100 caracteres',
    username: (v) => RE_USERNAME.test(v.trim()) ? '' : 'Usuario de 3 a 30 caracteres (letras, números o _)',
    password: (v) => {
        if (v.length < 6) return 'Mínimo 6 caracteres';
        return (/[A-Za-z]/.test(v) && /\d/.test(v)) ? '' : 'Debe incluir al menos una letra y un número';
    }
};

function mostrarError(input, mensaje) {
    const small = input.parentElement.querySelector('small.error');
    if (small) small.textContent = mensaje;
    input.classList.toggle('invalid', !!mensaje);
    input.classList.toggle('valid', !mensaje && input.value !== '');
}

function validarCampo(input) {
    const mensaje = validadores[input.dataset.campo](input.value);
    mostrarError(input, mensaje);
    return !mensaje;
}

function validarFormulario(formulario) {
    let todoOk = true;
    formulario.querySelectorAll('[data-campo]').forEach((input) => {
        if (!validarCampo(input)) todoOk = false;
    });
    return todoOk;
}

// Muestra los errores que devuelve el servidor, campo por campo
function mostrarErroresServidor(formulario, errores) {
    Object.entries(errores || {}).forEach(([campo, mensaje]) => {
        const input = formulario.querySelector(`[data-campo="${campo}"]`);
        if (input) mostrarError(input, mensaje);
    });
}

function activarValidacionEnVivo(formulario) {
    formulario.querySelectorAll('[data-campo]').forEach((input) => {
        input.addEventListener('input', () => validarCampo(input));
    });
}

// ---------------- Autenticación ----------------
function cambiarTab(login) {
    $('tab-login').classList.toggle('active', login);
    $('tab-register').classList.toggle('active', !login);
    $('login-form').hidden = !login;
    $('register-form').hidden = login;
}

$('tab-login').addEventListener('click', () => cambiarTab(true));
$('tab-register').addEventListener('click', () => cambiarTab(false));
activarValidacionEnVivo($('register-form'));

$('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = $('login-username').value.trim();
    const password = $('login-password').value;
    if (!username || !password) {
        toast('Escribe tu usuario y contraseña', 'error');
        return;
    }
    const { ok, data } = await api('/auth/login', {
        method: 'POST', body: JSON.stringify({ username, password })
    });
    if (!ok) {
        toast(data.error || 'No se pudo iniciar sesión', 'error');
        return;
    }
    token = data.token;
    usuario = data.usuario;
    localStorage.setItem('token', token);
    localStorage.setItem('usuario', JSON.stringify(usuario));
    $('login-form').reset();
    toast(`¡Bienvenido, ${usuario.username}!`, 'success');
    mostrarApp();
});

$('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = $('register-form');
    if (!validarFormulario(f)) {
        toast('Corrige los campos marcados en rojo', 'error');
        return;
    }
    const cuerpo = {
        username: $('reg-username').value.trim(),
        email: $('reg-email').value.trim(),
        password: $('reg-password').value
    };
    const { ok, data } = await api('/auth/register', { method: 'POST', body: JSON.stringify(cuerpo) });
    if (!ok) {
        mostrarErroresServidor(f, data.errores);
        toast(data.error || 'No se pudo registrar', 'error');
        return;
    }
    toast('Cuenta creada. Ahora inicia sesión.', 'success');
    f.reset();
    f.querySelectorAll('input').forEach((i) => mostrarError(i, ''));
    cambiarTab(true);
    $('login-username').value = cuerpo.username;
    $('login-password').focus();
});

function cerrarSesionLocal() {
    token = null;
    usuario = null;
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    appSection.hidden = true;
    authSection.hidden = false;
}

$('logout-btn').addEventListener('click', async () => {
    await api('/auth/logout', { method: 'POST' }).catch(() => {});
    cerrarSesionLocal();
    toast('Sesión cerrada', 'info');
});

// ---------------- Pantalla principal ----------------
function mostrarApp() {
    authSection.hidden = true;
    appSection.hidden = false;

    const rol = usuario.rol;
    $('user-info').innerHTML = '';
    $('user-info').append(`${usuario.username} `);
    const badge = document.createElement('span');
    badge.className = `badge badge-${rol}`;
    badge.textContent = rol;
    $('user-info').appendChild(badge);

    // Solo el admin ve el formulario y las acciones
    $('form-container').hidden = !esAdmin();
    $('th-acciones').hidden = !esAdmin();

    limpiarFormulario();
    cargarEstadisticas();
    cargarEstudiantes();
}

async function cargarEstadisticas() {
    const { ok, data } = await api('/estudiantes/estadisticas');
    if (!ok) return;
    $('stat-total').textContent = data.total_estudiantes;
    $('stat-promedio').textContent = data.edad_promedio;
    $('stat-min').textContent = data.edad_minima;
    $('stat-max').textContent = data.edad_maxima;

    const lista = $('stat-carreras');
    lista.innerHTML = '';
    data.por_carrera.forEach((c) => {
        const li = document.createElement('li');
        li.textContent = `${c.carrera}: ${c.total}`;
        lista.appendChild(li);
    });
}

// ---------------- Lista, búsqueda, orden y paginación ----------------
function celda(texto) {
    const td = document.createElement('td');
    td.textContent = texto;   // textContent evita inyección de HTML
    return td;
}

async function cargarEstudiantes() {
    const params = new URLSearchParams(estado);
    const { ok, data } = await api(`/estudiantes?${params.toString()}`);
    if (!ok) {
        if (token) toast(data.error || 'Error al cargar los estudiantes', 'error');
        return;
    }

    tbody.innerHTML = '';
    if (data.estudiantes.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = esAdmin() ? 7 : 6;
        td.className = 'empty';
        td.textContent = 'No se encontraron estudiantes';
        tr.appendChild(td);
        tbody.appendChild(tr);
    }

    data.estudiantes.forEach((est) => {
        const tr = document.createElement('tr');
        [est.id, est.nombre, est.apellido, est.email, est.edad, est.carrera]
            .forEach((valor) => tr.appendChild(celda(valor)));

        if (esAdmin()) {
            const td = document.createElement('td');
            const editar = document.createElement('button');
            editar.className = 'btn-editar';
            editar.textContent = 'Editar';
            editar.dataset.accion = 'editar';
            editar.dataset.id = est.id;
            const borrar = document.createElement('button');
            borrar.className = 'btn-eliminar';
            borrar.textContent = 'Eliminar';
            borrar.dataset.accion = 'eliminar';
            borrar.dataset.id = est.id;
            td.append(editar, borrar);
            tr.appendChild(td);
        }
        tbody.appendChild(tr);
    });

    dibujarPaginacion(data.paginacion);
}

function dibujarPaginacion(p) {
    estado.page = p.page;
    const desde = p.total_items === 0 ? 0 : (p.page - 1) * p.per_page + 1;
    const hasta = Math.min(p.page * p.per_page, p.total_items);
    $('page-info').textContent =
        `Mostrando ${desde}-${hasta} de ${p.total_items} (página ${p.page} de ${p.total_pages})`;

    const cont = $('pagination');
    cont.innerHTML = '';

    const boton = (texto, pagina, { activo = false, deshabilitado = false } = {}) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = texto;
        b.disabled = deshabilitado;
        if (activo) b.classList.add('active');
        b.addEventListener('click', () => { estado.page = pagina; cargarEstudiantes(); });
        cont.appendChild(b);
    };

    boton('« Anterior', p.page - 1, { deshabilitado: !p.has_prev });
    const inicio = Math.max(1, p.page - 2);
    const fin = Math.min(p.total_pages, p.page + 2);
    for (let i = inicio; i <= fin; i++) boton(String(i), i, { activo: i === p.page });
    boton('Siguiente »', p.page + 1, { deshabilitado: !p.has_next });
}

// Búsqueda en tiempo real (espera 400 ms después de la última tecla)
let temporizador;
$('search-input').addEventListener('input', (e) => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => {
        estado.search = e.target.value.trim();
        estado.page = 1;
        cargarEstudiantes();
    }, 400);
});

$('sort-by').addEventListener('change', (e) => { estado.sort_by = e.target.value; estado.page = 1; cargarEstudiantes(); });
$('sort-order').addEventListener('change', (e) => { estado.order = e.target.value; estado.page = 1; cargarEstudiantes(); });
$('per-page').addEventListener('change', (e) => { estado.per_page = parseInt(e.target.value, 10); estado.page = 1; cargarEstudiantes(); });

// ---------------- Crear / Actualizar ----------------
activarValidacionEnVivo(form);

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validarFormulario(form)) {
        toast('Corrige los campos marcados en rojo', 'error');
        return;
    }

    const id = $('estudiante-id').value;
    const estudiante = {
        nombre: $('nombre').value.trim(),
        apellido: $('apellido').value.trim(),
        email: $('email').value.trim(),
        edad: parseInt($('edad').value, 10),
        carrera: $('carrera').value.trim()
    };

    const { ok, data } = await api(id ? `/estudiantes/${id}` : '/estudiantes', {
        method: id ? 'PUT' : 'POST',
        body: JSON.stringify(estudiante)
    });

    if (!ok) {
        mostrarErroresServidor(form, data.errores);
        toast(data.error || 'Error al guardar el estudiante', 'error');
        return;
    }
    toast(data.mensaje, 'success');
    limpiarFormulario();
    cargarEstudiantes();
    cargarEstadisticas();
});

// Botones Editar / Eliminar (delegación de eventos sobre la tabla)
tbody.addEventListener('click', (e) => {
    const boton = e.target.closest('button[data-accion]');
    if (!boton) return;
    const id = boton.dataset.id;
    if (boton.dataset.accion === 'editar') editarEstudiante(id);
    else eliminarEstudiante(id);
});

async function editarEstudiante(id) {
    const { ok, data } = await api(`/estudiantes/${id}`);
    if (!ok) {
        toast(data.error || 'No se pudo cargar el estudiante', 'error');
        return;
    }
    $('estudiante-id').value = data.id;
    $('nombre').value = data.nombre;
    $('apellido').value = data.apellido;
    $('email').value = data.email;
    $('edad').value = data.edad;
    $('carrera').value = data.carrera;
    form.querySelectorAll('[data-campo]').forEach((i) => mostrarError(i, ''));

    $('form-title').textContent = 'Editar Estudiante';
    $('submit-btn').textContent = 'Actualizar Estudiante';
    $('cancel-btn').hidden = false;
    form.scrollIntoView({ behavior: 'smooth' });
}

async function eliminarEstudiante(id) {
    if (!confirm('¿Estás seguro de eliminar este estudiante?')) return;
    const { ok, data } = await api(`/estudiantes/${id}`, { method: 'DELETE' });
    if (!ok) {
        toast(data.error || 'Error al eliminar el estudiante', 'error');
        return;
    }
    toast(data.mensaje, 'success');
    cargarEstudiantes();
    cargarEstadisticas();
}

function limpiarFormulario() {
    form.reset();
    $('estudiante-id').value = '';
    form.querySelectorAll('[data-campo]').forEach((i) => {
        mostrarError(i, '');
        i.classList.remove('valid');
    });
    $('form-title').textContent = 'Agregar Nuevo Estudiante';
    $('submit-btn').textContent = 'Agregar Estudiante';
    $('cancel-btn').hidden = true;
}
$('cancel-btn').addEventListener('click', limpiarFormulario);

// ---------------- Inicio: ¿ya había una sesión? ----------------
(async function iniciar() {
    if (token && usuario) {
        const { ok } = await api('/auth/me');
        if (ok) { mostrarApp(); return; }
        cerrarSesionLocal();
    }
})();
