from flask import Blueprint, request, jsonify, render_template, current_app
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import random
import string
import re

from extensions import db
from models import Guardian, Appointment
from email_service import send_email, email_appointment_received

client_bp = Blueprint('client', __name__)


def generate_reference() -> str:
    while True:
        ref = 'APT-' + ''.join(random.choices(string.digits, k=5))
        if not Appointment.query.filter_by(reference_number=ref).first():
            return ref


def parse_date(date_str: str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def is_valid_name(name: str) -> bool:
    """Allow letters, spaces, hyphens, apostrophes only."""
    return bool(re.match(r"^[A-Za-z\s'\-\.]{2,80}$", name.strip()))


def is_valid_email(email: str) -> bool:
    """Basic email format check."""
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()))


def is_weekday(d: date) -> bool:
    """Return True if date is Monday–Friday (weekday < 5)."""
    return d.weekday() < 5


@client_bp.route('/')
def index():
    return render_template('form.html')


@client_bp.route('/submit-appointment', methods=['POST'])
def submit_appointment():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request.'}), 400

    guardian_data = data.get('guardian', {})
    child_data    = data.get('child', {})
    schedule_data = data.get('schedule', {})

    # ── 1. Required fields ────────────────────────────────────────────── #
    required = {
        'guardian': ['fname', 'lname', 'relation', 'phone'],
        'child':    ['fname', 'lname', 'dob', 'sex', 'reason'],
        'schedule': ['date', 'time', 'visit_type'],
    }
    for section, fields in required.items():
        src = data.get(section, {})
        for f in fields:
            if not src.get(f, '').strip():
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {section}.{f}'
                }), 422

    # ── 2. Name validation ────────────────────────────────────────────── #
    for field, label in [
        (guardian_data.get('fname', ''), 'Guardian first name'),
        (guardian_data.get('lname', ''), 'Guardian last name'),
        (child_data.get('fname', ''),    'Child first name'),
        (child_data.get('lname', ''),    'Child last name'),
    ]:
        if not is_valid_name(field):
            return jsonify({
                'success': False,
                'error': f'{label} must contain letters only (min 2 characters).'
            }), 422

    # ── 3. Phone validation ───────────────────────────────────────────── #
    phone = guardian_data['phone'].strip()
    if not (phone.startswith('09') and len(phone) == 11 and phone.isdigit()):
        return jsonify({
            'success': False,
            'error': 'Invalid phone number. Must be 11 digits starting with 09.'
        }), 422

    # ── 4. Email validation (if provided) ────────────────────────────── #
    email = guardian_data.get('email', '').strip()
    if email and not is_valid_email(email):
        return jsonify({
            'success': False,
            'error': 'Invalid email address format.'
        }), 422

    # ── 5. Child date of birth validation ────────────────────────────── #
    child_dob = parse_date(child_data.get('dob', ''))
    if not child_dob:
        return jsonify({'success': False, 'error': 'Invalid date of birth.'}), 422

    today = date.today()

    # Must not be in the future
    if child_dob > today:
        return jsonify({
            'success': False,
            'error': 'Date of birth cannot be in the future.'
        }), 422

    # Child must be 18 years old or younger (pediatric clinic)
    age_years = relativedelta(today, child_dob).years
    if age_years > 18:
        return jsonify({
            'success': False,
            'error': 'This clinic serves patients 18 years old and below only.'
        }), 422

    # ── 6. Preferred date validation ─────────────────────────────────── #
    preferred_date = parse_date(schedule_data.get('date', ''))
    if not preferred_date:
        return jsonify({'success': False, 'error': 'Invalid preferred date.'}), 422

    if preferred_date < today:
        return jsonify({
            'success': False,
            'error': 'Preferred date must be today or in the future.'
        }), 422

    # Must be a weekday (Mon–Fri)
    if not is_weekday(preferred_date):
        return jsonify({
            'success': False,
            'error': 'Preferred date must be a weekday (Monday to Friday). The clinic is closed on weekends.'
        }), 422

    # ── 7. Alt date validation (if provided) ─────────────────────────── #
    alt_date = parse_date(schedule_data.get('alt_date', ''))
    if alt_date:
        if alt_date < today:
            return jsonify({
                'success': False,
                'error': 'Alternative date must be today or in the future.'
            }), 422
        if not is_weekday(alt_date):
            return jsonify({
                'success': False,
                'error': 'Alternative date must be a weekday (Monday to Friday).'
            }), 422
        if alt_date == preferred_date:
            return jsonify({
                'success': False,
                'error': 'Alternative date must be different from the preferred date.'
            }), 422

    # ── 8. Duplicate appointment check ───────────────────────────────── #
    existing = (
        Appointment.query
        .join(Guardian)
        .filter(
            Guardian.phone        == phone,
            Appointment.preferred_date == preferred_date,
            Appointment.status.in_(['pending', 'approved'])
        ).first()
    )
    if existing:
        return jsonify({
            'success': False,
            'error': f'An active appointment already exists for this phone number on {preferred_date.strftime("%B %d, %Y")} (Ref: {existing.reference_number}). Please choose a different date.'
        }), 422

    # ── Save to database ─────────────────────────────────────────────── #
    try:
        guardian = Guardian(
            first_name   = guardian_data['fname'].strip(),
            last_name    = guardian_data['lname'].strip(),
            relationship = guardian_data['relation'].strip(),
            phone        = phone,
            email        = email or None,
            address      = guardian_data.get('address', '').strip() or None,
        )
        db.session.add(guardian)
        db.session.flush()

        reference = generate_reference()
        appointment = Appointment(
            reference_number = reference,
            guardian_id      = guardian.id,
            child_first_name = child_data['fname'].strip(),
            child_last_name  = child_data['lname'].strip(),
            child_dob        = child_dob,
            child_sex        = child_data['sex'].strip(),
            reason           = child_data['reason'].strip(),
            notes            = child_data.get('notes', '').strip() or None,
            visit_type       = schedule_data['visit_type'].strip(),
            preferred_date   = preferred_date,
            preferred_time   = schedule_data['time'].strip(),
            alt_date         = alt_date,
            status           = Appointment.STATUS_PENDING,
        )
        db.session.add(appointment)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'[DB ERROR] {e}')
        return jsonify({'success': False, 'error': 'A server error occurred. Please try again.'}), 500

    # ── Send Email ────────────────────────────────────────────────────── #
    try:
        if guardian.email:
            subject, html = email_appointment_received(
                guardian_name  = guardian.full_name,
                child_name     = appointment.child_full_name,
                reference      = reference,
                preferred_date = appointment.preferred_date.strftime('%B %d, %Y'),
                preferred_time = appointment.preferred_time,
                reason         = appointment.reason,
                visit_type     = appointment.visit_type,
                clinic         = current_app.config['CLINIC_NAME'],
            )
            send_email(guardian.email, subject, html)
    except Exception as e:
        current_app.logger.error(f'[EMAIL ERROR] {e}')

    return jsonify({
        'success':          True,
        'reference_number': reference,
        'message':          'Appointment submitted successfully.',
    }), 201