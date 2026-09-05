"""Offline audit appendix; inputs are frozen JSON and text receipts."""
import json,html,re
from pathlib import Path
B=Path(__file__).resolve().parent
esc=lambda x:html.escape(str(x) if x is not None else '')
def load(n):return json.loads((B/n).read_text())
W=load('workbook_data.json');C=load('chart_data.json');S=W['style']

# --- Excel number-format rendering, for the twelve formats the archived workbook uses ---
def sections(code):
 out=[];cur='';q=False
 for ch in code:
  if ch=='"':q=not q;cur+=ch
  elif ch==';' and not q:out.append(cur);cur=''
  else:cur+=ch
 out.append(cur);return out

def pieces(sec):
 out=[];i=0
 while i<len(sec):
  ch=sec[i]
  if ch=='"':
   j=sec.index('"',i+1);out.append(('lit',sec[i+1:j]));i=j+1
  elif ch=='\\':out.append(('lit',sec[i+1:i+2]));i+=2
  elif ch in '#0,.':
   j=i
   while j<len(sec) and sec[j] in '#0,.':j+=1
   out.append(('num',sec[i:j]));i=j
  else:out.append(('lit',ch));i+=1
 return out

def render(value,code):
 """Return (text, red) for one cell. `value` is the cached workbook value."""
 if value is None:return '',False
 if isinstance(value,str):
  # Dates arrive as ISO strings from the archive extraction.
  return (value.split('T')[0] if code and 'y' in code and 'T' in value else value),False
 if isinstance(value,bool) or not code or code=='General':return str(value),False
 secs=[s for s in sections(code)]
 if value>0 or len(secs)==1:sec,signed=secs[0],True
 elif value<0:sec,signed=(secs[1],False) if len(secs)>1 else (secs[0],True)
 else:sec,signed=(secs[2],False) if len(secs)>2 else (secs[0],True)
 red='[Red]' in sec;sec=sec.replace('[Red]','')
 parts=pieces(sec)
 pat=next((t for k,t in parts if k=='num'),None)
 if pat is None:return ''.join(t for k,t in parts),red
 percent=any(k=='lit' and t=='%' for k,t in parts)
 x=abs(value)*100 if percent else abs(value)
 dec=len(pat.split('.')[1]) if '.' in pat else 0
 body=format(x,(',' if ',' in pat else '')+'.'+str(dec)+'f')
 if signed and value<0:body='-'+body
 return ''.join(body if k=='num' else t for k,t in parts),red

# --- end number formats ---

CELLS={s['name']:{c['ref']:c for c in s['cells']} for s in W['sheets']}
STYLE={s['name']:s for s in S['sheets']}
HEADER_FILL='285F8F'   # the workbook's header band; it marks where a block starts
PX_PER_CHAR=7    # Excel max-digit-width for Arial 10; column px = width*MDW + padding
PX_PAD=5
def letter(n):
 s=''
 while n:n,r=divmod(n-1,26);s=chr(65+r)+s
 return s
def index(s):
 n=0
 for ch in s:n=n*26+ord(ch)-64
 return n
def span(ref):
 a,b=ref.split(':')
 m=re.match(r'([A-Z]+)(\d+)',a);n=re.match(r'([A-Z]+)(\d+)',b)
 return int(m[2]),index(m[1]),int(n[2]),index(n[1])
def chart(name):
 c=C[name];rows=[]
 svg='\n'.join(line.rstrip() for line in c['svg'].splitlines())
 for ident in set(re.findall(r'id="([^"]+)"',svg)):
  svg=svg.replace('id="'+ident+'"','id="'+name+'-'+ident+'"')
  svg=re.sub(r'#'+re.escape(ident)+r'(?=["\)])','#'+name+'-'+ident,svg)
 for p in c['panels']:
  rows.append('<h4>'+esc(p['title'])+'</h4><p>'+esc(p['xlabel']+' / '+p['ylabel'])+'</p>')
  rows.append('<pre>'+esc(json.dumps({k:v for k,v in p.items() if k!='series'},ensure_ascii=False,indent=2))+'</pre>')
  rows.append('<div class="table-wrap"><table><thead><tr><th>系列 / 类型</th><th>完整数据（原始精度）</th></tr></thead><tbody>')
  for s in p['series']:rows.append('<tr><td>'+esc(s.get('label',s['kind']))+'</td><td><pre>'+esc(json.dumps(s,ensure_ascii=False,indent=2))+'</pre></td></tr>')
  rows.append('</tbody></table></div>')
 return '<figure id="chart-'+esc(name)+'" class="vector-chart">'+svg+'<details><summary>查看数据与标注</summary>'+''.join(rows)+'</details></figure>'
