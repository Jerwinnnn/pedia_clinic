  let currentPage = 1;
  let selectedReason = '';
  let selectedVisit  = '';
  let toastTimer     = null;

  // ── Toast helpers ──────────────────────────────────────────────────── //
  function showToast(title, errors) {
    const toast = document.getElementById('valToast');
    document.getElementById('valToastTitle').textContent = title;
    const body = document.getElementById('valToastBody');
    if (Array.isArray(errors) && errors.length > 1) {
      body.innerHTML = '<ul>' + errors.map(e => `<li>${e}</li>`).join('') + '</ul>';
    } else {
      body.innerHTML = Array.isArray(errors) ? errors[0] : errors;
    }
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(hideToast, 5000);
  }

  function hideToast() {
    document.getElementById('valToast').classList.remove('show');
  }

  // ── Radio helpers ──────────────────────────────────────────────────── //
  function selectReason(val, id) {
    selectedReason = val;
    document.querySelectorAll('[id^="ro"]').forEach(el => el.classList.remove('selected'));
    document.getElementById(id).classList.add('selected');
    document.getElementById('err_reason').classList.remove('show');
  }

  function selectVisit(val, id) {
    selectedVisit = val;
    document.querySelectorAll('[id^="vt"]').forEach(el => el.classList.remove('selected'));
    document.getElementById(id).classList.add('selected');
    document.getElementById('err_vtype').classList.remove('show');
  }

  // ── Navigation ─────────────────────────────────────────────────────── //
  function goTo(n) {
    if (n >= currentPage) return;
    showPage(n);
  }

  function showPage(n) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page' + n).classList.add('active');
    document.querySelectorAll('.step').forEach((s, i) => {
      s.classList.remove('active', 'done');
      if (i + 1 === n) s.classList.add('active');
      if (i + 1 < n)  s.classList.add('done');
    });
    currentPage = n;
    hideToast();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ── Field error helpers ────────────────────────────────────────────── //
  function setError(fieldId, errId, hasError) {
    const el  = document.getElementById(fieldId);
    const err = document.getElementById(errId);
    if (!el || !err) return;
    if (hasError) { el.classList.add('error');    err.classList.add('show'); }
    else          { el.classList.remove('error'); err.classList.remove('show'); }
  }

  function clearAllDobErrors() {
    ['err_c_dob', 'err_c_dob_age', 'err_c_dob_future'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.remove('show');
    });
    const dob = document.getElementById('c_dob');
    if (dob) dob.classList.remove('error');
  }

  function isValidName(val) {
    return /^[A-Za-z\s'\-\.]{2,}$/.test(val.trim());
  }

  function isValidEmail(val) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());
  }

  function isWeekday(dateStr) {
    if (!dateStr) return true;
    const d = new Date(dateStr + 'T00:00:00');
    const day = d.getDay(); // 0=Sun, 6=Sat
    return day !== 0 && day !== 6;
  }

  function getChildAge(dobStr) {
    if (!dobStr) return null;
    const dob   = new Date(dobStr);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
    return age;
  }

  // ── Step 1 Validation ─────────────────────────────────────────────── //
  function validate1() {
    const errors = [];

    // First name
    const fname = v('g_fname');
    const fnameOk = isValidName(fname);
    setError('g_fname', 'err_g_fname', !fnameOk);
    if (!fnameOk) errors.push(fname.trim() === '' ? 'Guardian first name is required.' : 'First name must contain letters only (min 2 characters).');

    // Last name
    const lname = v('g_lname');
    const lnameOk = isValidName(lname);
    setError('g_lname', 'err_g_lname', !lnameOk);
    if (!lnameOk) errors.push(lname.trim() === '' ? 'Guardian last name is required.' : 'Last name must contain letters only (min 2 characters).');

    // Relationship
    const relOk = v('g_relation') !== '';
    setError('g_relation', 'err_g_relation', !relOk);
    if (!relOk) errors.push('Please select your relationship to the child.');

    // Phone
    const phoneOk = /^09\d{9}$/.test(v('g_phone').trim());
    setError('g_phone', 'err_g_phone', !phoneOk);
    if (!phoneOk) errors.push('Mobile number must be 11 digits starting with 09.');

    // Email (optional but validate format if provided)
    const email = v('g_email').trim();
    const emailOk = email === '' || isValidEmail(email);
    setError('g_email', 'err_g_email', !emailOk);
    if (!emailOk) errors.push('Please enter a valid email address (e.g. name@email.com).');

    if (errors.length > 0) {
      showToast(
        errors.length === 1 ? 'Please fix this before continuing' : `Please fix ${errors.length} errors before continuing`,
        errors
      );
      return false;
    }
    return true;
  }

  // ── Step 2 Validation ─────────────────────────────────────────────── //
  function validate2() {
    const errors = [];

    // Child first name
    const cfname = v('c_fname');
    const cfnameOk = isValidName(cfname);
    setError('c_fname', 'err_c_fname', !cfnameOk);
    if (!cfnameOk) errors.push(cfname.trim() === '' ? 'Child first name is required.' : 'Child first name must contain letters only.');

    // Child last name
    const clname = v('c_lname');
    const clnameOk = isValidName(clname);
    setError('c_lname', 'err_c_lname', !clnameOk);
    if (!clnameOk) errors.push(clname.trim() === '' ? 'Child last name is required.' : 'Child last name must contain letters only.');

    // Date of birth
    clearAllDobErrors();
    const dob = v('c_dob');
    if (!dob) {
      document.getElementById('c_dob').classList.add('error');
      document.getElementById('err_c_dob').classList.add('show');
      errors.push("Please enter the child's date of birth.");
    } else {
      const today = new Date(); today.setHours(0,0,0,0);
      const dobDate = new Date(dob + 'T00:00:00');
      if (dobDate > today) {
        document.getElementById('c_dob').classList.add('error');
        document.getElementById('err_c_dob_future').classList.add('show');
        errors.push('Date of birth cannot be in the future.');
      } else {
        const age = getChildAge(dob);
        if (age > 18) {
          document.getElementById('c_dob').classList.add('error');
          document.getElementById('err_c_dob_age').classList.add('show');
          errors.push('This clinic serves patients 18 years old and below only.');
        }
      }
    }

    // Sex
    const sexOk = v('c_sex') !== '';
    setError('c_sex', 'err_c_sex', !sexOk);
    if (!sexOk) errors.push("Please select the child's sex.");

    // Reason
    const reasonErr = document.getElementById('err_reason');
    if (!selectedReason) {
      reasonErr.classList.add('show');
      errors.push('Please select a purpose of visit.');
    } else {
      reasonErr.classList.remove('show');
    }

    if (errors.length > 0) {
      showToast(
        errors.length === 1 ? 'Please fix this before continuing' : `Please fix ${errors.length} errors before continuing`,
        errors
      );
      return false;
    }
    return true;
  }

  // ── Step 3 Validation ─────────────────────────────────────────────── //
  function validate3() {
    const errors = [];

    // Preferred date
    const sdate = v('s_date');
    const sdateEl  = document.getElementById('s_date');
    const sdateErr = document.getElementById('err_s_date');
    const sdateWeekendErr = document.getElementById('err_s_date_weekend');

    sdateEl.classList.remove('error');
    sdateErr.classList.remove('show');
    sdateWeekendErr.classList.remove('show');

    if (!sdate) {
      sdateEl.classList.add('error');
      sdateErr.classList.add('show');
      errors.push('Please select a preferred date.');
    } else if (!isWeekday(sdate)) {
      sdateEl.classList.add('error');
      sdateWeekendErr.classList.add('show');
      errors.push('Preferred date must be a weekday (Monday to Friday). The clinic is closed on weekends.');
    }

    // Time slot
    const timeOk = v('s_time') !== '';
    setError('s_time', 'err_s_time', !timeOk);
    if (!timeOk) errors.push('Please select a preferred time slot.');

    // Visit type
    const vtypeErr = document.getElementById('err_vtype');
    if (!selectedVisit) {
      vtypeErr.classList.add('show');
      errors.push('Please select a visit type (in-person or teleconsultation).');
    } else {
      vtypeErr.classList.remove('show');
    }

    if (errors.length > 0) {
      showToast(
        errors.length === 1 ? 'Please fix this before continuing' : `Please fix ${errors.length} errors before continuing`,
        errors
      );
      return false;
    }
    return true;
  }

  // ── Navigation ─────────────────────────────────────────────────────── //
  function nextPage(n) {
    if (n === 1 && !validate1()) return;
    if (n === 2 && !validate2()) return;
    if (n === 3 && !validate3()) return;
    if (n === 3) buildSummary();
    showPage(n + 1);
  }

  function prevPage(n) { showPage(n - 1); }

  // ── Summary builder ────────────────────────────────────────────────── //
  function buildSummary() {
    const rows = [
      ['Guardian',       v('g_fname') + ' ' + v('g_lname') + ' (' + v('g_relation') + ')'],
      ['Mobile',         v('g_phone')],
      ['Email',          v('g_email') || '—'],
      ['Child',          v('c_fname') + ' ' + v('c_lname')],
      ['Date of birth',  v('c_dob')],
      ['Sex',            v('c_sex')],
      ['Reason',         selectedReason],
      ['Notes',          v('c_notes') || '—'],
      ['Preferred date', v('s_date')],
      ['Time slot',      v('s_time')],
      ['Alt. date',      v('s_alt_date') || '—'],
      ['Visit type',     selectedVisit],
    ];
    document.getElementById('summary').innerHTML = rows.map(([k, val]) => `
      <div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--border);gap:12px">
        <span style="color:var(--muted);flex-shrink:0;font-size:11px;text-transform:uppercase;letter-spacing:0.4px;padding-top:2px">${k}</span>
        <span style="color:var(--text);text-align:right;font-size:13.5px">${val}</span>
      </div>`).join('');
  }

  function v(id) { return document.getElementById(id).value; }

  // ── Submit ─────────────────────────────────────────────────────────── //
  async function submitForm() {
    const btn = document.querySelector('#page4 .btn-next');
    btn.disabled = true;
    btn.textContent = 'Submitting…';

    const payload = {
      guardian: {
        fname:    v('g_fname'),
        lname:    v('g_lname'),
        relation: v('g_relation'),
        phone:    v('g_phone'),
        email:    v('g_email'),
        address:  v('g_address') || '',
      },
      child: {
        fname:  v('c_fname'),
        lname:  v('c_lname'),
        dob:    v('c_dob'),
        sex:    v('c_sex'),
        reason: selectedReason,
        notes:  v('c_notes'),
      },
      schedule: {
        date:       v('s_date'),
        time:       v('s_time'),
        alt_date:   v('s_alt_date'),
        visit_type: selectedVisit,
      }
    };

    try {
      const res = await fetch('/submit-appointment', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });

      let data;
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        data = await res.json();
      } else {
        data = res.ok
          ? { success: true,  reference_number: 'APT-' + Math.floor(10000 + Math.random() * 90000) }
          : { success: false, error: `Server error (${res.status}). Your appointment may have been saved — please check with the clinic.` };
      }

      if (data.success) {
        document.getElementById('ref-num').textContent = data.reference_number;
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.step').forEach(s => { s.classList.remove('active'); s.classList.add('done'); });
        document.getElementById('page5').classList.add('active');
      } else {
        showToast('Submission Failed', data.error || 'Something went wrong. Please try again.');
        btn.disabled = false;
        btn.textContent = 'Submit Appointment';
      }

    } catch (err) {
      showToast('Connection Error', 'Could not reach the server. Please check your internet connection and try again.');
      btn.disabled = false;
      btn.textContent = 'Submit Appointment';
    }
  }

  // ── Set min date to today ──────────────────────────────────────────── //
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('s_date').setAttribute('min', today);
  document.getElementById('s_alt_date').setAttribute('min', today);
