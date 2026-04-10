from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.usuario import Usuario
from models.autor import Autor
from models.libro import Libro
from models.prestamo import Prestamo
from datetime import datetime
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

EMAIL_RE = re.compile(r'^[^@]+@[^@]+\.[^@]+$')


# ── Decorador de acceso admin ────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            flash('Acceso restringido a administradores.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'libros':    Libro.query.count(),
        'usuarios':  Usuario.query.filter_by(activo=True).count(),
        'activos':   Prestamo.query.filter_by(estado='Activo').count(),
        'autores':   Autor.query.count(),
        'vencidos':  len([p for p in Prestamo.listar_activos() if p.esta_vencido()]),
    }
    prestamos_recientes = Prestamo.query.order_by(Prestamo.fecha_prestamo.desc()).limit(5).all()
    prestamos_vencidos  = [p for p in Prestamo.listar_activos() if p.esta_vencido()]
    return render_template('admin/dashboard.html',
                           stats=stats,
                           prestamos_recientes=prestamos_recientes,
                           prestamos_vencidos=prestamos_vencidos)


# ══════════════════════════════════════════════════════════
# USUARIOS
# ══════════════════════════════════════════════════════════
@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    lista = Usuario.listar_todos()
    return render_template('admin/usuarios.html', usuarios=lista)


@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_usuario():
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        dni      = request.form.get('dni', '').strip()
        password = request.form.get('password', '').strip()
        rol      = request.form.get('rol', 'usuario')

        if not all([nombre, username, email, password]):
            flash('Nombre, usuario, email y contraseña son obligatorios.', 'error')
            return render_template('admin/form_usuario.html', usuario=None)
        if not EMAIL_RE.match(email):
            flash('Formato de email inválido.', 'error')
            return render_template('admin/form_usuario.html', usuario=None)
        if Usuario.buscar_por_username(username):
            flash(f'El nombre de usuario "{username}" ya existe.', 'error')
            return render_template('admin/form_usuario.html', usuario=None)
        if Usuario.buscar_por_email(email):
            flash(f'El email "{email}" ya está registrado.', 'error')
            return render_template('admin/form_usuario.html', usuario=None)

        u = Usuario(nombre=nombre, username=username, email=email, dni=dni or None, rol=rol)
        u.set_password(password)
        u.guardar()
        flash(f'Usuario "{username}" creado exitosamente.', 'success')
        return redirect(url_for('admin.usuarios'))

    return render_template('admin/form_usuario.html', usuario=None)


@admin_bp.route('/usuarios/<int:uid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(uid):
    u = Usuario.buscar_por_id(uid)
    if u.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'error')
        return redirect(url_for('admin.usuarios'))
    u.activo = not u.activo
    db.session.commit()
    estado = 'activado' if u.activo else 'desactivado'
    flash(f'Usuario "{u.username}" {estado}.', 'success')
    return redirect(url_for('admin.usuarios'))


# ══════════════════════════════════════════════════════════
# AUTORES
# ══════════════════════════════════════════════════════════
@admin_bp.route('/autores')
@login_required
@admin_required
def autores():
    lista = Autor.listar_todos()
    return render_template('admin/autores.html', autores=lista)


