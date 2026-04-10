from models import db
from datetime import date, timedelta


class Prestamo(db.Model):
    """Ciclo de vida de un préstamo bibliográfico."""
    __tablename__ = 'prestamo'

    id                = db.Column(db.Integer, primary_key=True)
    usuario_id        = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    libro_id          = db.Column(db.Integer, db.ForeignKey('libro.id'),   nullable=False)
    fecha_prestamo    = db.Column(db.Date, default=date.today, nullable=False)
    fecha_limite      = db.Column(db.Date, nullable=False)
    fecha_devolucion  = db.Column(db.Date, nullable=True)
    estado            = db.Column(db.String(20), default='Activo', nullable=False)

    usuario = db.relationship('Usuario', back_populates='prestamos')
    libro   = db.relationship('Libro',   back_populates='prestamos')

    def esta_vencido(self):
        return self.estado == 'Activo' and date.today() > self.fecha_limite

    def dias_restantes(self):
        return (self.fecha_limite - date.today()).days

    def registrar_devolucion(self):
        self.fecha_devolucion = date.today()
        self.estado = 'Devuelto'
        self.libro.aumentar_disponibilidad()
        db.session.commit()

    @staticmethod
    def registrar_prestamo(usuario, libro):
        if not usuario.activo:
            return None, 'El usuario no está activo.'
        if not libro.esta_disponible():
            return None, 'No hay ejemplares disponibles.'
        prestamo = Prestamo(
            usuario_id    = usuario.id,
            libro_id      = libro.id,
            fecha_prestamo = date.today(),
            fecha_limite  = date.today() + timedelta(days=14),
            estado        = 'Activo'
        )
        libro.reducir_disponibilidad()
        db.session.add(prestamo)
        db.session.commit()
        return prestamo, None

    @staticmethod
    def listar_activos():
        return Prestamo.query.filter_by(estado='Activo').order_by(Prestamo.fecha_limite).all()

    @staticmethod
    def historial_usuario(usuario_id):
        return Prestamo.query.filter_by(usuario_id=usuario_id).order_by(Prestamo.fecha_prestamo.desc()).all()

    @staticmethod
    def historial_libro(libro_id):
        return Prestamo.query.filter_by(libro_id=libro_id).order_by(Prestamo.fecha_prestamo.desc()).all()

    @staticmethod
    def buscar_por_id(pid):
        return Prestamo.query.get_or_404(pid)

    def __repr__(self):
        return f'<Prestamo {self.id} [{self.estado}]>'