def palette_css():
 out=['.xs{font-family:Arial,Helvetica,"PingFang SC",sans-serif;font-size:10pt;color:#000;background-color:#fff}']
 for i,p in enumerate(S['palette']):
  d=[]
  if p['fill']:d.append('background:#'+p['fill'])
  if p['color']:d.append('color:#'+p['color'])
  if p['bold']:d.append('font-weight:700')
  if p['italic']:d.append('font-style:italic')
  if p['size']:d.append('font-size:'+str(p['size'])+'pt')
  if p['name']:d.append('font-family:'+p['name']+',Helvetica,"PingFang SC",sans-serif')
  if p['halign']:d.append('text-align:'+p['halign'])
  d.append('vertical-align:'+{'center':'middle','justify':'middle','distributed':'middle'}.get(p['valign'],p['valign'] or 'bottom'))
  d.append('white-space:'+('pre-wrap' if p['wrap'] else 'nowrap'))
  out.append('.xs'+str(i)+'{'+';'.join(d)+'}')
 return ''.join(out)
def rowpx(sh,r):
 h=sh['row_height'].get(str(r)) or sh['default_row_height'] or 15.0
 return round(h*4/3)
def grid(name):
 """Render one worksheet as a real two-dimensional table, 1:1 with the workbook."""
 sh=STYLE[name];cells=CELLS[name];rows,cols=sh['max_row'],sh['max_col']
 covered={};anchor={}
 for ref in W['sheets'][[s['name'] for s in W['sheets']].index(name)]['merges']:
  r1,c1,r2,c2=span(ref);anchor[(r1,c1)]=(r2-r1+1,c2-c1+1)
  for r in range(r1,r2+1):
   for c in range(c1,c2+1):
    if (r,c)!=(r1,c1):covered[(r,c)]=True
 frozen=int(re.match(r'[A-Z]*(\d+)',sh['freeze'] or 'A1')[1])-1
 # Each sheet stacks several blocks: a dark header band starts one, a full-width merged note
 # or an empty run ends it. Only rows inside a block may be sorted or filtered.
 band=lambda r:any(S['palette'][sh['styles'].get(letter(c)+str(r),0)]['fill']==HEADER_FILL for c in range(1,cols+1))
 block={};kind={};current=0
 for r in range(1,rows+1):
  if band(r):current+=1;kind[r]='head'
  elif any((r,c) in anchor and anchor[(r,c)][1]==cols for c in range(1,cols+1)) or (r,1) in covered:kind[r]='note'
  elif not any(letter(c)+str(r) in cells for c in range(1,cols+1)):kind[r]='blank';current=current
  else:kind[r]='data'
  block[r]=current
 top=[0]
 for r in range(1,frozen+1):top.append(top[-1]+rowpx(sh,r))
 out=['<div class="grid-wrap" tabindex="0" role="region" aria-label="'+esc(name)+' 原格式网格">',
      '<table class="xlgrid'+('' if sh['grid_lines'] else ' nolines')+'"><colgroup><col class="gutter">']
 for c in range(1,cols+1):
  w=sh['col_width'].get(letter(c)) or sh['default_col_width'] or 8.43
  out.append('<col style="width:'+str(round(w*PX_PER_CHAR+PX_PAD))+'px">')
 out.append('</colgroup><thead><tr class="axis" style="height:22px"><th class="gutter corner" style="top:0"></th>')
 for c in range(1,cols+1):out.append('<th class="axis-col" scope="col" data-col="'+letter(c)+'" style="top:0">'+letter(c)+'<span class="rz" aria-hidden="true"></span></th>')
 out.append('</tr>')
 for r in range(1,rows+1):
  head=r<=frozen
  sticky=' style="top:'+str(22+top[r-1])+'px"' if head else ''
  if r==frozen+1:out.append('</thead><tbody>')
  mark=' data-row="'+str(r)+'" data-kind="'+kind[r]+'"'+(' data-block="'+str(block[r])+'"' if block[r] and kind[r] in ('head','data') else '')
  out.append('<tr'+mark+' style="height:'+str(rowpx(sh,r))+'px">'
             +'<th class="gutter axis-row'+(' frozen' if head else '')+'" scope="row"'+sticky+'>'+str(r)+'</th>')
  for c in range(1,cols+1):
   if (r,c) in covered:continue
   ref=letter(c)+str(r);cell=cells.get(ref);sid=sh['styles'].get(ref,0)
   rs,cs=anchor.get((r,c),(1,1))
   attrs=[' class="xs xs'+str(sid)+('' if not head else ' frozen')+(' col1' if c==1 and anchor.get((r,c),(1,1))[1]==1 else '')]
   text,red='',False
   if cell is not None:
    text,red=render(cell['value'],cell['format'])
    if red:attrs[0]+=' neg'
    if cell['comment']:attrs[0]+=' noted'
   attrs[0]+='"'
   attrs.append(' data-ref="'+esc(name)+'!'+ref+'"')
   if cell is not None and cell['value'] is not None:attrs.append(' data-raw="'+esc(cell['value'])+'"')
   if cell is not None and cell['comment']:attrs.append(' title="'+esc(cell['comment'])+'"')
   if rs>1:attrs.append(' rowspan="'+str(rs)+'"')
   if cs>1:attrs.append(' colspan="'+str(cs)+'"')
   if sticky:attrs.append(sticky)
   body=esc(text)
   if cell is not None and cell['formula']:
    body+='<a class="fmark" href="#calc-'+esc(name)+'!'+ref+'" title="公式 ='+esc(cell['formula'])+'">ƒ</a>'
   out.append('<'+('th' if head else 'td')+''.join(attrs)+'>'+body+'</'+('th' if head else 'td')+'>')
  out.append('</tr>')
 out.append('</tbody></table></div>')
 return ''.join(out)
