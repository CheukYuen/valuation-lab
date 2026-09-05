"""P0 tables, SVGs and source audit, rendered only from p0_data.json."""
import json, html, re, math
from datetime import datetime
from pathlib import Path
from collections import defaultdict
B=Path(__file__).resolve().parent
P=json.loads((B/'p0_data.json').read_text())
def esc(v):return html.escape('MISSING' if v is None else str(v))
def fmt(v):return format(v,',.4f').rstrip('0').rstrip('.') if isinstance(v,float) else ('MISSING' if v is None else str(v))
def source(v):
 text=esc(v)
 return re.sub(r'\b([JGNBMTFCUEDH])(?= p)',lambda m:f'<a href="#p0-source-{m[1]}">{m[1]}</a>',text)
def table(key):
 t=P['tables'][key];out=f'<div class="p0-table" id="p0-{key}"><h3>{esc(t["title"])}</h3><label class="p0-search-label">筛选本表 <input class="p0-table-search" type="search" aria-label="筛选{esc(t["title"])}" placeholder="地区、规格、企业或年份"></label><div class="table-wrap" tabindex="0"><table><thead><tr>'
 out+=''.join('<th>'+esc(c)+'</th>' for c in t['columns'])+'</tr></thead><tbody>'
 for row in t['rows']:out+='<tr>'+''.join('<td>'+source(fmt(v))+'</td>' for v in row)+'</tr>'
 return out+'</tbody></table></div><p class="caption">'+esc(t['note'])+'</p></div>'
def calc(key):
 c=P['calculations'][key];args=[P['tables'][t]['rows'][r][col] for t,r,col in c['inputs']]
 op=c['operation'];v=args[0]/args[1]*12 if op=='annualize' else (args[0]/args[1]*12/args[2]-1)*100 if op=='annual_change' else args[0]/args[1] if op=='divide' else args[0]/100 if op=='million_to_yi' else 100-sum(args)
 return f'<details class="p0-calc" id="p0-calc-{key}" data-value="{v}"><summary>{esc(c["title"])}：{v:,.2f} {esc(c["unit"])}</summary><p>{esc(c["formula"])}；代入值 {esc(args)}</p><p>{esc(c["note"])}</p></details>'
def svgwrap(id,title,body,height):
 return f'<svg role="img" aria-labelledby="p0-title-{id}" viewBox="0 0 860 {height}" xmlns="http://www.w3.org/2000/svg"><title id="p0-title-{id}">{esc(title)}</title><rect width="860" height="{height}" fill="white"/>{body}</svg>'
def chart(key):
 c=next(c for c in P['charts'] if c['id']==key);t=P['tables'][c['table']];rows=t['rows']
 if 'indices' in c:rows=[rows[i] for i in c['indices']]
 for col,allowed in c.get('where',{}).items():rows=[r for r in rows if r[int(col)] in allowed]
 groups=defaultdict(list)
 if 'ys' in c:
  for y in c['ys']:groups[t['columns'][y]]=[(str(r[c['x']]),r[y]) for r in rows]
 else:
  for r in rows:groups[str(r[c.get('group',c['x'])])].append((str(r[c['x']]),r[c['y']]))
 xs=sorted(set(x for vs in groups.values() for x,y in vs));mx=max(y for vs in groups.values() for x,y in vs)*1.1
 raw=mx/4;scale=10**math.floor(math.log10(raw));step=next(n*scale for n in [1,2,2.5,5,10] if n*scale>=raw);mx=4*step
 colors=['#12656b','#b56c32','#6375aa','#5c8a62'];body=f'<text x="65" y="27" font-size="14" fill="#52676f">{esc(c["unit"])}</text>'
 for i in range(5):
  y=280-i*55;body+=f'<path d="M65 {y}H820" stroke="#dce5e5"/><text x="55" y="{y+5}" text-anchor="end" font-size="13">{mx*i/4:.0f}</text>'
 if all(re.fullmatch(r'\d{4}-\d{2}',x) for x in xs):
  positions={x:datetime.strptime(x,'%Y-%m').toordinal() for x in xs}
 else:positions={x:i for i,x in enumerate(xs)}
 lo=min(positions.values());span=max(1,max(positions.values())-lo)
 X=lambda x:85+(positions[x]-lo)*710/span;Y=lambda y:280-y/mx*220
 for i,(label,vs) in enumerate(groups.items()):
  color=colors[i%4];label=c.get('labels',{}).get(label,label)
  if c.get('kind')=='bar':
   for x,y in vs:
    px=180+i*370;body+=f'<rect x="{px}" y="{Y(y)}" width="150" height="{280-Y(y)}" fill="{color}"/><text x="{px+75}" y="{Y(y)-10}" text-anchor="middle">{y}%</text><text x="{px+75}" y="306" text-anchor="middle">{esc(label)}</text>'
  else:
   body+='<polyline fill="none" stroke="'+color+'" stroke-width="3" points="'+' '.join(f'{X(x)},{Y(y)}' for x,y in vs)+'"/>'
   for x,y in vs:body+=f'<circle cx="{X(x)}" cy="{Y(y)}" r="4" fill="{color}"><title>{esc(label)} / {esc(x)}: {y}</title></circle>'
  body+=f'<rect x="65" y="{343+i*23}" width="14" height="3" fill="{color}"/><text x="88" y="{349+i*23}" font-size="13">{esc(label)}</text>'
 if c.get('kind')!='bar':
  for x in xs:body+=f'<text x="{X(x)}" y="306" text-anchor="middle" font-size="11" transform="rotate(-25 {X(x)} 306)">{esc(x)}</text>'
 height=370+len(groups)*23
 return f'<figure class="p0-chart" id="p0-chart-{key}"><h3>{esc(c["title"])}</h3>'+svgwrap(key,c['title'],body,height)+f'<figcaption>{esc(c["note"])}</figcaption><a href="#p0-{c["table"]}">查看同源数据表与口径</a></figure>'
