from flask import current_app

try:
    import requests
except ImportError:
    requests = None


def send_sms(phone_number: str, message: str) -> dict:
    """
    Send an SMS via the Semaphore API.

    Args:
        phone_number: Recipient's PH mobile number (e.g. 09171234567)
        message:      The SMS body text

    Returns:
        dict with 'success' bool and 'response' or 'error' keys
    """
    api_key   = current_app.config['SEMAPHORE_API_KEY']
    sender    = current_app.config['SEMAPHORE_SENDER']
    api_url   = current_app.config['SEMAPHORE_API_URL']

    if api_key == 'YOUR_SEMAPHORE_API_KEY':
        # SMS not configured — log and skip (useful during development)
        current_app.logger.warning(
            f'[SMS SKIPPED] To: {phone_number} | Message: {message}'
        )
        return {'success': False, 'error': 'SMS API key not configured.'}

    payload = {
        'apikey':      api_key,
        'number':      phone_number,
        'message':     message,
        'sendername':  sender,
    }

    try:
        resp = requests.post(api_url, data=payload, timeout=10)
        resp.raise_for_status()
        current_app.logger.info(f'[SMS SENT] To: {phone_number}')
        return {'success': True, 'response': resp.json()}
    except requests.RequestException as e:
        current_app.logger.error(f'[SMS ERROR] {e}')
        return {'success': False, 'error': str(e)}


# --------------------------------------------------------------------------- #
#  Pre-built SMS message templates
# --------------------------------------------------------------------------- #

def sms_appointment_received(guardian_name: str, child_name: str, reference: str) -> str:
    return (
        f"Hello {guardian_name}! We received your appointment request for "
        f"{child_name} (Ref: {reference}). Our staff will review it and confirm "
        f"your schedule shortly. Thank you! - PediaCare Clinic"
    )


def sms_appointment_approved(
    guardian_name: str,
    child_name: str,
    reference: str,
    confirmed_date: str,
    confirmed_time: str,
    visit_type: str,
    clinic_address: str
) -> str:
    location = clinic_address if visit_type == 'In-person' else 'via video call (link to be sent)'
    return (
        f"Good news, {guardian_name}! Your appointment for {child_name} "
        f"(Ref: {reference}) is CONFIRMED on {confirmed_date} at {confirmed_time}. "
        f"Location: {location}. See you soon! - PediaCare Clinic"
    )


def sms_appointment_rescheduled(
    guardian_name: str,
    child_name: str,
    reference: str,
    new_date: str,
    new_time: str,
    reason: str = ''
) -> str:
    note = f' Reason: {reason}.' if reason else ''
    return (
        f"Hello {guardian_name}, we need to reschedule {child_name}'s appointment "
        f"(Ref: {reference}).{note} New schedule: {new_date} at {new_time}. "
        f"Please reply or call us for concerns. - PediaCare Clinic"
    )


def sms_appointment_cancelled(
    guardian_name: str,
    child_name: str,
    reference: str,
    reason: str = ''
) -> str:
    note = f' Reason: {reason}.' if reason else ''
    return (
        f"Hello {guardian_name}, your appointment for {child_name} "
        f"(Ref: {reference}) has been CANCELLED.{note} "
        f"Please call us to reschedule. - PediaCare Clinic"
    )