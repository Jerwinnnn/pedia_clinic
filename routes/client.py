from flask import Blueprint, request, jsonify, render_template, current_app
from datetime import datetime, date
import random
import string

from app import db
from models import Guardian, Appointment
from sms import send_sms, sms_appointment_received

client_bp = Blueprint('client', __name__)


def generate_reference() -> str:
    """Generate a unique reference number like APT-48291."""
    while True:
        ref = 'APT-' + ''.join(random.choices(string.digits, k=5))
        if not Appointment.query.filter_by(reference_number=ref).first():
            return ref


def parse_date(date_str: str):
    """Safely parse a date string (YYYY-MM-DD). Returns None if empty."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
#  GET /  — serve the appointment form
# --------------------------------------------------------------------------- #
@client_bp.route('/')
def index():
    return render_template('form.html')


# --------------------------------------------------------------------------- #
#  POST /submit-appointment  — receive form data, save to DB, send SMS
# --------------------------------------------------------------------------- #
@client_bp.route('/submit-appointment', methods=['POST'])
def submit_appointment():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request.'}), 400

    guardian_data = data.get('guardian', {})
    child_data    = data.get('child', {})
    schedule_data = data.get('schedule', {})

    # ---- Basic validation ------------------------------------------------- #
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

    phone = guardian_data['phone'].strip()
    if not (phone.startswith('09') and len(phone) == 11 and phone.isdigit()):
        return jsonify({'success': False, 'error': 'Invalid phone number format.'}), 422

    child_dob = parse_date(child_data.get('dob', ''))
    if not child_dob:
        return jsonify({'success': False, 'error': 'Invalid date of birth.'}), 422

    preferred_date = parse_date(schedule_data.get('date', ''))
    if not preferred_date or preferred_date < date.today():
        return jsonify({'success': False, 'error': 'Preferred date must be today or in the future.'}), 422

    # ---- Save to database ------------------------------------------------- #
    try:
        guardian = Guardian(
            first_name   = guardian_data['fname'].strip(),
            last_name    = guardian_data['lname'].strip(),
            relationship = guardian_data['relation'].strip(),
            phone        = phone,
            email        = guardian_data.get('email', '').strip() or None,
        )
        db.session.add(guardian)
        db.session.flush()  # get guardian.id before committing

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
            alt_date         = parse_date(schedule_data.get('alt_date', '')),
            status           = Appointment.STATUS_PENDING,
        )
        db.session.add(appointment)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'DB error on appointment submit: {e}')
        return jsonify({'success': False, 'error': 'A server error occurred. Please try again.'}), 500

    # ---- Send confirmation SMS -------------------------------------------- #
    sms_body = sms_appointment_received(
        guardian_name = guardian.full_name,
        child_name    = appointment.child_full_name,
        reference     = reference,
    )
    send_sms(phone, sms_body)

    return jsonify({
        'success':          True,
        'reference_number': reference,
        'message':          'Appointment submitted successfully.',
    }), 201