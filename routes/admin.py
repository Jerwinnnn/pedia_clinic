from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func

from extensions import db
from models import User, Appointment, Guardian
from email_service import (
    send_email,
    email_appointment_approved,
    email_appointment_rescheduled,
    email_appointment_cancelled,
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

    counts = {
        'all':         Appointment.query.count(),
        'pending':     Appointment.query.filter_by(status='pending').count(),
        'approved':    Appointment.query.filter_by(status='approved').count(),
        'rescheduled': Appointment.query.filter_by(status='rescheduled').count(),
        'cancelled':   Appointment.query.filter_by(status='cancelled').count(),
        'completed':   Appointment.query.filter_by(status='completed').count(),
    }

    # Bar chart — appointments per day for last 7 days
    today = date.today()
    bar_labels = []
    bar_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Appointment.query.filter(
            func.date(Appointment.created_at) == day
        ).count()
        bar_labels.append(day.strftime('%a %d'))
        bar_data.append(count)

    today_str = today.strftime('%Y-%m-%d')

    # All appointments unfiltered (for today's section)
    all_appointments = Appointment.query.join(Guardian).order_by(Appointment.created_at.desc()).all()

    return render_template(
        'admin/dashboard.html',
        appointments=appointments,
        all_appointments=all_appointments,
        counts=counts,
        status_filter=status_filter,
        bar_labels=bar_labels,
        bar_data=bar_data,
        today_str=today_str,
    )



# --------------------------------------------------------------------------- #
#  Appointments list (separate from dashboard)
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointments')
@login_required
def appointments():
    status_filter = request.args.get('status', 'all')
    search_query  = request.args.get('q', '').strip()

    query = (
        Appointment.query
        .join(Guardian, Appointment.guardian_id == Guardian.id)
        .order_by(Appointment.created_at.desc())
    )

    # Status filter
    if status_filter != 'all':
        query = query.filter(Appointment.status == status_filter)

    # Search filter — reference number, child name, guardian name
    if search_query:
        like = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Appointment.reference_number.ilike(like),
                Appointment.child_first_name.ilike(like),
                Appointment.child_last_name.ilike(like),
                Guardian.first_name.ilike(like),
                Guardian.last_name.ilike(like),
                Guardian.phone.ilike(like),
                db.func.concat(
                    Appointment.child_first_name, ' ',
                    Appointment.child_last_name
                ).ilike(like),
                db.func.concat(
                    Guardian.first_name, ' ',
                    Guardian.last_name
                ).ilike(like),
            )
        )

    appointments = query.all()

    counts = {
        'all':         Appointment.query.count(),
        'pending':     Appointment.query.filter_by(status='pending').count(),
        'approved':    Appointment.query.filter_by(status='approved').count(),
        'rescheduled': Appointment.query.filter_by(status='rescheduled').count(),
        'cancelled':   Appointment.query.filter_by(status='cancelled').count(),
        'completed':   Appointment.query.filter_by(status='completed').count(),
    }

    return render_template(
        'admin/appointments.html',
        appointments=appointments,
        counts=counts,
        status_filter=status_filter,
        search_query=search_query,
    )

