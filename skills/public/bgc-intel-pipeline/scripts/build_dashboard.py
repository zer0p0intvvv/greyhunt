#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 4 / 可视化 (visualization)

输入：analyze.py 产出的 analysis.json
输出：自包含离线 HTML 情报看板（数据内嵌，无需联网，无 CDN 依赖）。

用法：
  python build_dashboard.py analysis.json -o dashboard.html
"""
import argparse
import json
import html


def build(analysis):
    data_json = json.dumps(analysis, ensure_ascii=False)
    # 仅做转义嵌入；所有渲染在前端 JS 完成，便于交互筛选。
    return TEMPLATE.replace("/*__DATA__*/", data_json)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>黑灰产情报看板</title>
<style>
  :root{
    --bg:#13141a; --panel:#1b1d26; --panel2:#22242f; --line:#2c2f3d;
    --ink:#e8e6df; --muted:#8b8fa0; --faint:#5d6172;
    --signal:#e8843c;      /* 风险信号橙 */
    --signal-hi:#ff5a4d;   /* 高危红 */
    --data:#5fb6c9;        /* 数据青 */
    --ok:#7fae6b;
    --mono:'SFMono-Regular',ui-monospace,'JetBrains Mono','Menlo',monospace;
    --sans:'Inter','Helvetica Neue','PingFang SC','Microsoft YaHei',sans-serif;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
       font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1180px;margin:0 auto;padding:32px 24px 80px}
  header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:28px}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.22em;
           text-transform:uppercase;color:var(--signal)}
  h1{font-size:27px;font-weight:650;margin:8px 0 4px;letter-spacing:-.01em}
  .sub{color:var(--faint);font-family:var(--mono);font-size:12px}
  .grid{display:grid;gap:16px}
  .kpis{grid-template-columns:repeat(5,1fr);margin-bottom:28px}
  @media(max-width:880px){.kpis{grid-template-columns:repeat(2,1fr)}}
  .kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 16px 14px;position:relative;overflow:hidden}
  .kpi .n{font-family:var(--mono);font-size:30px;font-weight:600;line-height:1}
  .kpi .l{color:var(--faint);font-size:12px;margin-top:8px}
  .kpi.hot .n{color:var(--signal-hi)}
  .kpi.warn .n{color:var(--signal)}
  .kpi.data .n{color:var(--data)}
  .cols{grid-template-columns:1fr 1fr;align-items:start}
  @media(max-width:880px){.cols{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 18px 20px}
  .card h2{font-size:13px;font-weight:600;letter-spacing:.04em;margin:0 0 16px;
           color:var(--ink);display:flex;align-items:center;gap:8px}
  .card h2 .tag{font-family:var(--mono);font-size:10px;color:var(--faint);
                border:1px solid var(--line);border-radius:4px;padding:1px 6px;letter-spacing:.1em}
  /* bar chart */
  .bar-row{display:grid;grid-template-columns:120px 1fr 42px;align-items:center;gap:10px;margin-bottom:9px}
  .bar-row .k{font-size:12.5px;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .bar-track{height:9px;background:var(--panel2);border-radius:5px;overflow:hidden}
  .bar-fill{height:100%;border-radius:5px;background:linear-gradient(90deg,var(--data),#7fd0e0)}
  .bar-fill.sig{background:linear-gradient(90deg,var(--signal),#ffae6e)}
  .bar-row .v{font-family:var(--mono);font-size:12px;color:var(--faint);text-align:right}
  /* risk donut text */
  .riskbox{display:flex;gap:18px;flex-wrap:wrap}
  .riskpill{flex:1;min-width:90px;text-align:center;background:var(--panel2);border-radius:8px;padding:14px 8px}
  .riskpill .n{font-family:var(--mono);font-size:24px;font-weight:600}
  .riskpill .l{font-size:11px;color:var(--faint);margin-top:5px}
  .riskpill.hi .n{color:var(--signal-hi)} .riskpill.mid .n{color:var(--signal)} .riskpill.lo .n{color:var(--ok)}
  /* table / records */
  .toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0 16px}
  .toolbar input,.toolbar select{background:var(--panel);border:1px solid var(--line);color:var(--ink);
      border-radius:7px;padding:8px 10px;font-size:13px;font-family:var(--sans)}
  .toolbar input{flex:1;min-width:160px}
  .rec{border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:12px;background:var(--panel)}
  .rec-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px}
  .rec-title{font-weight:600;font-size:14.5px}
  .rec-meta{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:3px}
  .risk-badge{font-family:var(--mono);font-weight:600;font-size:13px;padding:4px 10px;border-radius:6px;white-space:nowrap}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
  .chip{font-size:11px;padding:2px 8px;border-radius:5px;background:var(--panel2);color:var(--muted);border:1px solid var(--line)}
  .chip.cat{color:#ffc89a;border-color:#5a4530}
  .chip.plat{color:var(--data);border-color:#2d4a52}
  .chip.tag{color:var(--signal-hi);border-color:#5a3030}
  .rec-body{margin-top:10px;font-size:12.5px;color:var(--muted);display:none}
  .rec.open .rec-body{display:block}
  .rec-body .row{margin:6px 0}
  .rec-body .lab{color:var(--faint);font-family:var(--mono);font-size:11px;margin-right:8px;text-transform:uppercase;letter-spacing:.06em}
  .quote{border-left:2px solid var(--line);padding-left:10px;margin:4px 0;color:var(--muted)}
  .more{cursor:pointer;color:var(--data);font-size:11px;font-family:var(--mono);margin-top:8px;display:inline-block}
  a{color:var(--data);text-decoration:none} a:hover{text-decoration:underline}
  /* gangs */
  .gang{border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:10px;background:var(--panel)}
  .gang-head{display:flex;justify-content:space-between;gap:10px;align-items:center}
  .gang-id{font-family:var(--mono);color:var(--signal);font-weight:600}
  .gang-meta{font-size:12px;color:var(--muted);margin-top:6px}
  .section-title{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;
                 color:var(--faint);margin:38px 0 14px;border-bottom:1px solid var(--line);padding-bottom:8px}
  footer{margin-top:50px;color:var(--faint);font-family:var(--mono);font-size:11px;text-align:center}
  /* overview 数据全貌 */
  .overview{margin:6px 0 40px}
  .ov-head{text-align:center;margin:8px 0 28px}
  .ov-head h2{font-size:34px;font-weight:750;letter-spacing:-.02em;margin:0;color:#f5f4ef}
  .ov-head .ov-sub{color:var(--muted);font-size:14px;margin-top:9px}
  .ov-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
  @media(max-width:880px){.ov-grid{grid-template-columns:1fr}}
  .ov-card{background:linear-gradient(180deg,#181a22,#15161d);border:1px solid var(--line);
           border-radius:16px;padding:22px 22px 20px;min-height:148px;
           opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease}
  .overview.in .ov-card{opacity:1;transform:none}
  .ov-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
  .ov-ico{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex:none}
  .ov-ico svg{width:22px;height:22px}
  .ov-num{display:flex;align-items:baseline;gap:6px;font-family:var(--mono);font-weight:700;
          font-size:40px;line-height:1;color:#fff;letter-spacing:-.02em}
  .ov-num .suf{font-family:var(--sans);font-size:15px;font-weight:600}
  .ov-num .arrow{font-size:17px;font-weight:700;margin-left:1px}
  .ov-title{font-size:16px;font-weight:650;margin-top:18px;color:var(--ink)}
  .ov-desc{font-size:12.5px;color:var(--faint);margin-top:7px;line-height:1.55}
  /* jargon seeds */
  .seedwrap{display:flex;flex-wrap:wrap;gap:8px}
  .seed{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;padding:5px 10px;border-radius:6px;
        background:var(--panel2);border:1px solid var(--line);color:var(--ink);cursor:default}
  .seed .ct{font-family:var(--mono);font-size:11px;color:var(--signal)}
  .seed.cat{border-color:#5a4530}
  .copybtn{margin-left:auto;font-family:var(--mono);font-size:11px;letter-spacing:.06em;cursor:pointer;
           background:var(--panel2);border:1px solid var(--line);color:var(--data);border-radius:6px;padding:4px 10px}
  .copybtn:hover{border-color:var(--data)}
  .copybtn.done{color:var(--ok);border-color:var(--ok)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">BLACK &amp; GRAY MARKET · THREAT INTEL</div>
    <h1>黑灰产情报看板</h1>
    <div class="sub" id="subline"></div>
  </header>

  <section class="overview" id="overview">
    <div class="ov-head">
      <h2>数据全貌</h2>
      <div class="ov-sub">从零爬取到团伙挖掘 · 端到端闭环</div>
    </div>
    <div class="ov-grid" id="ovgrid"></div>
  </section>

  <div class="grid cols">
    <div class="card">
      <h2>业务类目分布 <span class="tag">CATEGORY</span></h2>
      <div id="cat"></div>
    </div>
    <div class="card">
      <h2>目标平台 <span class="tag">PLATFORM</span></h2>
      <div id="plat"></div>
    </div>
  </div>

  <div class="grid cols" style="margin-top:16px">
    <div class="card">
      <h2>风险分布 <span class="tag">RISK</span></h2>
      <div class="riskbox" id="risk"></div>
    </div>
    <div class="card">
      <h2>属地来源 TOP <span class="tag">IP</span></h2>
      <div id="ip"></div>
    </div>
  </div>

  <div class="section-title">黑话词库 / 搜索种子 · LEXICON SEEDS</div>
  <div class="card">
    <h2>黑话搜索种子 <span class="tag">SEEDS</span>
      <button class="copybtn" id="copySeeds">复制全部种子词</button></h2>
    <div class="seedwrap" id="seeds"></div>
  </div>

  <div class="section-title">团伙聚类 · GANG CLUSTERS</div>
  <div id="gangs"></div>

  <div class="section-title">情报明细 · RECORDS</div>
  <div class="toolbar">
    <input id="search" placeholder="搜索标题 / 昵称 / 黑话…">
    <select id="fcat"><option value="">全部类目</option></select>
    <select id="sort">
      <option value="risk">按风险分</option>
      <option value="demand">按需求热度</option>
      <option value="engage">按互动量</option>
    </select>
  </div>
  <div id="records"></div>

  <footer>本看板由黑灰产情报流水线离线生成，仅供反诈 / 平台风控 / 安全研究使用。</footer>
</div>

<script>
const DATA = /*__DATA__*/;
const S = DATA.summary;
const DISPLAY_MIN_RISK = S.min_record_risk ?? 50;
const DISPLAY_MIN_GANG_RISK = S.min_peak_risk ?? 60;
const G = (DATA.gangs || []).filter(g => (g.max_risk || 0) > DISPLAY_MIN_GANG_RISK);
const R = (DATA.records || []).filter(r => (r.risk_score || 0) > DISPLAY_MIN_RISK);
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// subline
document.getElementById('subline').textContent =
  `生成于 ${new Date().toISOString().slice(0,10)} · 共 ${R.length} 条情报 · ${G.length} 个团伙簇`
  + (DISPLAY_MIN_RISK ? ` · 明细仅展示风险>${DISPLAY_MIN_RISK}` : '')
  + (DISPLAY_MIN_GANG_RISK ? ` · 团伙仅展示峰值风险>${DISPLAY_MIN_GANG_RISK}` : '');

// ===== 数据全貌 overview =====
const PS = S.pipeline_stats || {};
const ICONS = {
  db:'<path d="M12 5c4.4 0 8 1.1 8 2.5S16.4 10 12 10 4 8.9 4 7.5 7.6 5 12 5Z"/><path d="M4 7.5v9C4 17.9 7.6 19 12 19s8-1.1 8-2.5v-9"/><path d="M4 12c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5"/>',
  filter:'<path d="M3 5h18l-7 8v6l-4-2v-4z"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  shield:'<path d="M12 3 5 6v5c0 4.5 3 8 7 9 4-1 7-4.5 7-9V6z"/><path d="m9 12 2 2 4-4"/>',
  target:'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/>',
  trend:'<path d="M3 17 9 11l4 4 8-8"/><path d="M21 7v5h-5"/>',
  bolt:'<path d="M13 3 4 14h6l-1 7 9-11h-6z"/>',
  contact:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  pulse:'<path d="M3 12h4l2 6 4-14 2 8h6"/>',
};
const ov_cards = [];
function ovc(icon,value,suffix,accent,title,desc,arrow){
  if(value===null||value===undefined) return;
  ov_cards.push({icon,value:+value,suffix,accent,title,desc,arrow:!!arrow});
}
ovc('db', PS.raw, '条', '#5fb6c9', '原始数据采集',
    (PS.source_keywords?`${PS.source_keywords} 个关键词 · `:'')+'跨平台采集去重前', false);
ovc('filter', PS.dedup_removed, '条重复', '#e8843c', '跨关键词去重',
    (PS.raw?`${(100*PS.dedup_removed/PS.raw).toFixed(1)}% 去重率 · `:'')+'note_id 精确 + 文本近似', false);
ovc('search', PS.noise_filtered, '条噪音', '#e0b84a', '噪声剔除',
    '无黑灰产特征 · 相关性过滤', false);
ovc('filter', S.record_risk_filtered, '条低分', '#e8843c', '风险分过滤',
    `单帖风险<=${DISPLAY_MIN_RISK} · 不进入明细`, false);
ovc('shield', R.length, '条', '#7fae6b', '高质量情报',
    '清洗 · 去噪 · 结构化提取', false);
ovc('target', G.length, '个', '#e86bb0', '团伙聚类',
    'union-find 共享标识交叉关联', true);
ovc('trend', (S.risk_distribution||{})['高危(70-100)'], '个', '#ff5a4d', '高危帖子',
    (DISPLAY_MIN_GANG_RISK?`峰值风险>${DISPLAY_MIN_GANG_RISK} · `:'')+'优先处置', true);
ovc('bolt', (S.jargon_collection||{}).total_unique_terms, '个', '#9b87e0', '黑话搜索种子',
    '跨语料汇总 · 回灌采集扩面', true);
ovc('contact', S.total_contacts_exposed, '个', '#5ec9b0', '露出联系方式',
    '微信/QQ/TG/手机 · 交易通道线索', false);
ovc('pulse', S.total_demand_signals, '个', '#5fb6c9', '需求询单信号',
    '评论区买方意向计数', true);

document.getElementById('ovgrid').innerHTML = ov_cards.map(c=>`
  <div class="ov-card">
    <div class="ov-top">
      <div class="ov-ico" style="background:${c.accent}1f">
        <svg viewBox="0 0 24 24" fill="none" stroke="${c.accent}" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">${ICONS[c.icon]||''}</svg>
      </div>
      <div class="ov-num">
        <span class="cnt" data-target="${c.value}">0</span>
        <span class="suf" style="color:${c.accent}">${esc(c.suffix)}</span>
        ${c.arrow?`<span class="arrow" style="color:${c.accent}">↑</span>`:''}
      </div>
    </div>
    <div class="ov-title">${esc(c.title)}</div>
    <div class="ov-desc">${esc(c.desc)}</div>
  </div>`).join('');

// 滚动进视口时数字从 0 跳动到目标值（仅触发一次）
function animateCount(el, delay){
  const target = +el.dataset.target || 0;
  const dur = 1300;
  const fmt = n => Math.round(n).toLocaleString('en-US');
  let t0 = null;
  function tick(now){
    if(t0===null) t0 = now;
    const p = Math.min(1, (now - t0) / dur);
    const e = 1 - Math.pow(1 - p, 3); // easeOutCubic
    el.textContent = fmt(target * e);
    if(p < 1) requestAnimationFrame(tick); else el.textContent = fmt(target);
  }
  setTimeout(()=>requestAnimationFrame(tick), delay);
}
(function(){
  const ov = document.getElementById('overview');
  if(!ov) return;
  const fire = ()=>{
    ov.classList.add('in');
    document.querySelectorAll('#ovgrid .cnt').forEach((el,i)=>animateCount(el, i*80));
  };
  if('IntersectionObserver' in window){
    const io = new IntersectionObserver((ents)=>{
      ents.forEach(en=>{ if(en.isIntersecting){ fire(); io.disconnect(); }});
    }, {threshold:0.2});
    io.observe(ov);
  } else { fire(); }
})();

// bar helper
function bars(el, pairs, sig){
  const max = Math.max(1, ...pairs.map(p=>p[1]));
  el.innerHTML = pairs.map(([k,v])=>`
    <div class="bar-row">
      <div class="k" title="${esc(k)}">${esc(k)}</div>
      <div class="bar-track"><div class="bar-fill ${sig?'sig':''}" style="width:${v/max*100}%"></div></div>
      <div class="v">${v}</div>
    </div>`).join('') || '<div class="sub">无数据</div>';
}
bars(document.getElementById('cat'), S.by_category, true);
bars(document.getElementById('plat'), S.by_platform, false);
bars(document.getElementById('ip'), S.by_ip, false);

// risk
const rd = S.risk_distribution;
document.getElementById('risk').innerHTML = `
  <div class="riskpill hi"><div class="n">${rd['高危(70-100)']}</div><div class="l">高危 70-100</div></div>
  <div class="riskpill mid"><div class="n">${rd['中危(40-69)']}</div><div class="l">中危 40-69</div></div>
  <div class="riskpill lo"><div class="n">${rd['低危(0-39)']}</div><div class="l">低危 0-39</div></div>`;

// gangs
document.getElementById('gangs').innerHTML = G.map(g=>{
  const cats = g.top_categories.map(c=>`${esc(c[0])}×${c[1]}`).join(' · ');
  return `<div class="gang">
    <div class="gang-head">
      <span class="gang-id">${g.gang_id} · ${g.note_count} 帖</span>
      <span class="risk-badge" style="color:${riskColor(g.max_risk)}">峰值风险 ${g.max_risk}</span>
    </div>
    <div class="gang-meta">运营号：${esc(g.authors.join('、')||'未知')}</div>
    <div class="gang-meta">属地：${esc(g.ip_locations.join('、')||'未知')} · 类目：${cats||'—'} · 询单热度 ${g.total_demand}</div>
    ${g.shared_contacts.length?`<div class="gang-meta">共享联系方式：${esc(g.shared_contacts.join('、'))}</div>`:''}
  </div>`;
}).join('') || '<div class="sub">未聚出多帖团伙</div>';

function riskColor(s){ return s>=70?'#ff5a4d':s>=40?'#e8843c':'#7fae6b'; }

// jargon seeds —— 按频次排序，供下一轮采集复用
const JC = S.jargon_collection || {terms:[], search_seeds:[]};
document.getElementById('seeds').innerHTML = JC.terms.map(t=>{
  const ev = (t.evidence||[]).map(e=>`${e.field}:${e.excerpt}`).filter(Boolean).join(' | ');
  const tip = [t.type, t.platforms.join('/'), t.categories.join('/'), ev].filter(Boolean).join(' · ');
  return `<span class="seed ${t.type==='类目黑话'?'cat':''}" title="${esc(tip)}">${esc(t.term)} <span class="ct">×${t.count}</span></span>`;
}).join('') || '<div class="sub">未汇总到黑话</div>';
document.getElementById('copySeeds').addEventListener('click', e=>{
  const txt = (JC.search_seeds||[]).join(' ');
  const done = ()=>{ e.target.textContent='已复制 '+(JC.search_seeds||[]).length+' 个 ✓'; e.target.classList.add('done'); };
  if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(txt).then(done).catch(()=>{prompt('复制以下种子词：',txt);}); }
  else { prompt('复制以下种子词：', txt); }
});

// records
const fcat = document.getElementById('fcat');
[...new Set(R.flatMap(r=>Object.keys(r.biz_categories)))].forEach(c=>{
  const o=document.createElement('option');o.value=c;o.textContent=c;fcat.appendChild(o);
});
function renderRecords(){
  const q=document.getElementById('search').value.toLowerCase();
  const cat=fcat.value, sort=document.getElementById('sort').value;
  let list=R.filter(r=>{
    const hay=(r.title+' '+r.desc_excerpt+' '+(r.author?.nickname||'')+' '+r.jargon_hits.join(' ')).toLowerCase();
    return (!q||hay.includes(q)) && (!cat||cat in r.biz_categories);
  });
  list.sort((a,b)=> sort==='demand'? b.demand_signals.inquiry_count-a.demand_signals.inquiry_count
    : sort==='engage'? (b.engagement.liked+b.engagement.comment)-(a.engagement.liked+a.engagement.comment)
    : b.risk_score-a.risk_score);
  document.getElementById('records').innerHTML = list.map(r=>{
    const cats=Object.keys(r.biz_categories).map(c=>`<span class="chip cat">${esc(c)}</span>`).join('');
    const plats=r.target_platforms.map(p=>`<span class="chip plat">${esc(p)}</span>`).join('');
    const tags=r.risk_tags.map(t=>`<span class="chip tag">${esc(t)}</span>`).join('');
    const prices=r.prices.map(p=>`${esc(p.amount)}元${p.near_unit?'/'+esc(p.near_unit):''}`).join('、');
    const contacts=r.contacts.map(c=>`${esc(c.type)}:${esc(c.value)}`).join('、');
    const demand=r.demand_signals.samples.map(s=>`<div class="quote">${esc(s.user)}：${esc(s.content)}</div>`).join('');
    return `<div class="rec">
      <div class="rec-head" onclick="this.parentNode.classList.toggle('open')">
        <div>
          <div class="rec-title">${esc(r.title||r.desc_excerpt||'(无标题)')}</div>
          <div class="rec-meta">${esc(r.author?.nickname||'?')} · ${esc(r.author?.ip_location||'?')} · ${esc((r.publish_time||'').slice(0,10))} · ${esc(r.source_keyword||'')}</div>
        </div>
        <span class="risk-badge" style="background:${riskColor(r.risk_score)}22;color:${riskColor(r.risk_score)}">风险 ${r.risk_score}</span>
      </div>
      <div class="chips">${cats}${plats}${tags}</div>
      <div class="rec-body">
        ${prices?`<div class="row"><span class="lab">报价</span>${esc(prices)}</div>`:''}
        ${contacts?`<div class="row"><span class="lab">联系方式</span>${esc(contacts)}</div>`:''}
        ${r.jargon_hits.length?`<div class="row"><span class="lab">黑话</span>${esc(r.jargon_hits.join('、'))}</div>`:''}
        ${r.scam_disguise.length?`<div class="row"><span class="lab">伪装话术</span>${esc(r.scam_disguise.join('、'))}</div>`:''}
        ${demand?`<div class="row"><span class="lab">需求样本</span></div>${demand}`:''}
        ${r.link?`<div class="row"><a href="${esc(r.link)}" target="_blank">查看原帖 ↗</a></div>`:''}
      </div>
      <span class="more" onclick="this.closest('.rec').classList.toggle('open')">展开 / 收起 ▾</span>
    </div>`;
  }).join('') || '<div class="sub">无匹配结果</div>';
}
['search','fcat','sort'].forEach(id=>{
  document.getElementById(id).addEventListener('input',renderRecords);
  document.getElementById(id).addEventListener('change',renderRecords);
});
renderRecords();
</script>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="analysis.json")
    ap.add_argument("-o", "--output", default="dashboard.html")
    args = ap.parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        analysis = json.load(f)
    htmlout = build(analysis)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(htmlout)
    print(f"[dashboard] 输出 -> {args.output}")


if __name__ == "__main__":
    main()
