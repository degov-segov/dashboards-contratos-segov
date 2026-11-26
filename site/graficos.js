/* Gráficos compartilhados pelos painéis (execução contratual e SIAFE).
   SVG/HTML puro, sem bibliotecas externas. Cada gráfico tem legenda com valores e dica ao passar o mouse. */
(function () {
  const R$ = v => (Number(v) || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const R$c = v => { // valor compacto para eixos e rótulos curtos
    const a = Math.abs(v);
    if (a >= 1e6) return 'R$ ' + (v / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' mi';
    if (a >= 1e3) return 'R$ ' + (v / 1e3).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + ' mil';
    return R$(v);
  };
  const P = v => (v == null || !isFinite(v)) ? '—' : (v * 100).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%';
  const HATCH = 'repeating-linear-gradient(135deg,#1f9d68 0 3px,#c9ecd9 3px 7px)';
  const fundo = s => s.hatch ? HATCH : s.cor;
  let nPadrao = 0;
  const H = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ---------- estilos ---------- */
  const css = `
  .g-tip { position:fixed; z-index:50; pointer-events:none; background:#10213d; color:#fff; font:12.5px/1.45 Inter,system-ui,sans-serif;
           padding:9px 12px; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,.18); max-width:320px; opacity:0; transition:opacity .08s; }
  .g-tip b { font-weight:700; } .g-tip .l { display:flex; align-items:center; gap:7px; justify-content:space-between; }
  .g-tip i { display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:6px; }
  .g-tip .t { font-weight:800; margin-bottom:4px; }
  .g-grid { display:grid; grid-template-columns:1fr 1fr 1.25fr; gap:16px; }
  .g-card { background:#fff; border:1px solid var(--line,#dfe7f1); border-radius:14px; padding:16px 18px; box-shadow:0 4px 14px rgba(29,54,88,.05); min-width:0; }
  .g-card h3 { font-size:13px; font-weight:800; color:var(--texto,#10213d); margin:0 0 2px; }
  .g-card .g-sub { font-size:11.5px; color:var(--muted,#66758a); margin-bottom:10px; }
  .g-donut { display:flex; align-items:center; gap:16px; }
  .g-donut svg { flex:0 0 136px; width:136px; height:136px; }
  .g-donut path { cursor:default; transition:opacity .1s; }
  .g-donut path:hover { opacity:.82; }
  .g-leg { list-style:none; margin:0; padding:0; flex:1; min-width:0; }
  .g-leg li { display:grid; grid-template-columns:12px 1fr auto; gap:8px; align-items:start; padding:5px 0; border-bottom:1px dashed #eef2f7; font-size:12.5px; }
  .g-leg li:last-child { border-bottom:0; }
  .g-leg i { width:12px; height:12px; border-radius:3px; margin-top:2px; }
  .g-leg .v { text-align:right; font-weight:700; font-variant-numeric:tabular-nums; color:var(--texto,#10213d); }
  .g-leg .v small { display:block; font-weight:500; color:var(--muted,#66758a); }
  .g-leg .sel { font-weight:800; }
  .g-hb .row { display:grid; grid-template-columns:minmax(150px,240px) 1fr 132px; gap:14px; align-items:center; padding:6px 4px; border-bottom:1px dashed #eef2f7; border-radius:6px; }
  .g-hb .row.clic { cursor:pointer; } .g-hb .row.clic:hover { background:#f5f8fc; }
  .g-hb .row:last-of-type { border-bottom:0; }
  .g-hb .nm { font-size:12.5px; line-height:1.3; min-width:0; }
  .g-hb .nm b { color:var(--navy,#0b2f63); } .g-hb .nm span { color:var(--muted,#66758a); }
  .g-hb .tr { height:20px; display:flex; gap:2px; background:#eef2f7; border-radius:5px; overflow:hidden; }
  .g-hb .tr div { height:100%; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; color:#fff; white-space:nowrap; overflow:hidden; }
  .g-hb .tr div.claro { color:#334155; }
  .g-hb .tr div:last-child { border-radius:0 4px 4px 0; }
  .g-hb .tt { text-align:right; font-size:12.5px; font-weight:700; font-variant-numeric:tabular-nums; }
  .g-hb .tt small { display:block; font-weight:500; color:var(--muted,#66758a); }
  .g-legh { display:flex; flex-wrap:wrap; gap:16px; font-size:12px; color:#4b5b70; margin-top:10px; }
  .g-legh span { display:inline-flex; align-items:center; gap:6px; } .g-legh i { width:12px; height:12px; border-radius:3px; display:inline-block; }
  .g-col svg { width:100%; height:auto; display:block; overflow:visible; }
  .g-col .bar { cursor:default; } .g-col .grupo:hover .bar { opacity:.85; }
  .g-col text { font:11px Inter,system-ui,sans-serif; fill:#66758a; }
  .g-col .vl { font-weight:700; fill:#33435a; }
  .g-al { list-style:none; margin:0; padding:0; max-height:250px; overflow:auto; }
  .g-al li { display:grid; grid-template-columns:22px 1fr; gap:8px; padding:8px 4px; border-bottom:1px dashed #eef2f7; font-size:12.5px; line-height:1.35; border-radius:6px; }
  .g-al li.clic { cursor:pointer; } .g-al li.clic:hover { background:#f5f8fc; }
  .g-al li:last-child { border-bottom:0; }
  .g-al .ic { width:20px; height:20px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:800; color:#fff; }
  .g-al .critico .ic { background:#b91c1c; } .g-al .atencao .ic { background:#b77900; } .g-al .ok .ic { background:#1f9d68; }
  .g-al .nv { font-size:10.5px; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }
  .g-al .critico .nv { color:#b91c1c; } .g-al .atencao .nv { color:#8a5a00; } .g-al .ok .nv { color:#17744d; }
  .g-al .tx { color:#33435a; }
  .g-vazio { color:var(--muted,#66758a); font-size:13px; padding:20px 0; text-align:center; }
  @media (max-width:1100px) { .g-grid { grid-template-columns:1fr; } .g-hb .row { grid-template-columns:1fr; gap:4px; } .g-hb .tt { text-align:left; } }
  `;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  /* ---------- dica (tooltip) ---------- */
  let tip;
  function dica(html, ev) {
    if (!tip) { tip = document.createElement('div'); tip.className = 'g-tip'; document.body.appendChild(tip); }
    if (!html) { tip.style.opacity = 0; return; }
    tip.innerHTML = html; tip.style.opacity = 1;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + w > innerWidth - 8) x = ev.clientX - w - 14;
    if (y + h > innerHeight - 8) y = ev.clientY - h - 14;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  function ligarDicas(raiz) {
    raiz.querySelectorAll('[data-tip]').forEach(el => {
      el.addEventListener('mousemove', ev => dica(decodeURIComponent(el.dataset.tip), ev));
      el.addEventListener('mouseleave', () => dica(null));
    });
  }
  const tipAttr = html => `data-tip="${encodeURIComponent(html)}"`;
  const linhaTip = (cor, rot, val) => `<div class="l"><span><i style="background:${cor}"></i>${H(rot)}</span><b>${val}</b></div>`;

  /* ---------- rosca ---------- */
  function donut(el, o) {
    const segs = o.segs.filter(s => s.v > 0), tot = segs.reduce((s, x) => s + x.v, 0);
    if (!tot) { el.innerHTML = '<div class="g-vazio">Sem valores para exibir.</div>'; return; }
    const R = 70, r = 46, cx = 75, cy = 75, gap = segs.length > 1 ? 0.012 : 0;
    let a0 = -Math.PI / 2;
    const pid = 'gh' + (++nPadrao);
    const defs = segs.some(s => s.hatch) ? `<defs><pattern id="${pid}" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" fill="#c9ecd9"/><rect width="3" height="7" fill="#1f9d68"/></pattern></defs>` : '';
    const arcos = segs.map(s => {
      const ang = s.v / tot * Math.PI * 2, a1 = a0 + ang;
      const ini = a0 + gap, fim = Math.max(ini + 0.0001, a1 - gap);
      const larg = fim - ini > Math.PI ? 1 : 0;
      const p = (rad, a) => `${(cx + rad * Math.cos(a)).toFixed(2)} ${(cy + rad * Math.sin(a)).toFixed(2)}`;
      const d = segs.length === 1
        ? `M ${cx} ${cy - R} A ${R} ${R} 0 1 1 ${cx - 0.01} ${cy - R} L ${cx - 0.01} ${cy - r} A ${r} ${r} 0 1 0 ${cx} ${cy - r} Z`
        : `M ${p(R, ini)} A ${R} ${R} 0 ${larg} 1 ${p(R, fim)} L ${p(r, fim)} A ${r} ${r} 0 ${larg} 0 ${p(r, ini)} Z`;
      a0 = a1;
      return `<path d="${d}" fill="${s.hatch ? `url(#${pid})` : s.cor}" ${tipAttr(`<div class="t">${H(s.rot)}</div>${R$(s.v)} · ${P(s.v / tot)} do total`)}></path>`;
    }).join('');
    el.innerHTML = `<div class="g-donut">
      <svg viewBox="0 0 150 150" role="img" aria-label="${H(o.titulo || 'Gráfico de rosca')}">${defs}${arcos}
        <text x="75" y="72" text-anchor="middle" style="font:800 14px Inter,system-ui,sans-serif;fill:#10213d">${H(o.centro || R$c(tot))}</text>
        <text x="75" y="89" text-anchor="middle" style="font:11px Inter,system-ui,sans-serif;fill:#66758a">${H(o.centroSub || 'total')}</text></svg>
      <ul class="g-leg">${segs.map(s => `<li class="${s.destaque ? 'sel' : ''}"><i style="background:${fundo(s)}"></i><span>${H(s.rot)}</span>
        <span class="v">${R$(s.v)}<small>${P(s.v / tot)}</small></span></li>`).join('')}</ul></div>`;
    ligarDicas(el);
  }

  /* ---------- barras horizontais empilhadas (cada barra = 100% do total da linha) ---------- */
  function barras100(el, o) {
    if (!o.linhas.length) { el.innerHTML = '<div class="g-vazio">Sem contratos para exibir.</div>'; return; }
    el.classList.add('g-hb');
    el.innerHTML = o.linhas.map((l, i) => {
      const base = l.base || l.segs.reduce((s, x) => s + Math.max(0, x.v), 0);
      const tipHtml = `<div class="t">${H(l.rot)}</div>` + l.segs.map(s => linhaTip(fundo(s), s.rot, `${R$(s.v)} · ${P(base ? s.v / base : null)}`)).join('') +
        `<div class="l" style="margin-top:4px;border-top:1px solid #2c3e5c;padding-top:4px"><span>${H(o.rotTotal || 'Total')}</span><b>${R$(base)}</b></div>`;
      const segs = l.segs.filter(s => s.v > 0).map(s => {
        const w = base ? s.v / base * 100 : 0;
        return `<div class="${s.claro || s.hatch ? 'claro' : ''}" style="width:${w}%;background:${fundo(s)}">${w >= 13 ? P(s.v / base) : ''}</div>`;
      }).join('');
      return `<div class="row ${l.onclick ? 'clic' : ''}" data-i="${i}" ${tipAttr(tipHtml)}>
        <div class="nm"><b>${H(l.rot)}</b>${l.sub ? ` <span>· ${H(l.sub)}</span>` : ''}</div>
        <div class="tr">${segs}</div><div class="tt">${R$c(base)}<small>${H(l.nota || '')}</small></div></div>`;
    }).join('') + `<div class="g-legh">${o.legenda.map(s => `<span><i style="background:${fundo(s)}"></i>${H(s.rot)}</span>`).join('')}</div>`;
    el.querySelectorAll('.row.clic').forEach(r => r.addEventListener('click', () => { dica(null); o.linhas[+r.dataset.i].onclick(); }));
    ligarDicas(el);
  }

  /* ---------- barras horizontais simples (ranking) ---------- */
  function ranking(el, o) {
    const max = Math.max(...o.linhas.map(l => l.v), 0);
    if (!max) { el.innerHTML = '<div class="g-vazio">Sem valores para exibir.</div>'; return; }
    const tot = o.linhas.reduce((s, l) => s + l.v, 0);
    el.classList.add('g-hb');
    el.innerHTML = o.linhas.map(l => `<div class="row" ${tipAttr(`<div class="t">${H(l.rot)}</div>${R$(l.v)} · ${P(l.v / tot)} do total`)}>
      <div class="nm"><b>${H(l.rot)}</b>${l.sub ? ` <span>· ${H(l.sub)}</span>` : ''}</div>
      <div class="tr" style="background:transparent"><div style="width:${l.v / max * 100}%;background:${o.cor};border-radius:0 4px 4px 0"></div></div>
      <div class="tt">${R$(l.v)}<small>${P(l.v / tot)}</small></div></div>`).join('');
    ligarDicas(el);
  }

  /* ---------- colunas empilhadas por mês ---------- */
  function colunas(el, o) {
    const cats = o.cats, n = cats.length;
    if (!n) { el.innerHTML = '<div class="g-vazio">Sem pagamentos com mês de referência identificado.</div>'; return; }
    const tots = cats.map((_, i) => o.series.reduce((s, x) => s + (x.vals[i] || 0), 0));
    const max = Math.max(...tots, 1);
    const passo = Math.pow(10, Math.floor(Math.log10(max))), mult = [1, 2, 2.5, 5, 10].find(m => m * passo * 4 >= max) || 10;
    const topo = mult * passo * 4, ticks = [0, 1, 2, 3, 4].map(k => k * mult * passo);
    const W = 1150, Hh = 250, ml = 70, mr = 12, mt = 18, mb = 34, pw = W - ml - mr, ph = Hh - mt - mb;
    const bw = Math.min(46, pw / n * 0.62), x = i => ml + pw / n * (i + 0.5), y = v => mt + ph - v / topo * ph;
    let acum = 0;
    const grade = ticks.map(t => `<line x1="${ml}" x2="${W - mr}" y1="${y(t)}" y2="${y(t)}" stroke="#e8edf4" stroke-width="1"/>
      <text x="${ml - 8}" y="${y(t) + 4}" text-anchor="end">${R$c(t)}</text>`).join('');
    const grupos = cats.map((c, i) => {
      acum += tots[i];
      let base = 0;
      const vis = o.series.filter(s => (s.vals[i] || 0) > 0);
      const rects = vis.map((s, k) => {
        const v = s.vals[i], y0 = y(base + v), hgt = Math.max(1, y(base) - y(base + v) - (k < vis.length - 1 ? 2 : 0));
        base += v;
        const topoSeg = k === vis.length - 1;
        const r = topoSeg ? Math.min(4, hgt / 2) : 0;
        const xL = x(i) - bw / 2;
        const d = r ? `M ${xL} ${y0 + hgt} V ${y0 + r} Q ${xL} ${y0} ${xL + r} ${y0} H ${xL + bw - r} Q ${xL + bw} ${y0} ${xL + bw} ${y0 + r} V ${y0 + hgt} Z`
                    : `M ${xL} ${y0 + hgt} V ${y0} H ${xL + bw} V ${y0 + hgt} Z`;
        return `<path class="bar" d="${d}" fill="${s.cor}"/>`;
      }).join('');
      const tipHtml = `<div class="t">${H(c)}</div>` + o.series.filter(s => s.vals[i]).map(s => linhaTip(s.cor, s.rot, R$(s.vals[i]))).join('') +
        `<div class="l" style="margin-top:4px;border-top:1px solid #2c3e5c;padding-top:4px"><span>Total do mês</span><b>${R$(tots[i])}</b></div>` +
        `<div class="l"><span>Acumulado no ano</span><b>${R$(acum)}</b></div>`;
      return `<g class="grupo" ${tipAttr(tipHtml)}><rect x="${x(i) - pw / n / 2}" y="${mt}" width="${pw / n}" height="${ph}" fill="transparent"/>${rects}
        ${tots[i] ? `<text class="vl" x="${x(i)}" y="${y(tots[i]) - 5}" text-anchor="middle">${R$c(tots[i])}</text>` : ''}
        <text x="${x(i)}" y="${Hh - mb + 18}" text-anchor="middle">${H(c)}</text></g>`;
    }).join('');
    el.classList.add('g-col');
    el.innerHTML = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${H(o.titulo || 'Colunas por mês')}">${grade}
      <line x1="${ml}" x2="${W - mr}" y1="${y(0)}" y2="${y(0)}" stroke="#c9d3e0"/>${grupos}</svg>
      <div class="g-legh">${o.series.filter(s => s.vals.some(v => v)).map(s => `<span><i style="background:${s.cor}"></i>${H(s.rot)}</span>`).join('')}${o.nota ? `<span style="color:#66758a">${H(o.nota)}</span>` : ''}</div>`;
    ligarDicas(el);
  }

  /* ---------- semáforo de alertas ---------- */
  function alertas(el, itens, vazio) {
    const ordem = { critico: 0, atencao: 1, ok: 2 }, rot = { critico: 'Crítico', atencao: 'Atenção', ok: 'Em dia' }, ic = { critico: '!', atencao: '!', ok: '✓' };
    itens = itens.slice().sort((a, b) => ordem[a.nivel] - ordem[b.nivel]);
    if (!itens.length) itens = [{ nivel: 'ok', titulo: vazio || 'Nenhum alerta', texto: '' }];
    el.innerHTML = `<ul class="g-al">${itens.map((a, i) => `<li class="${a.nivel} ${a.onclick ? 'clic' : ''}" data-i="${i}">
      <span class="ic" aria-hidden="true">${ic[a.nivel]}</span>
      <div><span class="nv">${rot[a.nivel]}</span> · <b>${H(a.titulo)}</b><div class="tx">${H(a.texto)}</div></div></li>`).join('')}</ul>`;
    el.querySelectorAll('li.clic').forEach(li => li.addEventListener('click', () => itens[+li.dataset.i].onclick()));
  }

  /* ---------- mês de referência a partir de texto ("Janeiro/2026", "Diárias — Jan a Mar/2026") ---------- */
  const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  function mesRef(txt) {
    if (!txt) return null;
    const t = String(txt).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const m = t.match(/\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*\b/);
    if (!m) return null;
    const a = t.match(/(20\d\d)/);
    return { mes: MESES.indexOf(m[1]), ano: a ? +a[1] : null };
  }
  const rotMes = (m, a) => MESES[m][0].toUpperCase() + MESES[m].slice(1) + (a ? '/' + String(a).slice(2) : '');

  window.G = { HATCH, donut, barras100, ranking, colunas, alertas, mesRef, rotMes, R$c };
})();
