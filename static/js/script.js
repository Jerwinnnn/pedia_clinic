  let currentPage = 1;
  let selectedReason = '';
  let selectedVisit = '';

  function selectReason(val, id) {
    selectedReason = val;
    document.querySelectorAll('[id^="ro"]').forEach(el => el.classList.remove('selected'));
    document.getElementById(id).classList.add('selected');
  }

  function selectVisit(val, id) {
    selectedVisit = val;
    document.querySelectorAll('[id^="vt"]').forEach(el => el.classList.remove('selected'));
    document.getElementById(id).classList.add('selected');
  }

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
      if (i + 1 < n) s.classList.add('done');
    });
    currentPage = n;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function validate1() {
    let ok = true;
    const fields = [
      { id: 'g_fname', err: 'err_g_fname', check: v => v.trim() !== '' },
      { id: 'g_lname', err: 'err_g_lname', check: v => v.trim() !== '' },
      { id: 'g_relation', err: 'err_g_relation', check: v => v !== '' },
      { id: 'g_phone', err: 'err_g_phone', check: v => /^09\d{9}$/.test(v.trim()) },
    ];
    fields.forEach(f => {
      const el = document.getElementById(f.id);
      const err = document.getElementById(f.err);
      if (!f.check(el.value)) {
        el.classList.add('error'); err.classList.add('show'); ok = false;
      } else {
        el.classList.remove('error'); err.classList.remove('show');
      }
    });
    return ok;
  }

  function validate2() {
    let ok = true;
    const fields = [
      { id: 'c_fname', err: 'err_c_fname', check: v => v.trim() !== '' },
      { id: 'c_lname', err: 'err_c_lname', check: v => v.trim() !== '' },
      { id: 'c_dob',   err: 'err_c_dob',   check: v => v !== '' },
      { id: 'c_sex',   err: 'err_c_sex',   check: v => v !== '' },
    ];
    fields.forEach(f => {
      const el = document.getElementById(f.id);
      const err = document.getElementById(f.err);
      if (!f.check(el.value)) {
        el.classList.add('error'); err.classList.add('show'); ok = false;
      } else {
        el.classList.remove('error'); err.classList.remove('show');
      }
    });
    const rErr = document.getElementById('err_reason');
    if (!selectedReason) { rErr.classList.add('show'); ok = false; }
    else rErr.classList.remove('show');
    return ok;
  }

  function validate3() {
    let ok = true;
    const fields = [
      { id: 's_date', err: 'err_s_date', check: v => v !== '' },
      { id: 's_time', err: 'err_s_time', check: v => v !== '' },
    ];
    fields.forEach(f => {
      const el = document.getElementById(f.id);
      const err = document.getElementById(f.err);
      if (!f.check(el.value)) {
        el.classList.add('error'); err.classList.add('show'); ok = false;
      } else {
        el.classList.remove('error'); err.classList.remove('show');
      }
    });
    const vErr = document.getElementById('err_vtype');
    if (!selectedVisit) { vErr.classList.add('show'); ok = false; }
    else vErr.classList.remove('show');
    return ok;
  }

  function nextPage(n) {
    if (n === 1 && !validate1()) return;
    if (n === 2 && !validate2()) return;
    if (n === 3 && !validate3()) return;
    if (n === 3) buildSummary();
    showPage(n + 1);
  }

  function prevPage(n) { showPage(n - 1); }

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
      const res  = await fetch('/submit-appointment', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      const data = await res.json();

      if (data.success) {
        document.getElementById('ref-num').textContent = data.reference_number;
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.step').forEach(s => { s.classList.remove('active'); s.classList.add('done'); });
        document.getElementById('page5').classList.add('active');
      } else {
        alert('Error: ' + (data.error || 'Something went wrong. Please try again.'));
        btn.disabled = false;
        btn.textContent = 'Submit Appointment';
      }
    } catch (err) {
      alert('Network error. Please check your connection and try again.');
      btn.disabled = false;
      btn.textContent = 'Submit Appointment';
    }
  }

  // Set minimum date to today
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('s_date').setAttribute('min', today);
  document.getElementById('s_alt_date').setAttribute('min', today);
