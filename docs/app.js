const $ = id => document.getElementById(id) || document.createElement('div');
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const j = async u => (await fetch(u + (u.includes('?') ? '&' : '?') + 't=' + Date.now())).json();
const fmt = s => new Date(s + 'T00:00:00').toLocaleDateString('en-US', {weekday:'short', month:'short', day:'numeric'});
const pat = s => String(s || '').replace(/^\d+-/, '').replace(/-/g, ' ');
const GLYPH = {gold:'★', silver:'◆', bronze:'●', none:'✕', frozen:'❄', live:'▶'};
const DEMO = new URLSearchParams(location.search).has('demo');
let CF, P, sel = null;

function theme(name) {
  const t = CF.themes[name] || CF.themes[CF.default_theme];
  for (const [k, v] of Object.entries(t)) document.documentElement.style.setProperty('--' + k, v);
  try { localStorage.setItem('theme', name); } catch (e) {}
  document.documentElement.dataset.theme = name;
  if (P) { hero(); }
}
const curTheme = () => document.documentElement.dataset.theme;

/* ---------- starfield ---------- */
function stars() {
  const c = $('stars'), x = c.getContext('2d'); let S = [];
  const size = () => { c.width = innerWidth; c.height = innerHeight; S = Array.from({length: Math.floor(innerWidth * innerHeight / 9000)}, () => ({x: Math.random() * c.width | 0, y: Math.random() * c.height | 0, s: Math.random() < .2 ? 4 : 2, p: Math.random()})); };
  size(); addEventListener('resize', size);
  const draw = () => { x.clearRect(0, 0, c.width, c.height); x.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--star'); S.forEach(s => { x.globalAlpha = (Math.random() < .03 ? s.p = Math.random() : s.p) * (curTheme() === 'sunrise' ? .35 : .8); x.fillRect(s.x, s.y, s.s, s.s); }); };
  draw(); if (!matchMedia('(prefers-reduced-motion: reduce)').matches) setInterval(draw, 500);
}

/* ---------- hero (procedural 16x16, mood + level aware) ---------- */
function mood() {
  if (!P.started || P.finished) return 'sleep';
  const d = P.today.done, t = P.today.targets;
  const req = (d.dsa || 0) >= 1 && (d.learn || 0) >= 1;
  if (req) return 'party';
  if (P.streak_at_risk) return 'worried';
  return 'happy';
}
function hero() {
  const c = $('hero'), x = c.getContext('2d'), css = k => getComputedStyle(document.documentElement).getPropertyValue('--' + k).trim();
  const m = mood(), lv = P.level;
  x.clearRect(0, 0, 16, 16);
  const R = (col, X, Y, w = 1, h = 1) => { x.fillStyle = col; x.fillRect(X, Y, w, h); };
  const hat = ['#ff4fd8', '#ff9f1c', '#ffd23f', '#b6ff3b', '#2de2e6', '#8a5cff'][Math.min((lv - 1) >> 1, 5)];
  const skin = '#f7c59f', dark = '#1a1033', shirt = css('a2'), pants = '#3b2f8f';
  if (lv >= 3) { R(css('a1'), 3, 7, 1, 5); R(css('a1'), 12, 7, 1, 5); }          // cape
  R(hat, 5, 1, 6, 2); R(hat, 4, 3, 8, 1);                                         // hat
  if (lv >= 7) { R(css('gold'), 5, 0, 1, 1); R(css('gold'), 8, 0, 1, 1); R(css('gold'), 10, 0, 1, 1); }
  R(skin, 5, 4, 6, 4);                                                            // head
  if (m === 'sleep') { R(dark, 6, 5, 2, 1); R(dark, 9, 5, 2, 1); R(dark, 8, 7, 1, 1); }
  else if (m === 'worried') { R(dark, 6, 5); R(dark, 9, 5); R(dark, 7, 7, 2, 1); R('#5ab0ff', 10, 6); }
  else if (m === 'party') { R(dark, 6, 5, 1, 1); R(dark, 9, 5, 1, 1); R(dark, 7, 7, 3, 1); R(dark, 6, 6); R(dark, 10, 6); }
  else { R(dark, 6, 5); R(dark, 9, 5); R(dark, 7, 7, 2, 1); }
  R(shirt, 4, 8, 8, 4);                                                           // body
  R(css('gold'), 7, 9, 2, 1);                                                     // belt buckle/emblem
  if (m === 'party') { R(skin, 3, 6, 1, 3); R(skin, 12, 6, 1, 3); R(css('gold'), 2, 4); R(css('gold'), 13, 3); R(css('a1'), 1, 6); R(css('a3'), 14, 5); }
  else { R(skin, 3, 9, 1, 3); R(skin, 12, 9, 1, 3); }
  R(pants, 5, 12, 2, 3); R(pants, 9, 12, 2, 3); R(dark, 5, 15, 2, 1); R(dark, 9, 15, 2, 1);
  $('herowrap').className = 'herowrap ' + m;
}

/* ---------- sections ---------- */
function coach() {
  const d = P.today.done, t = P.today.targets;
  if (P.finished) return '90 days. DONE. Look at everything you built.';
  if (!P.started) return `Day 1 starts ${fmt(P.start)}. Get lets-dsa open. Be ready!`;
  const need = k => Math.max((t[k] || 1) - (d[k] || 0), 0), req = (d.dsa >= 1) && (d.learn >= 1);
  if (req && d.tech) return `PERFECT DAY! Streak ${P.streak} locked in. Go rest, champ.`;
  if (req) return `Streak safe! Read the digest to hit silver.`;
  const left = []; if (need('dsa')) left.push(need('dsa') + ' DSA'); if (need('learn')) left.push(need('learn') + ' learn entry');
  if (P.streak_at_risk) return `${P.streak}-day streak on the line! ${left.join(' + ')} to save it.`;
  return `Today's mission: ${left.join(' + ')}. You've got this.`;
}
function hud() {
  $('title').textContent = CF.title; $('tag').textContent = CF.tagline; document.title = CF.title;
  $('bubble').textContent = coach();
  const day = P.started ? `${Math.min(P.day_number, P.total_days)}<small style="font-size:.6em">/${P.total_days}</small>` : 'SOON';
  $('stats').innerHTML = [
    ['DAY', day, ''], ['STREAK', (P.streak > 0 ? '<span class="flame">🔥</span>' : '') + P.streak, P.streak > 0 ? 'hot' : ''],
    ['BEST', P.best_streak, ''], ['GOLD DAYS', P.metrics.gold_days, '']
  ].map(([l, v, c]) => `<div class="stat ${c}"><b>${v}</b><span>${l}</span></div>`).join('');
  const into = P.xp % P.level_every; $('xpfill').style.width = (into / P.level_every * 100) + '%';
  $('lvl').textContent = 'LEVEL ' + P.level; $('xpn').textContent = `${into}/${P.level_every} XP to level ${P.level + 1}`;
}
function quests() {
  const t = P.today, L = [['dsa', '⚔️', 'DSA problem', 'wig'], ['learn', '🧠', 'Learn with Claude', 'bob'], ['tech', '📰', 'Read the digest', 'flip']];
  $('quests').innerHTML = L.map(([k, ic, lb, an]) => {
    const need = t.targets[k] ?? 1, d = t.done[k] || 0, ok = d >= need && P.started;
    return `<div class="qr ${ok ? 'done' : ''}"><span><b class="qi ${an}">${ic}</b> ${ok ? '■' : '□'} ${lb}</span><span class="qn">${d}/${need}</span></div>`;
  }).join('');
  $('daytype').textContent = P.started ? t.type.replace('_', ' ') + ' day' : '';
  const req = (t.done.dsa >= 1) && (t.done.learn >= 1);
  $('dayline').textContent = !P.started ? 'The clock starts on Day 1.' : (req ? (t.done.tech ? '★ GOLD-tier day in progress.' : 'Streak secured. Read the digest for silver.') : 'Do DSA + learn to keep the streak alive. Read the digest for bonus XP.');
}
function dsa() {
  const d = P.dsa, n = d.goal; $('dsaBig').textContent = `${d.solved}/${n}`;
  $('dsaPct').textContent = `${Math.round(d.solved / n * 100)}% of the way`;
  $('goalfill').style.width = Math.min(100, d.solved / n * 100) + '%';
  $('pacemark').style.left = Math.min(100, d.ideal_by_today / n * 100) + '%';
  $('pacemark').style.display = P.started ? '' : 'none';
  const ahead = d.ahead_by;
  $('pace').innerHTML = !P.started ? 'Goal: <b>100</b> by Dec 31. That is about 1.1 a day.' :
    `${ahead >= 0 ? 'Ahead of' : 'Behind'} plan by <b>${Math.abs(ahead)}</b> (marker = where you should be). Need <b>${d.needed_per_day}</b>/day to hit 100 by Dec 31.`;
}
let extraWeeks = 0, selDay = null;
// After tapping a day, scroll toward the bottom of the page so the details AND the achievements below
// come into view, but never so far that the top of the details panel leaves the screen.
function scrollToDetail() {
  const behavior = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    const d = $('detail').getBoundingClientRect();
    const pageBottom = document.documentElement.scrollHeight - innerHeight;
    const top = Math.min(pageBottom, scrollY + d.top - 16);
    if (top > scrollY + 1) scrollTo({top, behavior});
  }));
}
function calendar() {
  const start = new Date(P.start + 'T00:00:00'), off = (start.getDay() + 6) % 7, byDay = Object.fromEntries(P.days.map(x => [x.day, x]));
  // only show weeks that have started; the + button reveals the future a week at a time
  const cur = P.started ? Math.min(P.day_number, P.total_days) : 1;
  const weekEnd = cur + (6 - ((off + cur - 1) % 7)), shownTo = Math.min(P.total_days, weekEnd + 7 * extraWeeks);
  let h = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'].map(x => `<div class="dow">${x}</div>`).join('');
  for (let i = 0; i < off; i++) h += '<div class="tile empty"></div>';
  for (let i = 1; i <= shownTo; i++) {
    const r = byDay[i], isToday = P.started && i === P.day_number, live = isToday && r && r.rating === 'none', rating = live ? 'live' : (r ? r.rating : ''), fut = !r && !isToday;
    const ms = CF.milestones[i] ? `<span class="ms">${CF.milestones[i]}</span>` : '';
    const pips = P.solved.filter(x => x.date === dayDate(i)).map(x => `<b class="pip ${esc(x.difficulty)}"></b>`).join('');
    h += `<button class="tile ${rating} ${isToday ? 'today' : ''} ${fut ? 'future' : ''}" data-day="${i}" aria-label="Day ${i}"><span class="d">${i}</span><span class="g">${GLYPH[rating] || ''}</span><span class="pips">${pips}</span>${ms}</button>`;
  }
  $('cal').innerHTML = h;
  const left = P.total_days - shownTo;
  $('calmore').innerHTML = left > 0 ? `<button class="more" id="more">+ NEXT WEEK <small>${left} days still ahead</small></button>` : '';
  if (left > 0) $('more').onclick = () => { extraWeeks++; calendar(); };
  $('cal').onclick = e => {
    const b = e.target.closest('.tile[data-day]');
    if (b && !b.classList.contains('future')) {
      showDay(+b.dataset.day);
      scrollToDetail();
    }
  };
  showDay(selDay ?? (P.started ? Math.min(P.day_number, P.total_days) : null));
}
function dayDate(n) { const d = new Date(P.start + 'T00:00:00'); d.setDate(d.getDate() + n - 1); return d.toLocaleDateString('en-CA'); }
function itemsFor(date) {
  return { solved: P.solved.filter(s => s.date === date), learned: P.learning.filter(l => l.date === date) };
}
function showDay(n) {
  selDay = n;
  document.querySelectorAll('.tile.sel').forEach(t => t.classList.remove('sel'));
  if (n == null) { $('detail').innerHTML = '<div class="empty-note">Tap a day once the challenge starts.</div>'; return; }
  const t = document.querySelector(`.tile[data-day="${n}"]`); t && t.classList.add('sel');
  const date = dayDate(n), r = P.days.find(x => x.day === n), it = itemsFor(date);
  const lines = [];
  it.solved.forEach(s => lines.push(`<div><span class="chip ${esc(s.difficulty)}">${esc(s.difficulty)}</span>Solved <b>${esc(s.title)}</b> <span style="color:var(--dim)">(${esc(pat(s.pattern))})</span></div>`));
  it.learned.forEach(l => lines.push(`<div><span class="chip t">${esc(l.tag || 'learn')}</span>${esc(l.topic)}${l.takeaway ? ' <span style="color:var(--dim)">- ' + esc(l.takeaway) + '</span>' : ''}</div>`));
  if (r && r.done.tech) lines.push('<div><span class="chip t">read</span>Read the digest</div>');
  const live = r && n === P.day_number && r.rating === 'none';
  const head = `DAY ${n} · ${fmt(date)} · ${live ? 'IN PROGRESS' : (r ? r.rating.toUpperCase() : 'UPCOMING')}${r ? ' · ' + r.type.replace('_', ' ') : ''}`;
  $('detail').innerHTML = `<h4>${head}</h4>` + (lines.length ? lines.join('') : `<div style="color:var(--dim)">${r ? (live || r.rating !== 'none' ? 'Nothing logged yet. Go make it count.' : 'Nothing logged. Tomorrow is the comeback.') : 'Not here yet.'}</div>`);
}
function badges() {
  const B = P.badges, got = B.filter(b => b.earned).length; $('bcount').textContent = `${got}/${B.length} unlocked`;
  const nxt = B.filter(b => !b.earned).sort((a, b) => b.cur / b.target - a.cur / a.target).slice(0, 3);
  $('next').innerHTML = nxt.length ? nxt.map(b => `<div class="nb"><div class="gl">${CF.glyph[b.id] || '★'}</div><div><div class="t"><span>${esc(b.name)} <span style="color:var(--dim)">- ${esc(b.desc)}</span></span><span>${b.cur}/${b.target}</span></div><div class="bar"><div class="fill" style="width:${b.cur / b.target * 100}%"></div></div></div></div>`).join('') : '<div class="empty-note">All badges unlocked. Legend.</div>';
  $('badges').innerHTML = B.map(b => `<div class="badge ${b.earned ? 'earned' : 'locked'}" title="${esc(b.desc)}"><div class="gl">${CF.glyph[b.id] || '★'}</div>${esc(b.name)}</div>`).join('');
}
/* ---------- confetti ---------- */
function confetti() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const c = $('confetti'), x = c.getContext('2d'); c.width = innerWidth; c.height = innerHeight;
  const cols = ['--a1', '--a2', '--gold', '--silver'].map(k => getComputedStyle(document.documentElement).getPropertyValue(k).trim());
  const ps = Array.from({length: 90}, () => ({x: innerWidth / 2 + (Math.random() - .5) * 200, y: innerHeight * .35, vx: (Math.random() - .5) * 12, vy: -Math.random() * 12 - 4, s: 6 + (Math.random() * 6 | 0), c: cols[Math.random() * cols.length | 0]}));
  let f = 0; (function step() { x.clearRect(0, 0, c.width, c.height); ps.forEach(p => { p.x += p.vx; p.y += p.vy; p.vy += .5; x.fillStyle = p.c; x.fillRect(p.x | 0, p.y | 0, p.s, p.s); }); if (++f < 110) requestAnimationFrame(step); else x.clearRect(0, 0, c.width, c.height); })();
}

/* ---------- boot ---------- */
(async () => {
  try {
    [CF, P] = await Promise.all([j('config.json'), j(DEMO ? 'demo.json' : 'public.json')]);
    let saved = null; try { saved = localStorage.getItem('theme'); } catch (e) {}
    theme(saved && CF.themes[saved] ? saved : CF.default_theme);
    $('themeBtn').onclick = () => { const names = Object.keys(CF.themes); theme(names[(names.indexOf(curTheme()) + 1) % names.length]); };
    stars(); hero(); hud(); quests(); dsa(); calendar(); badges();
    $('foot').textContent = (DEMO ? 'DEMO DATA · ' : '') + 'updated ' + P.generated.replace('T', ' ').slice(0, 16) + ' IST';
    const d = P.today.done; if (P.started && d.dsa >= 1 && d.learn >= 1) setTimeout(confetti, 500);
  } catch (e) { document.body.insertAdjacentHTML('beforeend', '<p style="position:relative;padding:20px">Could not load data: ' + esc(e.message) + '</p>'); }
})();
