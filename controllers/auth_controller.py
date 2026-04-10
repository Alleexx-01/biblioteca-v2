from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.usuario import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Por favor completa todos los campos.', 'error')
            return render_template('auth/login.html')

        # Buscar por username o email
        usuario = Usuario.buscar_por_username(username) or Usuario.buscar_por_email(username)

        if not usuario or not usuario.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'error')
            return render_template('auth/login.html')

        if not usuario.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return render_template('auth/login.html')

        login_user(usuario, remember=True)

        # Redirigir según rol
        if usuario.es_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('usuario_bp.catalogo'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario."""
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirecciona al panel correcto según el rol."""
    if current_user.es_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('usuario_bp.catalogo'))


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))