def timeline():
 rows=P['timeline'];body=''
 for i,r in enumerate(rows):
  y=30+i*87;body+=f'<rect x="5" y="{y}" width="850" height="72" rx="4" fill="{["#eef4f3","#f7f1e8"][i%2]}"/><text x="20" y="{y+25}" font-size="16" font-weight="600">{esc(r[0])}</text><text x="20" y="{y+51}" font-size="14">{esc(r[1])}</text>'
 return '<figure class="p0-chart"><h3>供给释放窗口：建设不是达产</h3>'+svgwrap('timeline','供给释放窗口',body,40+len(rows)*87)+'<figcaption>原报告时间口径不同；节点不表示已完成投产，也不生成新增产能总和。</figcaption></figure>'
def appendix():
 out='<section id="p0-evidence"><h2>P0数据与研报证据</h2><p>可按关键词检索来源；点击正文来源编号展开对应原文定位。已读报告仅纳入截止日期前的证据。</p><label>搜索来源 <input id="p0-source-search" type="search" placeholder="机构、公司、关键词"></label>'
 for id,s in P['sources'].items():
  out+=f'<details class="p0-source" id="p0-source-{id}"><summary>{id} · {esc(s["title"])} · {esc(s["date"])}</summary><p>{esc(s["pages"])}；{esc(s["verification"])}</p><a href="{esc(s["path"])}">打开本地PDF</a><p>SHA256：<code>{s["sha256"]}</code></p></details>'
 out+='<h3>专项核验记录</h3>'
 for r in P['verification']:out+='<details><summary>'+esc(r['topic'])+'：'+esc(r['status'])+'</summary><p>'+esc(r['result'])+'</p><p>回执：'+esc(r['receipt'])+'</p></details>'
 out+='<details><summary>完整P0结构化数据与派生公式</summary><pre>'+esc(json.dumps(P,ensure_ascii=False,indent=2))+'</pre></details></section>'
 return out+'<script type="application/json" id="p0-data">'+json.dumps(P,ensure_ascii=False).replace('<','\\u003c')+'</script>'
CSS='''
.p0-chart svg{display:block;width:100%;height:auto;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#243e47}.p0-chart h3{margin:0 0 8px}.p0-chart figcaption,.p0-chart>a{font-size:12px;color:#526b72}.p0-calc{padding:14px 18px;background:#edf3f0;margin:14px 0;border-left:3px solid #1b666c}.p0-calc summary{cursor:pointer;font-weight:600}#p0-evidence details{padding:13px;border-bottom:1px solid #dae3e4}#p0-evidence pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;max-height:480px;overflow:auto}#p0-evidence code{overflow-wrap:anywhere}#p0-source-search{font:inherit;padding:6px;border:1px solid #adbebb;max-width:100%}.p0-table td{max-width:320px;overflow-wrap:anywhere}.hero .keyline{grid-template-columns:repeat(3,minmax(0,1fr))}@media(max-width:720px){.hero .keyline{grid-template-columns:1fr;gap:12px}.hero .metric .value{font-size:20px}}@media print{.p0-search-label{display:none}.p0-chart{break-inside:avoid}.p0-chart svg{max-height:350px}#p0-source-search{display:none}}'''
JS='''
function openP0Source(){const el=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(el?.matches('details.p0-source'))el.open=true;}
addEventListener('hashchange',openP0Source);openP0Source();
document.querySelectorAll('.p0-table-search').forEach(input=>input.addEventListener('input',()=>{const q=input.value.toLowerCase();input.closest('.p0-table').querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));}));
document.getElementById('p0-source-search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('.p0-source').forEach(d=>d.hidden=!d.textContent.toLowerCase().includes(q));});
'''
