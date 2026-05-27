from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime


# --------------------------------------------------------------------------- #
#  Admin users (clinic assistants)
# --------------------------------------------------------------------------- #
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    full_name  = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------------------------------------------------------------------------- #
#  Guardians / Parents
# --------------------------------------------------------------------------- #
class Guardian(db.Model):
    __tablename__ = 'guardians'

    id           = db.Column(db.Integer, primary_key=True)
    first_name   = db.Column(db.String(80),  nullable=False)
    last_name    = db.Column(db.String(80),  nullable=False)
    relationship = db.Column(db.String(50),  nullable=False)
    phone        = db.Column(db.String(20),  nullable=False)
    email        = db.Column(db.String(120), nullable=True)
    address      = db.Column(db.String(255), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # One guardian can have many appointments
    appointments = db.relationship('Appointment', backref='guardian', lazy=True)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Guardian {self.full_name}>'


# --------------------------------------------------------------------------- #
#  Appointments
# --------------------------------------------------------------------------- #
class Appointment(db.Model):
    __tablename__ = 'appointments'

    # Status constants
    STATUS_PENDING      = 'pending'
    STATUS_APPROVED     = 'approved'
    STATUS_RESCHEDULED  = 'rescheduled'
    STATUS_CANCELLED    = 'cancelled'
    STATUS_COMPLETED    = 'completed'

    id                = db.Column(db.Integer, primary_key=True)
    reference_number  = db.Column(db.String(20), unique=True, nullable=False)

    # Foreign key to guardian
    guardian_id       = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)

    # Child details
    child_first_name  = db.Column(db.String(80),  nullable=False)
    child_last_name   = db.Column(db.String(80),  nullable=False)
    child_dob         = db.Column(db.Date,         nullable=False)
    child_sex         = db.Column(db.String(10),   nullable=False)

    # Visit details
    reason            = db.Column(db.String(120),  nullable=False)
    notes             = db.Column(db.Text,         nullable=True)
    visit_type        = db.Column(db.String(50),   nullable=False)  # In-person / Teleconsultation

    # Scheduling
    preferred_date    = db.Column(db.Date,         nullable=False)
    preferred_time    = db.Column(db.String(50),   nullable=False)
    alt_date          = db.Column(db.Date,         nullable=True)
    confirmed_date    = db.Column(db.Date,         nullable=True)   # Set by admin on approval
    confirmed_time    = db.Column(db.String(50),   nullable=True)   # Set by admin on approval

    # Status tracking
    status            = db.Column(db.String(20),   nullable=False, default='pending')
    admin_notes       = db.Column(db.Text,         nullable=True)   # Notes from the assistant
    reviewed_by       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at       = db.Column(db.DateTime,     nullable=True)
    created_at        = db.Column(db.DateTime,     default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime,     default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def child_full_name(self):
        return f'{self.child_first_name} {self.child_last_name}'

    @property
    def status_badge(self):
        """Returns a CSS class name for the status badge."""
        return {
            'pending':     'badge-pending',
            'approved':    'badge-approved',
            'rescheduled': 'badge-rescheduled',
            'cancelled':   'badge-cancelled',
            'completed':   'badge-completed',
        }.get(self.status, 'badge-pending')

    def __repr__(self):
        return f'<Appointment {self.reference_number} [{self.status}]>'