@admin_bp.route('/autores/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_autor():
    if request.method == 'POST':
        nombre       = request.form.get('nombre', '').strip()
        nacionalidad = request.form.get('nacionalidad', '').strip()
        fecha_str    = request.form.get('fecha_nac', '').strip()

        if not nombre:
            flash('El nombre es obligatorio.', 'error')
            return render_template('admin/form_autor.html', autor=None)
        if Autor.existe_por_nombre(nombre):
            flash(f'Ya existe un autor con el nombre "{nombre}".', 'error')
            return render_template('admin/form_autor.html', autor=None)

        fecha_nac = None
        if fecha_str:
            try:
                fecha_nac = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido.', 'error')
                return render_template('admin/form_autor.html', autor=None)

        a = Autor(nombre=nombre, nacionalidad=nacionalidad or None, fecha_nac=fecha_nac)
        a.guardar()
        flash(f'Autor "{nombre}" registrado.', 'success')
        return redirect(url_for('admin.autores'))

    return render_template('admin/form_autor.html', autor=None)


@admin_bp.route('/autores/<int:aid>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_autor(aid):
    autor = Autor.buscar_por_id(aid)
    if request.method == 'POST':
        nombre       = request.form.get('nombre', '').strip()
        nacionalidad = request.form.get('nacionalidad', '').strip()
        fecha_str    = request.form.get('fecha_nac', '').strip()

        if not nombre:
            flash('El nombre es obligatorio.', 'error')
            return render_template('admin/form_autor.html', autor=autor)

        existente = Autor.existe_por_nombre(nombre)
        if existente and existente.id != aid:
            flash(f'Ya existe otro autor con ese nombre.', 'error')
            return render_template('admin/form_autor.html', autor=autor)

        autor.nombre = nombre
        autor.nacionalidad = nacionalidad or None
        if fecha_str:
            try:
                autor.fecha_nac = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido.', 'error')
                return render_template('admin/form_autor.html', autor=autor)
        db.session.commit()
        flash(f'Autor actualizado.', 'success')
        return redirect(url_for('admin.autores'))

    return render_template('admin/form_autor.html', autor=autor)


@admin_bp.route('/autores/<int:aid>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_autor(aid):
    autor = Autor.buscar_por_id(aid)
    if autor.libros:
        flash('No se puede eliminar un autor con libros asociados.', 'error')
        return redirect(url_for('admin.autores'))
    nombre = autor.nombre
    autor.eliminar()
    flash(f'Autor "{nombre}" eliminado.', 'success')
    return redirect(url_for('admin.autores'))


# ══════════════════════════════════════════════════════════
# LIBROS
# ══════════════════════════════════════════════════════════
@admin_bp.route('/libros')
@login_required
@admin_required
def libros():
    termino = request.args.get('q', '').strip()
    lista   = Libro.buscar(termino) if termino else Libro.listar_todos()
    return render_template('admin/libros.html', libros=lista, termino=termino)


@admin_bp.route('/libros/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_libro():
    autores = Autor.listar_todos()
    if request.method == 'POST':
        isbn        = request.form.get('isbn', '').strip()
        titulo      = request.form.get('titulo', '').strip()
        anio        = request.form.get('anio_pub', '').strip()
        genero      = request.form.get('genero', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        ejemplares  = request.form.get('ejemplares_total', '1').strip()
        autores_ids = request.form.getlist('autores_ids')

        if not isbn or not titulo:
            flash('ISBN y título son obligatorios.', 'error')
            return render_template('admin/form_libro.html', libro=None, autores=autores)
        if len(isbn) != 13 or not isbn.isdigit():
            flash('El ISBN debe tener exactamente 13 dígitos.', 'error')
            return render_template('admin/form_libro.html', libro=None, autores=autores)
        if Libro.buscar_por_isbn(isbn):
            flash(f'Ya existe un libro con ISBN {isbn}.', 'error')
            return render_template('admin/form_libro.html', libro=None, autores=autores)
        try:
            ej = int(ejemplares)
            if ej < 1: raise ValueError
        except ValueError:
            flash('Los ejemplares deben ser un número mayor a 0.', 'error')
            return render_template('admin/form_libro.html', libro=None, autores=autores)

        libro = Libro(
            isbn=isbn, titulo=titulo,
            anio_pub=int(anio) if anio else None,
            genero=genero or None,
            descripcion=descripcion or None,
            ejemplares_total=ej, ejemplares_disponibles=ej
        )
        for aid in autores_ids:
            a = Autor.query.get(int(aid))
            if a: libro.autores.append(a)
        libro.guardar()
        flash(f'Libro "{titulo}" registrado.', 'success')
        return redirect(url_for('admin.libros'))

    return render_template('admin/form_libro.html', libro=None, autores=autores)


@admin_bp.route('/libros/<int:lid>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_libro(lid):
    libro   = Libro.buscar_por_id(lid)
    autores = Autor.listar_todos()
    if request.method == 'POST':
        titulo      = request.form.get('titulo', '').strip()
        genero      = request.form.get('genero', '').strip()
        anio        = request.form.get('anio_pub', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        autores_ids = request.form.getlist('autores_ids')

        if not titulo:
            flash('El título es obligatorio.', 'error')
            return render_template('admin/form_libro.html', libro=libro, autores=autores)

        libro.titulo      = titulo
        libro.genero      = genero or None
        libro.anio_pub    = int(anio) if anio else None
        libro.descripcion = descripcion or None

        # Actualizar ejemplares totales y ajustar disponibles proporcionalmente
        nuevos_total = request.form.get('ejemplares_total', '').strip()
        if nuevos_total.isdigit() and int(nuevos_total) >= 1:
            diferencia = int(nuevos_total) - libro.ejemplares_total
            libro.ejemplares_total = int(nuevos_total)
            libro.ejemplares_disponibles = max(0, libro.ejemplares_disponibles + diferencia)

        libro.autores     = []
        for aid in autores_ids:
            a = Autor.query.get(int(aid))
            if a: libro.autores.append(a)
        db.session.commit()
        flash('Libro actualizado.', 'success')
        return redirect(url_for('admin.libros'))

    return render_template('admin/form_libro.html', libro=libro, autores=autores)


@admin_bp.route('/libros/<int:lid>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_libro(lid):
    libro = Libro.buscar_por_id(lid)
    if libro.prestamos:
        flash('No se puede eliminar un libro con historial de préstamos.', 'error')
        return redirect(url_for('admin.libros'))
    titulo = libro.titulo
    libro.eliminar()
    flash(f'Libro "{titulo}" eliminado.', 'success')
    return redirect(url_for('admin.libros'))


# ══════════════════════════════════════════════════════════
# PRÉSTAMOS
# ══════════════════════════════════════════════════════════
@admin_bp.route('/prestamos')
@login_required
@admin_required
def prestamos():
    activos = Prestamo.listar_activos()
    return render_template('admin/prestamos.html', prestamos=activos)


@admin_bp.route('/prestamos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_prestamo():
    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.nombre).all()
    libros   = Libro.listar_todos()
    if request.method == 'POST':
        uid = request.form.get('usuario_id')
        lid = request.form.get('libro_id')
        if not uid or not lid:
            flash('Selecciona usuario y libro.', 'error')
            return render_template('admin/form_prestamo.html', usuarios=usuarios, libros=libros)
        usuario = Usuario.query.get(int(uid))
        libro   = Libro.query.get(int(lid))
        prestamo, error = Prestamo.registrar_prestamo(usuario, libro)
        if error:
            flash(error, 'error')
            return render_template('admin/form_prestamo.html', usuarios=usuarios, libros=libros)
        flash(f'Préstamo registrado. Límite: {prestamo.fecha_limite.strftime("%d/%m/%Y")}.', 'success')
        return redirect(url_for('admin.prestamos'))
    return render_template('admin/form_prestamo.html', usuarios=usuarios, libros=libros)


@admin_bp.route('/prestamos/<int:pid>/devolver', methods=['POST'])
@login_required
@admin_required
def devolver(pid):
    p = Prestamo.buscar_por_id(pid)
    if p.estado == 'Devuelto':
        flash('Este préstamo ya fue devuelto.', 'error')
        return redirect(url_for('admin.prestamos'))
    p.registrar_devolucion()
    from datetime import date
    tardio = p.fecha_devolucion > p.fecha_limite
    if tardio:
        flash(f'Devolución tardía ({(p.fecha_devolucion - p.fecha_limite).days} días de retraso).', 'warning')
    else:
        flash('Devolución registrada.', 'success')
    return redirect(url_for('admin.prestamos'))
