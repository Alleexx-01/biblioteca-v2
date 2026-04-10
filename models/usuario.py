from models import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import date


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(db.Model, UserMixin):
    """
    Modelo de usuario con soporte para autenticación y roles.
    Roles disponibles: 'admin' | 'usuario'
    """
    __tablename__ = 'usuario'

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80),  unique=True, nullable=False)
    email           = db.Column(db.String(150), unique=True, nullable=False)
    dni             = db.Column(db.String(20),  unique=True, nullable=True)
    nombre          = db.Column(db.String(150), nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    rol             = db.Column(db.String(20),  nullable=False, default='usuario')  # 'admin' | 'usuario'
    activo          = db.Column(db.Boolean, default=True, nullable=False)
    fecha_registro  = db.Column(db.Date, default=date.today, nullable=False)

    # Relación con préstamos
    prestamos = db.relationship('Prestamo', back_populates='usuario', lazy=True)

    # ── Propiedades de rol ──────────────────────────────
    @property
    def es_admin(self):
        return self.rol == 'admin'

    @property
    def es_usuario(self):
        return self.rol == 'usuario'

    # ── Contraseña ──────────────────────────────────────
    def set_password(self, password):
        """Hashea y guarda la contraseña."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica si la contraseña es correcta."""
        return bcrypt.check_password_hash(self.password_hash, password)

    # ── CRUD ────────────────────────────────────────────
    def guardar(self):
        db.session.add(self)
        db.session.commit()

    def desactivar(self):
        self.activo = False
        db.session.commit()

    def prestamos_activos(self):
        return [p for p in self.prestamos if p.estado == 'Activo']

    # ── Queries estáticas ───────────────────────────────
    @staticmethod
    def listar_todos():
        return Usuario.query.order_by(Usuario.nombre).all()

    @staticmethod
    def buscar_por_username(username):
        return Usuario.query.filter_by(username=username).first()

    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_id(uid):
        return Usuario.query.get_or_404(uid)

    def __repr__(self):
        return f'<Usuario {self.username} [{self.rol}]>'