# --------------------------------------------------------------------------- #
#  Appointment detail
# --------------------------------------------------------------------------- #
@admin_bp.route('/appointment/<int:appointment_id>')
@login_required
def appointment_detail(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    counts = {
        'pending':     Appointment.query.filter_by(status='pending').count(),
        'approved':    Appointment.query.filter_by(status='approved').count(),
        'rescheduled': Appointment.query.filter_by(status='rescheduled').count(),
        'cancelled':   Appointment.query.filter_by(status='cancelled').count(),
        'completed':   Appointment.query.filter_by(status='completed').count(),
    }
    return render_template('admin/appointment_detail.html', appointment=appointment, counts=counts)


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

    guardian = appointment.guardian
    # Send approval email
    try:
        if guardian.email:
            subject, html = email_appointment_approved(
                guardian_name  = guardian.full_name,
                child_name     = appointment.child_full_name,
                reference      = appointment.reference_number,
                confirmed_date = confirmed_date.strftime('%B %d, %Y'),
                confirmed_time = confirmed_time,
                visit_type     = appointment.visit_type,
                clinic         = current_app.config['CLINIC_NAME'],
                clinic_address = current_app.config['CLINIC_ADDRESS'],
            )
            send_email(guardian.email, subject, html)
    except Exception as e:
        current_app.logger.error(f'[EMAIL ERROR on approve] {e}')

    flash(f'Appointment {appointment.reference_number} approved and client notified.', 'success')
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
    # Send reschedule email
    try:
        if guardian.email:
            subject, html = email_appointment_rescheduled(
                guardian_name = guardian.full_name,
                child_name    = appointment.child_full_name,
                reference     = appointment.reference_number,
                new_date      = new_date.strftime('%B %d, %Y'),
                new_time      = new_time,
                reason        = reason,
                clinic        = current_app.config['CLINIC_NAME'],
            )
            send_email(guardian.email, subject, html)
    except Exception as e:
        current_app.logger.error(f'[EMAIL ERROR on reschedule] {e}')

    flash(f'Appointment {appointment.reference_number} rescheduled and client notified.', 'success')
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
    # Send cancellation email
    try:
        if guardian.email:
            subject, html = email_appointment_cancelled(
                guardian_name = guardian.full_name,
                child_name    = appointment.child_full_name,
                reference     = appointment.reference_number,
                reason        = reason,
                clinic        = current_app.config['CLINIC_NAME'],
                clinic_phone  = current_app.config['CLINIC_PHONE'],
            )
            send_email(guardian.email, subject, html)
    except Exception as e:
        current_app.logger.error(f'[EMAIL ERROR on cancel] {e}')

    flash(f'Appointment {appointment.reference_number} cancelled and client notified.', 'success')
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


# --------------------------------------------------------------------------- #
#  User management
# --------------------------------------------------------------------------- #
@admin_bp.route('/users')
@login_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    counts = {
        'all':         Appointment.query.count(),
        'pending':     Appointment.query.filter_by(status='pending').count(),
        'approved':    Appointment.query.filter_by(status='approved').count(),
        'rescheduled': Appointment.query.filter_by(status='rescheduled').count(),
        'cancelled':   Appointment.query.filter_by(status='cancelled').count(),
        'completed':   Appointment.query.filter_by(status='completed').count(),
    }
    return render_template('admin/users.html', users=all_users, counts=counts)


@admin_bp.route('/users/create', methods=['POST'])
@login_required
def create_user():
    username  = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password  = request.form.get('password', '').strip()
    confirm   = request.form.get('confirm_password', '').strip()

    if not username or not full_name or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('admin.users'))

    if password != confirm:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('admin.users'))

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" is already taken.', 'error')
        return redirect(url_for('admin.users'))

    from werkzeug.security import generate_password_hash
    new_user = User(
        username  = username,
        full_name = full_name,
        password  = generate_password_hash(password),
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f'User "{username}" created successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/change-password', methods=['POST'])
@login_required
def change_password(user_id):
    user       = User.query.get_or_404(user_id)
    password   = request.form.get('password', '').strip()
    confirm    = request.form.get('confirm_password', '').strip()

    if not password:
        flash('Password cannot be empty.', 'error')
        return redirect(url_for('admin.users'))

    if password != confirm:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('admin.users'))

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('admin.users'))

    from werkzeug.security import generate_password_hash
    user.password = generate_password_hash(password)
    db.session.commit()
    flash(f'Password for "{user.username}" updated successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))

    if User.query.count() <= 1:
        flash('Cannot delete the only admin account.', 'error')
        return redirect(url_for('admin.users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'success')
    return redirect(url_for('admin.users'))