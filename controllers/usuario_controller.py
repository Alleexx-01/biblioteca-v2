from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.libro import Libro
from models.prestamo import Prestamo

usuario_bp = Blueprint('usuario_bp', __name__, url_prefix='/catalogo')


@usuario_bp.route('/')
@login_required
def catalogo():
    """Catálogo público de libros — accesible para todos los roles."""
    termino = request.args.get('q', '').strip()
    libros  = Libro.buscar(termino) if termino else Libro.listar_todos()
    return render_template('usuario/catalogo.html', libros=libros, termino=termino)


@usuario_bp.route('/libro/<int:lid>')
@login_required
def detalle_libro(lid):
    """Detalle básico de un libro (título, autor, disponibilidad)."""
    libro = Libro.buscar_por_id(lid)
    return render_template('usuario/detalle_libro.html', libro=libro)


@usuario_bp.route('/solicitar/<int:lid>', methods=['POST'])
@login_required
def solicitar_prestamo(lid):
    """El usuario solicita un préstamo de un libro."""
    if current_user.es_admin:
        return redirect(url_for('admin.nuevo_prestamo'))

    libro = Libro.buscar_por_id(lid)
    prestamo, error = Prestamo.registrar_prestamo(current_user, libro)
    if error:
        flash(error, 'error')
    else:
        flash(f'Préstamo solicitado. Fecha límite de devolución: {prestamo.fecha_limite.strftime("%d/%m/%Y")}.', 'success')
    return redirect(url_for('usuario_bp.detalle_libro', lid=lid))


@usuario_bp.route('/mis-prestamos')
@login_required
def mis_prestamos():
    """El usuario ve su propio historial de préstamos."""
    prestamos = Prestamo.historial_usuario(current_user.id)
    return render_template('usuario/mis_prestamos.html', prestamos=prestamos)
