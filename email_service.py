import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app


# --------------------------------------------------------------------------- #
#  Core sender
# --------------------------------------------------------------------------- #
def send_email(to_email: str, subject: str, html_body: str) -> dict:
    username  = current_app.config['MAIL_USERNAME']
    password  = current_app.config['MAIL_PASSWORD']
    from_addr = current_app.config['MAIL_FROM']
    clinic    = current_app.config['CLINIC_NAME']

    # ── Guard: credentials not configured ───────────────────────────────── #
    not_configured = (
        'your_gmail' in username.lower() or
        'xxxx' in password.lower() or
        not username or not password
    )
    if not_configured:
        current_app.logger.warning(
            f'[EMAIL SKIPPED] Gmail not configured in config.py. '
            f'To: {to_email} | Subject: {subject}'
        )
        return {'success': False, 'error': 'Email not configured'}

    # ── Guard: invalid recipient ─────────────────────────────────────────── #
    if not to_email or '@' not in to_email:
        current_app.logger.info(f'[EMAIL SKIPPED] No valid email address provided.')
        return {'success': False, 'error': 'No valid recipient email'}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[{clinic}] {subject}'
        msg['From']    = f'{clinic} <{from_addr}>'
        msg['To']      = to_email

        # Plain text fallback
        plain = re.sub(r'<[^>]+>', ' ', html_body)
        plain = re.sub(r'\s+', ' ', plain).strip()
        msg.attach(MIMEText(plain, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        sent = False
        errors = []

        # Try each provider in order until one works
        smtp_configs = [
            # (host, port, use_ssl)
            ('smtp-mail.outlook.com', 587, False),   # Outlook/Hotmail TLS
            ('smtp.gmail.com',        587, False),   # Gmail TLS
            ('smtp.gmail.com',        465, True),    # Gmail SSL
            ('smtp.mail.yahoo.com',   587, False),   # Yahoo TLS
        ]

        for host, port, use_ssl in smtp_configs:
            try:
                if use_ssl:
                    import ssl as ssl_module
                    ctx = ssl_module.create_default_context()
                    with smtplib.SMTP_SSL(host, port, context=ctx, timeout=10) as server:
                        server.ehlo()
                        server.login(username, password)
                        server.sendmail(from_addr, to_email, msg.as_string())
                else:
                    with smtplib.SMTP(host, port, timeout=10) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(username, password)
                        server.sendmail(from_addr, to_email, msg.as_string())
                sent = True
                current_app.logger.info(f'[EMAIL] Sent via {host}:{port}')
                break
            except (smtplib.SMTPConnectError, OSError, TimeoutError,
                    ConnectionRefusedError) as e:
                errors.append(f'{host}:{port} → {str(e)}')
                continue

        if not sent:
            raise smtplib.SMTPConnectError(
                -1,
                f'All SMTP servers failed. Errors: {"; ".join(errors)}'
            )

        current_app.logger.info(f'[EMAIL SENT] To: {to_email} | Subject: {subject}')
        return {'success': True}

    except smtplib.SMTPAuthenticationError:
        msg = (
            'Gmail authentication failed. Make sure you are using an App Password '
            '(not your regular Gmail password). '
            'Guide: myaccount.google.com → Security → App passwords'
        )
        current_app.logger.error(f'[EMAIL ERROR] {msg}')
        return {'success': False, 'error': msg}

    except smtplib.SMTPRecipientsRefused:
        current_app.logger.error(f'[EMAIL ERROR] Recipient refused: {to_email}')
        return {'success': False, 'error': f'Recipient email refused: {to_email}'}

    except smtplib.SMTPException as e:
        current_app.logger.error(f'[EMAIL ERROR] SMTP error: {e}')
        return {'success': False, 'error': str(e)}

    except Exception as e:
        current_app.logger.error(f'[EMAIL ERROR] Unexpected: {e}')
        return {'success': False, 'error': str(e)}


# --------------------------------------------------------------------------- #
#  Test function — call from Flask shell to verify Gmail works
#  Usage: from email_service import test_email; test_email('youremail@gmail.com')
# --------------------------------------------------------------------------- #
def test_email(to_email: str) -> None:
    result = send_email(
        to_email  = to_email,
        subject   = 'Test Email from PediaCare',
        html_body = '<h2>It works!</h2><p>Your Gmail SMTP is configured correctly.</p>',
    )
    if result['success']:
        print(f'✅ Email sent successfully to {to_email}')
    else:
        print(f'❌ Failed: {result["error"]}')


# --------------------------------------------------------------------------- #
#  Shared HTML wrapper
# --------------------------------------------------------------------------- #
def _wrap(clinic: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ font-family: Arial, sans-serif; background:#F0F7F4; margin:0; padding:0; color:#0F2420; }}
  .wrap {{ max-width:580px; margin:32px auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,.07); }}
  .header {{ background:#1B5E4B; padding:28px 32px; text-align:center; }}
  .header h1 {{ color:#fff; font-size:20px; margin:0 0 4px; }}
  .header p {{ color:rgba(255,255,255,.65); font-size:12px; margin:0; }}
  .body {{ padding:32px; }}
  .info-table {{ width:100%; border-collapse:separate; border-spacing:0 4px; margin:20px 0; }}
  .info-table td {{ padding:10px 14px; font-size:13.5px; }}
  .info-table td:first-child {{ color:#5A7A72; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.4px; background:#F0F7F4; border-radius:6px 0 0 6px; width:36%; }}
  .info-table td:last-child {{ background:#FAFCFB; border-radius:0 6px 6px 0; font-weight:500; }}
  .divider {{ height:1px; background:#D0E5DC; margin:24px 0; }}
  .badge {{ display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }}
  .badge-pending     {{ background:#FEF3CD; color:#78430A; }}
  .badge-approved    {{ background:#D1FAE5; color:#065F46; }}
  .badge-rescheduled {{ background:#DBEAFE; color:#1E3A8A; }}
  .badge-cancelled   {{ background:#FEE2E2; color:#7F1D1D; }}
  .notice {{ background:#E8F5F0; border-left:3px solid #1B5E4B; padding:14px 16px; font-size:13px; color:#1B5E4B; margin:20px 0; border-radius:0 8px 8px 0; }}
  .ref {{ font-family:monospace; background:#E8F5F0; color:#1B5E4B; padding:2px 8px; border-radius:5px; font-weight:700; }}
  .footer {{ background:#F0F7F4; padding:18px 32px; text-align:center; font-size:11.5px; color:#5A7A72; border-top:1px solid #D0E5DC; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>{clinic}</h1>
    <p>Appointment Notification</p>
  </div>
  <div class="body">{content}</div>
  <div class="footer">
    This is an automated message from {clinic}. Please do not reply to this email.
  </div>
</div>
</body>
</html>"""


# --------------------------------------------------------------------------- #
#  Email templates
# --------------------------------------------------------------------------- #

def email_appointment_received(
    guardian_name, child_name, reference,
    preferred_date, preferred_time, reason, visit_type, clinic
):
    subject = f'Appointment Request Received – {reference}'
    content = f"""
    <p style="font-size:15px;margin-bottom:16px">Hello <strong>{guardian_name}</strong>,</p>
    <p style="font-size:14px;color:#3D5A54;line-height:1.7;margin-bottom:20px">
      We received your appointment request for <strong>{child_name}</strong>.
      Our clinic assistant will review and confirm your schedule shortly.
    </p>
    <table class="info-table">
      <tr><td>Reference #</td><td><span class="ref">{reference}</span></td></tr>
      <tr><td>Patient</td><td>{child_name}</td></tr>
      <tr><td>Reason</td><td>{reason}</td></tr>
      <tr><td>Visit type</td><td>{visit_type}</td></tr>
      <tr><td>Preferred date</td><td>{preferred_date}</td></tr>
      <tr><td>Preferred time</td><td>{preferred_time}</td></tr>
      <tr><td>Status</td><td><span class="badge badge-pending">Pending Review</span></td></tr>
    </table>
    <div class="notice">
      <strong>What happens next?</strong><br>
      Our clinic assistant will review your request and send you a confirmation email with the final schedule.
    </div>
    <div class="divider"></div>
    <p style="font-size:12px;color:#5A7A72">
      Keep your reference number <span class="ref">{reference}</span> for follow-ups.
    </p>"""
    return subject, _wrap(clinic, content)


def email_appointment_approved(
    guardian_name, child_name, reference,
    confirmed_date, confirmed_time, visit_type, clinic, clinic_address
):
    subject = f'Appointment Confirmed – {reference}'
    location = clinic_address if 'In-person' in visit_type else 'Video call (link will be sent separately)'
    content = f"""
    <p style="font-size:15px;margin-bottom:16px">Hello <strong>{guardian_name}</strong>,</p>
    <p style="font-size:14px;color:#3D5A54;line-height:1.7;margin-bottom:20px">
      Great news! The appointment for <strong>{child_name}</strong> is
      <strong style="color:#065F46">confirmed</strong>.
    </p>
    <table class="info-table">
      <tr><td>Reference #</td><td><span class="ref">{reference}</span></td></tr>
      <tr><td>Patient</td><td>{child_name}</td></tr>
      <tr><td>Date</td><td><strong>{confirmed_date}</strong></td></tr>
      <tr><td>Time</td><td><strong>{confirmed_time}</strong></td></tr>
      <tr><td>Visit type</td><td>{visit_type}</td></tr>
      <tr><td>Location</td><td>{location}</td></tr>
      <tr><td>Status</td><td><span class="badge badge-approved">Confirmed</span></td></tr>
    </table>
    <div class="notice">
      <strong>Reminder:</strong> Please arrive 10–15 minutes early and bring any
      relevant medical records or previous prescriptions.
    </div>"""
    return subject, _wrap(clinic, content)


def email_appointment_rescheduled(
    guardian_name, child_name, reference,
    new_date, new_time, reason, clinic
):
    subject = f'Appointment Rescheduled – {reference}'
    reason_row = f'<tr><td>Reason</td><td>{reason}</td></tr>' if reason else ''
    content = f"""
    <p style="font-size:15px;margin-bottom:16px">Hello <strong>{guardian_name}</strong>,</p>
    <p style="font-size:14px;color:#3D5A54;line-height:1.7;margin-bottom:20px">
      We need to reschedule the appointment for <strong>{child_name}</strong>.
      Please see the updated schedule below.
    </p>
    <table class="info-table">
      <tr><td>Reference #</td><td><span class="ref">{reference}</span></td></tr>
      <tr><td>Patient</td><td>{child_name}</td></tr>
      <tr><td>New date</td><td><strong>{new_date}</strong></td></tr>
      <tr><td>New time</td><td><strong>{new_time}</strong></td></tr>
      {reason_row}
      <tr><td>Status</td><td><span class="badge badge-rescheduled">Rescheduled</span></td></tr>
    </table>
    <div class="notice">
      If this new schedule doesn't work for you, please contact us directly at the clinic.
    </div>"""
    return subject, _wrap(clinic, content)


def email_appointment_cancelled(
    guardian_name, child_name, reference,
    reason, clinic, clinic_phone
):
    subject = f'Appointment Cancelled – {reference}'
    reason_row = f'<tr><td>Reason</td><td>{reason}</td></tr>' if reason else ''
    content = f"""
    <p style="font-size:15px;margin-bottom:16px">Hello <strong>{guardian_name}</strong>,</p>
    <p style="font-size:14px;color:#3D5A54;line-height:1.7;margin-bottom:20px">
      We regret to inform you that the appointment for <strong>{child_name}</strong>
      has been <strong style="color:#7F1D1D">cancelled</strong>.
    </p>
    <table class="info-table">
      <tr><td>Reference #</td><td><span class="ref">{reference}</span></td></tr>
      <tr><td>Patient</td><td>{child_name}</td></tr>
      {reason_row}
      <tr><td>Status</td><td><span class="badge badge-cancelled">Cancelled</span></td></tr>
    </table>
    <div class="notice">
      To reschedule, call us at <strong>{clinic_phone}</strong> or submit a new appointment request.
    </div>"""
    return subject, _wrap(clinic, content)