DISPLAY={n:{r:list(render(c['value'],c['format'])) for r,c in cs.items()} for n,cs in CELLS.items()}
def appendix():
 receipts={str(p.relative_to(B)):p.read_text() for p in sorted((B/'raw').rglob('*')) if p.is_file() and p.suffix in ('.json','.jsonl','.md','.txt')}
 receipts['DATA-SOURCES.md']=(B/'DATA-SOURCES.md').read_text()
 data={'workbook':W,'charts':C,'sector':load('sector_data.json'),'brokers':load('broker_data.json'),'display':DISPLAY,'receipts':receipts}
 out=['<section id="full-data"><h2>完整数据</h2><p>六张原工作表共 '+str(W['counts']['cells'])+' 个有效单元格，按原始行列、合并区域、显示格式、配色、列宽和行高 1:1 还原；前 '+str(int(re.match(r"[A-Z]*(\d+)",STYLE["公司财务"]["freeze"])[1])-1)+' 行按原冻结窗格固定。单元格右上角 ƒ 链到该公式的复算过程，带虚线下划线的格子有原始来源批注。原表中的“可编辑”说明仅作历史记录，本页不提供假设编辑。</p><label>工作表 <select id="sheet-filter"><option value="">全部</option>'+''.join('<option>'+esc(s['name'])+'</option>' for s in W['sheets'])+'</select></label> <label>搜索 <input id="data-search" type="search" placeholder="公司、指标、来源或单元格"></label><p id="data-count" role="status"></p>']
 for s in W['sheets']:
  n=s['name'];sh=STYLE[n]
  out.append('<details class="print-open" data-sheet-block="'+esc(n)+'"><summary>'+esc(n)+'</summary><p>表内口径：'+esc('；'.join(str(c['value']) for c in s['cells'] if c['ref'] in ('A1','A3','A5')))+'</p>')
  out.append('<p class="grid-meta">原表 '+str(sh['max_row'])+' 行 × '+str(sh['max_col'])+' 列，'+str(len(s['cells']))+' 个有效单元格，'+str(len(s['merges']))+' 个合并区域，冻结 '+esc(sh['freeze'])+'。</p>')
  out.append(grid(n))
  out.append('<details class="print-open ledger"><summary>单元格台账（原始精度、公式与来源批注）</summary><div class="table-wrap"><table><thead><tr><th>追踪编号</th><th>原始值</th><th>公式 / 来源 / 格式</th></tr></thead><tbody>')
  for c in s['cells']:
   key=n+'!'+c['ref'];out.append('<tr class="audit-cell" data-sheet="'+esc(n)+'"><td>'+esc(key)+'</td><td>'+esc(c['value'])+'</td><td><details><summary>展开详情</summary><p>原显示格式：'+esc(c['format'])+'</p><p>来源批注：'+esc(c['comment'] or '未附单元格批注；参见表内来源与口径')+'</p><p>公式：'+esc(c['formula'] or '原始输入 / 文本')+'</p></details></td></tr>')
  out.append('</tbody></table></div></details></details>')
 out.append('</section><section id="calculations"><h2>计算过程</h2><p id="calc-status" role="status">等待浏览器复算</p><p>下列值按原公式复算，保留完整精度；公式中引用编号对应“完整数据”。</p>')
 for s in W['sheets']:
  for c in s['cells']:
   if c['formula']:
    key=s['name']+'!'+c['ref'];out.append('<details id="calc-'+esc(key)+'"><summary>'+esc(key)+' · '+esc(c['formula'])+'</summary><div id="calcbody-'+esc(key)+'"></div></details>')
 out.append('</section><section id="sources"><h2>来源与缺口</h2><p>以下为保存的来源台账和文本回执。外部研报仍按原链接、日期和页码追溯；本页不包含原始 PDF 全文。MISSING / PARTIAL 保持原义。</p>')
 for name,body in receipts.items():out.append('<details><summary>'+esc(name)+'</summary><pre>'+esc(body)+'</pre></details>')
 for name,body in [('sector_data.json',data['sector']),('broker_data.json',data['brokers']),('原工作簿图表定义及范围',W['original_charts'])]:out.append('<details><summary>'+esc(name)+'</summary><pre>'+esc(json.dumps(body,ensure_ascii=False,indent=2))+'</pre></details>')
 out.append('<p>迁移基线 SHA-256：'+W['archive_sha256']+'</p></section>')
 out.append('<script type="application/json" id="research-data">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>')
 return ''.join(out)
