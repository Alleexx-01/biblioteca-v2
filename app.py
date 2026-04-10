from flask import Flask, redirect, url_for
from config import Config
from models import db, bcrypt, login_manager


def create_app():
    """Factory que crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Inicializar extensiones ──
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # ── Registrar blueprints ──
    from controllers.auth_controller  import auth_bp
    from controllers.admin_controller import admin_bp
    from controllers.usuario_controller import usuario_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(usuario_bp)

    # ── Ruta raíz ──
    @app.route('/')
    def index():
        return redirect(url_for('auth.index'))

    # ── Error handlers ──
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('shared/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('shared/403.html'), 403

    return app


def seed_database(app):
    """Crea los usuarios de prueba si no existen."""
    with app.app_context():
        from models.usuario import Usuario

        # Admin de prueba
        if not Usuario.buscar_por_username('admin'):
            admin = Usuario(
                username = 'admin',
                email    = 'admin@biblioteca.com',
                nombre   = 'Administrador',
                rol      = 'admin'
            )
            admin.set_password('admin123')
            admin.guardar()
            print('✅ Usuario admin creado  →  admin / admin123')

        # Usuario normal de prueba
        if not Usuario.buscar_por_username('usuario'):
            user = Usuario(
                username = 'usuario',
                email    = 'usuario@biblioteca.com',
                nombre   = 'Usuario Demo',
                rol      = 'usuario'
            )
            user.set_password('usuario123')
            user.guardar()
            print('✅ Usuario demo creado   →  usuario / usuario123')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_database(app)
    print('🚀 Servidor iniciado en http://localhost:5000')
    app.run(debug=True)