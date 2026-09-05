"""Build an offline HTML research report with embedded charts and source links."""
from html_audit import chart, appendix, CSS, palette_css
import html
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
def inline(text):
 text=html.escape(text)
 text=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',text)
 text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
 text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{m[2]}"'+(' target="_blank" rel="noopener noreferrer"' if m[2].startswith('http') else '')+f'>{m[1]}</a>',text)
 return text

lines=(BASE/'REPORT.md').read_text().splitlines();parts=[];toc=[];i=0;opened=False;section=0
while i<len(lines):
 line=lines[i];i+=1
 if line.startswith('<!-- chart:'):
  parts.append(chart(line.split(':',1)[1].split(' -->')[0]));continue
 if not line.strip() or line.startswith('<!--') or line.startswith('# '):continue
 if line.startswith('## '):
  if opened:parts.append('</section>')
  heading=line[3:];section+=1;anchor=f'section-{section}';toc.append((anchor,heading))
  parts.append(f'<section id="{anchor}" aria-labelledby="title-{section}"><div class="section-kicker">{section:02d} / 13</div><h2 id="title-{section}">{inline(heading)}</h2>');opened=True;continue
 if not opened:continue
 if line.startswith('### '):parts.append('<h3>'+inline(line[4:])+'</h3>');continue
 if line.startswith('!['):
  m=re.match(r'!\[([^]]+)\]\(([^)]+)\)',line)
  parts.append(chart(Path(m[2]).stem));continue
 if line.startswith('|'):
  batch=[line]
  while i<len(lines) and lines[i].startswith('|'):batch.append(lines[i]);i+=1
  rows=[[x.strip() for x in row.strip().strip('|').split('|')] for row in batch]
  rows=[r for r in rows if not all(re.fullmatch(r':?-+:?',x) for x in r)]
  isbroker=section==12
  if isbroker and '原评级' in rows[0]:parts.append('<div class="broker-tools" aria-label="筛选投行报告"><span>公司筛选</span><button class="selected" data-filter="全部" aria-pressed="true">全部</button><button data-filter="长飞光纤" aria-pressed="false">长飞光纤</button><button data-filter="中天科技" aria-pressed="false">中天科技</button><span id="broker-count" role="status">6 份报告</span></div>')
  parts.append('<div class="table-wrap" tabindex="0" role="region" aria-label="'+html.escape(rows[0][0])+'比较表"><table'+(' class="broker-table"' if isbroker else '')+'><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
  for row in rows[1:]:
   cls=' data-company="'+('长飞光纤' if '长飞' in row[0] else '中天科技')+'"' if isbroker else ''
   parts.append('<tr'+cls+'>'+''.join('<td'+(' class="missing"' if c=='MISSING' else '')+'>'+inline(c)+'</td>' for c in row)+'</tr>')
  parts.append('</tbody></table></div>');continue
 cls=' class="caption"' if line.startswith('图 ') else ''
 parts.append('<p'+cls+'>'+inline(line)+'</p>')
if opened:parts.append('</section>')
nav=''.join(f'<a href="#{a}"><span>{i:02d}</span>{html.escape(t)}</a>' for i,(a,t) in enumerate(toc,1))
nav+='<a href="#full-data">完整数据</a><a href="#calculations">计算过程</a><a href="#sources">来源与缺口</a>'
css='''
:root{--ink:#172b36;--muted:#536772;--brand:#1b666c;--line:#dbe3e4;--paper:#fff;--bg:#f4f6f4;--gold:#ac6c39}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:92px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.9 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}button{font:inherit;cursor:pointer}button:focus-visible,a:focus-visible,.table-wrap:focus-visible{outline:3px solid #d4a65f;outline-offset:4px}.topbar{height:62px;position:sticky;top:0;z-index:5;background:#153e45;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 32px;border-bottom:1px solid #36616a}.brand{letter-spacing:.09em;font-size:13px}.topbar-actions{display:flex;gap:22px;align-items:center;font-size:12px}.topbar-actions a{color:#d9ece7}.print{color:white;border:1px solid #65868b;background:transparent;border-radius:4px;padding:4px 12px}.reading-progress{position:fixed;top:62px;left:0;height:3px;background:#c1a368;width:0;z-index:6}.layout{max-width:1520px;margin:auto;display:grid;grid-template-columns:240px minmax(0,1fr);gap:48px;padding:34px 40px 100px}.sidebar{position:sticky;top:95px;align-self:start;max-height:calc(100vh - 120px);overflow:auto}.sidebar-title{font-size:11px;letter-spacing:.16em;color:var(--muted);margin:0 0 15px}.toc a{display:flex;gap:12px;padding:7px 8px;font-size:12px;line-height:1.65;color:#566b75;border-left:2px solid transparent}.toc a span{color:#85979d;font-variant-numeric:tabular-nums;flex-shrink:0}.toc a.active{color:#174e54;background:#e6edeb;border-left-color:var(--brand);font-weight:600}.sidebar-note{font-size:11px;color:#6c7b80;border-top:1px solid var(--line);margin-top:24px;padding-top:16px}.sidebar-note a{display:block;margin-top:8px}.hero{padding:16px 0 28px;border-bottom:1px solid #b7c9c8}.eyebrow{font-size:12px;letter-spacing:.14em;color:var(--brand);font-weight:600}.hero h1{font-family:"Songti SC","Noto Serif SC",serif;font-weight:600;font-size:clamp(32px,3.7vw,52px);letter-spacing:-.025em;line-height:1.3;max-width:900px;margin:18px 0}.deck{font-size:17px;line-height:1.9;max-width:900px;color:#455e65;margin:0 0 22px}.meta{display:flex;flex-wrap:wrap;gap:10px 24px;font-size:11px;color:#587078}.keyline{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;margin:30px 0 20px}.metric{border-left:2px solid #aac2bf;padding-left:14px}.metric .value{font-size:24px;line-height:1.5;font-weight:600;letter-spacing:-.02em}.metric small{display:block;font-size:11px;line-height:1.6;color:#63757c}.evidence-note{margin-top:25px;background:#edf1ed;padding:14px 18px;border-left:3px solid #ad915e;font-size:12px;line-height:1.8;color:#455e63}section{padding:42px 0;border-bottom:1px solid var(--line);scroll-margin-top:85px}.section-kicker{font-size:11px;color:var(--brand);letter-spacing:.12em;font-weight:600}h2{font-size:27px;font-family:"Songti SC","Noto Serif SC",serif;line-height:1.4;margin:8px 0 22px;color:#173e44}h3{font-size:18px;margin:30px 0 12px}p{margin:16px 0}strong{font-weight:650;color:#203c42}code{font-size:.9em;background:#e9efec;padding:1px 4px;border-radius:3px}.table-wrap{overflow-x:auto;background:var(--paper);margin:24px 0;border:1px solid var(--line);border-radius:5px}table{width:100%;border-collapse:collapse;font-size:12px;line-height:1.8;min-width:650px}th{font-weight:600;color:#25545b;background:#e6eeec;text-align:left;padding:13px 12px;white-space:normal;border-bottom:1px solid #c5d6d2}td{padding:12px;vertical-align:top;border-bottom:1px solid #e6ecea;font-variant-numeric:tabular-nums}tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#f9faf9}tbody tr:hover{background:#edf3f2}.missing{color:#9b713e;font-size:11px;letter-spacing:.02em}figure{margin:26px 0 8px;padding:18px;background:white;border:1px solid var(--line);border-radius:5px}figure img{display:block;max-width:100%;height:auto;width:100%}.caption{font-size:11px;line-height:1.8;color:#63747b;margin:8px 4px 24px}.broker-tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:25px;font-size:12px;color:#5b7077}.broker-tools button{font-size:12px;padding:5px 12px;border:1px solid #bfd0cd;border-radius:4px;background:#fff;color:#395961}.broker-tools button.selected{background:var(--brand);color:white;border-color:var(--brand)}#broker-count{margin-left:auto}.footer{font-size:11px;color:#63747b;padding:24px 0}.mobile-toc{display:none}[hidden]{display:none!important}
@media(min-width:1500px){.layout{gap:64px}}@media(max-width:1000px){.layout{grid-template-columns:180px minmax(0,1fr);gap:28px;padding:28px 24px}.toc a{font-size:11px}.hero h1{font-size:36px}.keyline{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:720px){body{font-size:14px}.topbar{padding:0 16px}.brand{font-size:11px;letter-spacing:.03em}.topbar-actions{gap:12px}.topbar-actions .desktop-only{display:none}.layout{display:block;padding:22px 18px 60px}.sidebar{display:none}.mobile-toc{display:block;margin:20px 0;background:#e9efec;padding:12px 16px;border-radius:4px}.mobile-toc summary{cursor:pointer;font-weight:600;color:var(--brand)}.mobile-toc a{display:block;padding:4px;font-size:12px}.mobile-toc a span{margin-right:10px}.hero{padding-top:0}.hero h1{font-size:32px}.deck{font-size:14px}.keyline{gap:18px}.metric .value{font-size:23px}h2{font-size:24px}section{padding:32px 0}figure{padding:9px}.table-wrap{margin:18px 0}td,th{padding:10px}#broker-count{margin-left:0;width:100%}}
@media print{body{background:white;font-size:10pt}.topbar,.sidebar,.mobile-toc,.broker-tools,.reading-progress{display:none}.layout{display:block;padding:0;max-width:none}.hero h1{font-size:28pt}.keyline{margin:18px 0}section{padding:18px 0;break-inside:auto}h2,h3{break-after:avoid}figure,.metric,tr{break-inside:avoid}.table-wrap{overflow:visible;border:0}table{min-width:0;font-size:8pt}a{color:inherit}figure img{max-height:280px;object-fit:contain}.evidence-note{font-size:9pt}.footer{border-top:1px solid #aaa}thead{display:table-header-group}}
'''
js='''
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{const selected=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button));});document.querySelectorAll('.broker-table tbody tr').forEach(row=>row.hidden=selected!=='全部'&&row.dataset.company!==selected);document.getElementById('broker-count').textContent=(selected==='全部'?6:selected==='长飞光纤'?4:2)+' 份报告';}));
document.getElementById('print-report').addEventListener('click',()=>window.print());
const links=[...document.querySelectorAll('.sidebar .toc a')];const observer=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting);if(visible.length){const id=visible[0].target.id;links.forEach(a=>a.classList.toggle('active',a.hash==='#'+id));}},{rootMargin:'-10% 0px -65% 0px'});document.querySelectorAll('main section').forEach(s=>observer.observe(s));
const progress=()=>{const max=document.documentElement.scrollHeight-innerHeight;document.querySelector('.reading-progress').style.width=(max>0?100*scrollY/max:0)+'%';};addEventListener('scroll',progress,{passive:true});progress();
'''
css+=CSS+palette_css()
js+=(BASE/'html_audit.js').read_text()
target='index.html'
parts.append(appendix())
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="光纤光缆与AI光连接行业概览，长飞与中天主线，Wind、Choice和投行研报交叉研究。"><title>光纤光缆与 AI 光连接行业概览</title><style>'''+css+'''</style></head><body><header class="topbar"><div class="brand">VALUATION LAB / 行业研究</div><div class="topbar-actions"><a class="desktop-only" href="#sources">来源与口径</a><a href="#full-data">完整数据</a><button class="print" id="print-report">打印</button></div></header><div class="reading-progress" aria-hidden="true"></div><div class="layout"><aside class="sidebar"><p class="sidebar-title">CONTENTS / 研究目录</p><nav class="toc" aria-label="章节目录">'''+nav+'''</nav><div class="sidebar-note">各家投行保留原报告日期。所有目标价均为原报告观点，未平均为本研究的目标价。<a href="#calculations">计算过程</a><a href="#sources">查询记录与证据边界 ↗</a></div></aside><main><div class="hero"><div class="eyebrow">SECTOR OVERVIEW / 2026.09</div><h1>光纤光缆与<br>AI 光连接行业概览</h1><p class="deck">沿长飞光纤与中天科技，辨别产品升级、供给扩张和现金回款。把行业增长放回具体业务，再看价格中包含了多少预期。</p><div class="meta"><span>研究日期 2026 年 9 月 5 日</span><span>估值截点 2026 年 9 月 2 日</span><span>财务基准 2025A / 2026H1</span><span>Codex 整理 · 内部研究</span></div><div class="keyline"><div class="metric"><div class="value">7 家</div><small>上市公司价值链比较</small></div><div class="metric"><div class="value">6 份</div><small>五家投行原时点报告</small></div><div class="metric"><div class="value">81 期</div><small>Choice 月末及末端估值观测</small></div><div class="metric"><div class="value">8 张</div><small>市场 经营与估值图表</small></div></div><div class="evidence-note"><strong>证据边界</strong> 全球收入 TAM、CR5、有效产能与完整 TTM EV 桥仍为 MISSING 或 PARTIAL。投行预测单列，不视为实际业绩或市场共识。</div></div><details class="mobile-toc"><summary>展开研究目录</summary>'''+nav+'''</details>'''+''.join(parts)+'''<footer class="footer">研究文件截至 2026 年 9 月 5 日。市场数值冻结于 9 月 2 日。SVG 图表、明细、公式和文本回执均已嵌入本页，可离线阅读；原始研究档案继续保留。</footer></main></div><script>'''+js+'''</script></body></html>'''
page=re.sub(r'<a href="[^"]*\.xlsx"[^>]*>.*?</a>', '<a href="#full-data">完整数据（已迁移）</a>', page)
(BASE/target).write_text(page)
assert page.count('<section id=')==16
assert page.count('<svg ')==8
assert 'data:image/png' not in page
print(BASE/target)