CSS='''svg{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.7 ui-monospace,monospace}details{margin:12px 0;border:1px solid #dbe3e4;padding:10px 14px;border-radius:5px}summary{cursor:pointer;color:#1b666c;font-weight:600}select,input{max-width:100%;padding:8px;font:inherit}main{min-width:0}p,details,summary{overflow-wrap:anywhere}details{min-width:0}figure{min-width:0}.audit-cell td{overflow-wrap:anywhere}.vector-chart svg{display:block;width:100%}
.grid-meta{font-size:11px;color:#63747b;margin:6px 0 10px}
.grid-wrap{max-height:74vh;overflow:auto;border:1px solid #c3ccd6;border-radius:4px;background:#fff;margin:0 0 16px}
table.xlgrid{border-collapse:separate;border-spacing:0;width:max-content;min-width:0;table-layout:fixed;font:10pt/1.35 Arial,Helvetica,"PingFang SC",sans-serif;background:#fff}
table.xlgrid td,table.xlgrid th{padding:1px 3px;overflow:hidden;border:0;box-shadow:inset -1px -1px 0 #e2e8ee}
table.xlgrid.nolines td.xs,table.xlgrid.nolines th.xs{box-shadow:none}
.xlgrid .gutter{width:44px;background:#eef1f4;color:#5b6b7a;font:11px/1.35 Arial,sans-serif;font-weight:400;text-align:center;vertical-align:middle;position:sticky;left:0;z-index:3;box-shadow:inset -1px -1px 0 #c3ccd6}
.xlgrid .axis-col{background:#eef1f4;color:#5b6b7a;font:11px/1.35 Arial,sans-serif;font-weight:400;text-align:center;position:sticky;z-index:2;box-shadow:inset -1px -1px 0 #c3ccd6}
.xlgrid tr.axis th{position:sticky;top:0;z-index:7}
.xlgrid .corner{z-index:8}
.xlgrid .axis-row{z-index:4}
.xlgrid .gutter.frozen{z-index:6}
.xlgrid th.xs.frozen,.xlgrid td.xs.frozen{position:sticky;z-index:3;background-clip:padding-box}
.grid-tools{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:12px;color:#5b7077;margin:0 0 8px}
.grid-tools input[type=search]{padding:4px 8px;font-size:12px;width:170px}
.grid-tools label{display:flex;gap:5px;align-items:center}
.grid-tools button{font-size:12px;padding:3px 10px;border:1px solid #bfd0cd;border-radius:4px;background:#fff;color:#395961}
.grid-tools .count{margin-left:auto;font-variant-numeric:tabular-nums}
.xlgrid th.axis-col{position:relative;overflow:visible}
.xlgrid .rz{position:absolute;right:0;top:0;bottom:0;width:6px;cursor:col-resize;z-index:9}
.xlgrid tr[data-kind="head"] .xs{cursor:pointer}
.xlgrid .sorted-asc::after{content:" ▲";font-size:7pt;opacity:.9}
.xlgrid .sorted-desc::after{content:" ▼";font-size:7pt;opacity:.9}
.xlgrid.freeze-col .col1{position:sticky;left:44px;z-index:2}
.xlgrid.freeze-col .col1.frozen{z-index:5}
.xlgrid tr[hidden]{display:none}
.xlgrid .neg{color:#c00}
.xlgrid .hit{outline:2px solid #ac6c39;outline-offset:-2px}
.xlgrid .noted{text-decoration:underline dotted rgba(40,95,143,.75);text-underline-offset:3px}
.xlgrid .fmark{font-size:8pt;color:#285f8f;text-decoration:none;margin-left:3px;vertical-align:super}
.xlgrid .fmark:hover{text-decoration:underline}
@media print{.vector-chart{break-inside:avoid}.vector-chart svg{max-height:350px}#full-data table{table-layout:fixed}#full-data select,#full-data input,.grid-tools{display:none}.grid-wrap{max-height:none;overflow:visible;border:0}table.xlgrid{font-size:7pt;width:100%;table-layout:auto}
/* Printing squeezes the columns, so let text wrap rather than clip: nothing may be hidden on paper. */
table.xlgrid td,table.xlgrid th{padding:1px 3px;white-space:normal;overflow:visible;overflow-wrap:anywhere}}'''
