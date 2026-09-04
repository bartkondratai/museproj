/**
 * Mokotown Music Academy — shared shell for the /szkola/ section.
 * Auth (staff/admin only), header + nav, toast, small helpers.
 */
import { supabase } from '/shared/supabase.js';
import { initAuth, getAuthState, signOut } from '/shared/auth.js';

export { supabase };

export const NAV = [
  { href: '/szkola/',                  label: 'Dziś',        key: 'dzis' },
  { href: '/szkola/leady.html',        label: 'Leady',       key: 'leady' },
  { href: '/szkola/nauczyciele.html',  label: 'Nauczyciele', key: 'nauczyciele' },
  { href: '/szkola/odwolania.html',    label: 'Odwołania',   key: 'odwolania' },
  { href: '/szkola/kalendarz.html',    label: 'Kalendarz',   key: 'kalendarz' },
];

export const LABELS = {
  lead_status: { nowy: 'Nowy', kontakt: 'W kontakcie', lekcja_probna: 'Lekcja próbna', zapisany: 'Zapisany', rezygnacja: 'Rezygnacja' },
  lead_source: { formularz: 'Formularz', quiz: 'Quiz „Jaki instrument”', telefon: 'Telefon', polecenie: 'Polecenie', social: 'Social media', inne: 'Inne' },
  cancel_status: { do_odrobienia: 'Do odrobienia', odrobiona: 'Odrobiona', zwrot: 'Zwrot', przepada: 'Przepada' },
  cancelled_by: { uczen: 'Uczeń', nauczyciel: 'Nauczyciel', szkola: 'Szkoła' },
  event_type: { wolne: 'Dzień wolny', ferie: 'Ferie / przerwa', koncert: 'Koncert', przesluchanie: 'Przesłuchanie', dzien_otwarty: 'Dzień otwarty', inne: 'Inne' },
  contract_type: { umowa_zlecenie: 'Umowa zlecenie', umowa_o_dzielo: 'Umowa o dzieło', b2b: 'B2B', inna: 'Inna' },
  settlement_status: { do_wyplaty: 'Do wypłaty', wyplacone: 'Wypłacone' },
};

const BADGE = {
  nowy: 'accent', kontakt: 'warn', lekcja_probna: 'warn', zapisany: 'ok', rezygnacja: 'danger',
  do_odrobienia: 'warn', odrobiona: 'ok', zwrot: '', przepada: 'danger',
  do_wyplaty: 'warn', wyplacone: 'ok',
  wolne: 'danger', ferie: 'danger', koncert: 'accent', przesluchanie: 'accent', dzien_otwarty: 'ok', inne: '',
};

/** Gate the page (staff/admin), render header. Resolves to auth state or null. */
export async function initSzkola(activeKey) {
  await initAuth();
  const state = getAuthState();
  if (!state.isAuthenticated) {
    window.location.href = '/login/?redirect=' + encodeURIComponent(window.location.pathname);
    return null;
  }
  if (!state.isStaff) {
    document.body.innerHTML = '<div class="mm-main"><div class="mm-card"><h2>Brak dostępu</h2><p>To konto nie ma uprawnień do sekcji Szkoła. Poproś dyrekcję o zaproszenie.</p><p><a href="/intranet/">Wróć do intranetu</a></p></div></div>';
    return null;
  }
  renderHeader(activeKey, state);
  return state;
}

function renderHeader(activeKey, state) {
  const target = document.getElementById('mmHeader');
  if (!target) return;
  const name = state.appUser?.display_name || state.user?.displayName || state.user?.email || '';
  target.innerHTML = `
    <header class="mm-header">
      <div class="mm-header__inner">
        <a class="mm-brand" href="/szkola/" title="Mokotown Music Academy — intranet">
          <img src="/assets/branding/mokotown/logo.svg" alt="Mokotown Music Academy" width="108" height="40">
          <span>intranet</span>
        </a>
        <nav class="mm-nav">
          ${NAV.map(n => `<a href="${n.href}" class="${n.key === activeKey ? 'active' : ''}">${n.label}</a>`).join('')}
          <a href="https://app.activenow.io" target="_blank" rel="noopener">ActiveNow ↗</a>
        </nav>
        <div class="mm-user">
          <span>${esc(name)}</span>
          <button type="button" id="mmSignOut">Wyloguj</button>
        </div>
      </div>
    </header>`;
  document.getElementById('mmSignOut')?.addEventListener('click', async () => {
    await signOut();
    window.location.href = '/login/';
  });
}

/* ---------- helpers ---------- */

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function badge(value, dict) {
  const cls = BADGE[value] ? ` mm-badge--${BADGE[value]}` : '';
  return `<span class="mm-badge${cls}">${esc(dict?.[value] ?? value ?? '')}</span>`;
}

export function options(dict, selected) {
  return Object.entries(dict).map(([v, l]) => `<option value="${v}" ${v === selected ? 'selected' : ''}>${esc(l)}</option>`).join('');
}

export function fmtDate(d) {
  if (!d) return '';
  const [y, m, day] = String(d).slice(0, 10).split('-');
  return `${day}.${m}.${y}`;
}

export function fmtMoney(n) {
  return new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'PLN', maximumFractionDigits: 2 }).format(Number(n || 0));
}

export function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function monthISO(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

export function monthLabel(period) {
  const [y, m] = period.split('-');
  const names = ['styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec', 'lipiec', 'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień'];
  return `${names[Number(m) - 1]} ${y}`;
}

export function formData(form) {
  const out = {};
  for (const [k, v] of new FormData(form).entries()) out[k] = typeof v === 'string' ? v.trim() : v;
  for (const el of form.querySelectorAll('input[type=checkbox][name]')) out[el.name] = el.checked;
  return out;
}

export function nullIfEmpty(v) { return v === '' || v === undefined ? null : v; }

let toastTimer;
export function toast(message, type = 'info') {
  let el = document.getElementById('mmToast');
  if (!el) { el = document.createElement('div'); el.id = 'mmToast'; document.body.appendChild(el); }
  el.className = `mm-toast${type === 'error' ? ' mm-toast--error' : type === 'ok' ? ' mm-toast--ok' : ''}`;
  el.textContent = message;
  requestAnimationFrame(() => el.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), type === 'error' ? 6000 : 3500);
}

/** Run a Supabase query, toast on error, return data (or null). */
export async function run(promise, okMessage) {
  const { data, error } = await promise;
  if (error) { console.error(error); toast(error.message || 'Błąd zapisu', 'error'); return null; }
  if (okMessage) toast(okMessage, 'ok');
  return data;
}

/** Cached list of teachers for selects. */
let teachersCache = null;
export async function loadTeachers(force = false) {
  if (teachersCache && !force) return teachersCache;
  const data = await run(supabase.from('teachers').select('id, name, is_active, rate_30, rate_45, rate_60').order('name'));
  teachersCache = data || [];
  return teachersCache;
}
