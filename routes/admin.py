from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime

from app import db
from models import User, Appointment, Guardian
from sms import (
    send_sms,
    sms_appointment_approved,
    sms_appointment_rescheduled,
    sms_appointment_cancelled,
)

admin_bp = Blueprint('admin', __name__)


# --------------------------------------------------------------------------- #
#  Login / Logout
# --------------------------------------------------------------------------- #
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


# --------------------------------------------------------------------------- #
#  Dashboard — list all appointments
# --------------------------------------------------------------------------- #
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    status_filter = request.args.get('status', 'all')

    query = (
        Appointment.query
        .join(Guardian, Appointment.guardian_id == Guardian.id)
        .order_by(Appointment.created_at.desc())
    )

    if status_filter != 'all':
        query = query.filter(Appointment.status == status_filter)

    appointments = query.all()

    # Counts for the summary cards
    counts = {
        'all':         Appointment.query.count(),
        'pending':     Appointment.query.filter_by(status='pending').count(),
        'approved':    Appointment.query.filter_by(status='approved').count(),
        'rescheduled': Appointment.query.filter_by(status='rescheduled').count(),
        'cancelled':   Appointment.query.filter_by(status='cancelled').count(),
        'completed':   Appointment.query.filter_by(status='completed').count(),
    }

    return render_template(
        'admin/dashboard.html',
        appointments=appointments,
        counts=counts,
        status_filter=status_filter,
    )


# --------------------------------------------------------------------------- #
#  Appointment detail
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointment/<int:appointment_id>')
@login_required
def appointment_detail(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('admin/appointment_detail.html', appointment=appointment)


# --------------------------------------------------------------------------- #
#  Approve
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointment/<int:appointment_id>/approve', methods=['POST'])
@login_required
def approve(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    confirmed_date_str = request.form.get('confirmed_date', '').strip()
    confirmed_time     = request.form.get('confirmed_time', '').strip()
    admin_notes        = request.form.get('admin_notes', '').strip()

    if not confirmed_date_str or not confirmed_time:
        flash('Please provide the confirmed date and time.', 'error')
        return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))

    try:
        confirmed_date = datetime.strptime(confirmed_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))

    appointment.status         = Appointment.STATUS_APPROVED
    appointment.confirmed_date = confirmed_date
    appointment.confirmed_time = confirmed_time
    appointment.admin_notes    = admin_notes
    appointment.reviewed_by    = current_user.id
    appointment.reviewed_at    = datetime.utcnow()
    db.session.commit()

    # Send SMS
    guardian = appointment.guardian
    sms_body = sms_appointment_approved(
        guardian_name  = guardian.full_name,
        child_name     = appointment.child_full_name,
        reference      = appointment.reference_number,
        confirmed_date = confirmed_date.strftime('%B %d, %Y'),
        confirmed_time = confirmed_time,
        visit_type     = appointment.visit_type,
        clinic_address = current_app.config['CLINIC_ADDRESS'],
    )
    send_sms(guardian.phone, sms_body)

    flash(f'Appointment {appointment.reference_number} approved and client notified via SMS.', 'success')
    return redirect(url_for('admin.dashboard'))


# --------------------------------------------------------------------------- #
#  Reschedule
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointment/<int:appointment_id>/reschedule', methods=['POST'])
@login_required
def reschedule(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    new_date_str = request.form.get('new_date', '').strip()
    new_time     = request.form.get('new_time', '').strip()
    reason       = request.form.get('reason', '').strip()
    admin_notes  = request.form.get('admin_notes', '').strip()

    if not new_date_str or not new_time:
        flash('Please provide the new date and time.', 'error')
        return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))

    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))

    appointment.status         = Appointment.STATUS_RESCHEDULED
    appointment.confirmed_date = new_date
    appointment.confirmed_time = new_time
    appointment.admin_notes    = admin_notes
    appointment.reviewed_by    = current_user.id
    appointment.reviewed_at    = datetime.utcnow()
    db.session.commit()

    guardian = appointment.guardian
    sms_body = sms_appointment_rescheduled(
        guardian_name = guardian.full_name,
        child_name    = appointment.child_full_name,
        reference     = appointment.reference_number,
        new_date      = new_date.strftime('%B %d, %Y'),
        new_time      = new_time,
        reason        = reason,
    )
    send_sms(guardian.phone, sms_body)

    flash(f'Appointment {appointment.reference_number} rescheduled and client notified via SMS.', 'success')
    return redirect(url_for('admin.dashboard'))


# --------------------------------------------------------------------------- #
#  Cancel
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    reason      = request.form.get('reason', '').strip()
    admin_notes = request.form.get('admin_notes', '').strip()

    appointment.status      = Appointment.STATUS_CANCELLED
    appointment.admin_notes = admin_notes
    appointment.reviewed_by = current_user.id
    appointment.reviewed_at = datetime.utcnow()
    db.session.commit()

    guardian = appointment.guardian
    sms_body = sms_appointment_cancelled(
        guardian_name = guardian.full_name,
        child_name    = appointment.child_full_name,
        reference     = appointment.reference_number,
        reason        = reason,
    )
    send_sms(guardian.phone, sms_body)

    flash(f'Appointment {appointment.reference_number} cancelled and client notified via SMS.', 'success')
    return redirect(url_for('admin.dashboard'))


# --------------------------------------------------------------------------- #
#  Mark as completed
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
def complete(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = Appointment.STATUS_COMPLETED
    db.session.commit()
    flash(f'Appointment {appointment.reference_number} marked as completed.', 'success')
    return redirect(url_for('admin.dashboard'))


# --------------------------------------------------------------------------- #
#  API — counts for dashboard badge refresh (optional AJAX use)
# --------------------------------------------------------------------------- #
@admin_bp.route('/api/counts')
@login_required
def api_counts():
    return jsonify({
        'pending':     Appointment.query.filter_by(status='pending').count(),
        'approved':    Appointment.query.filter_by(status='approved').count(),
        'rescheduled': Appointment.query.filter_by(status='rescheduled').count(),
        'cancelled':   Appointment.query.filter_by(status='cancelled').count(),
        'completed':   Appointment.query.filter_by(status='completed').count(),
    })