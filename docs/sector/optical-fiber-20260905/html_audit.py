"""Offline audit appendix; inputs are frozen JSON and text receipts."""
import json,html,hashlib,re
from pathlib import Path
B=Path(__file__).resolve().parent
esc=lambda x:html.escape(str(x) if x is not None else '')
def load(n):return json.loads((B/n).read_text())
W=load('workbook_data.json');C=load('chart_data.json')
def chart(name):
 c=C[name];rows=[]
 svg=c['svg']
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
def appendix():
 receipts={str(p.relative_to(B)):p.read_text() for p in sorted((B/'raw').rglob('*')) if p.is_file() and p.suffix in ('.json','.jsonl','.md','.txt')}
 receipts['DATA-SOURCES.md']=(B/'DATA-SOURCES.md').read_text()
 data={'workbook':W,'charts':C,'sector':load('sector_data.json'),'brokers':load('broker_data.json'),'receipts':receipts}
 out=['<section id="full-data"><h2>完整数据</h2><p>六张原工作表共 '+str(W['counts']['cells'])+' 个有效单元格。保留原始数值、编号、显示格式、公式和来源批注。原表中的“可编辑”说明仅作历史记录，本页不提供假设编辑。</p><label>工作表 <select id="sheet-filter"><option value="">全部</option>'+''.join('<option>'+esc(s['name'])+'</option>' for s in W['sheets'])+'</select></label> <label>搜索 <input id="data-search" type="search" placeholder="公司、指标、来源或单元格"></label><p id="data-count" role="status"></p>']
 for s in W['sheets']:
  out.append('<details class="print-open"><summary>'+esc(s['name'])+'</summary><p>表内口径：'+esc('；'.join(str(c['value']) for c in s['cells'] if c['ref'] in ('A1','A3','A5')))+'</p><div class="table-wrap"><table><thead><tr><th>追踪编号</th><th>原始值</th><th>公式 / 来源 / 格式</th></tr></thead><tbody>')
  for c in s['cells']:
   key=s['name']+'!'+c['ref'];out.append('<tr class="audit-cell" data-sheet="'+esc(s['name'])+'"><td>'+esc(key)+'</td><td>'+esc(c['value'])+'</td><td><details><summary>展开详情</summary><p>原显示格式：'+esc(c['format'])+'</p><p>来源批注：'+esc(c['comment'] or '未附单元格批注；参见表内来源与口径')+'</p><p>公式：'+esc(c['formula'] or '原始输入 / 文本')+'</p></details></td></tr>')
  out.append('</tbody></table></div></details>')
 out.append('</section><section id="calculations"><h2>计算过程</h2><p id="calc-status" role="status">等待浏览器复算</p><p>下列值按原公式复算，保留完整精度；公式中引用编号对应“完整数据”。</p>')
 for s in W['sheets']:
  for c in s['cells']:
   if c['formula']:
    key=s['name']+'!'+c['ref'];out.append('<details><summary>'+esc(key)+' · '+esc(c['formula'])+'</summary><div id="calc-'+esc(key)+'"></div></details>')
 out.append('</section><section id="sources"><h2>来源与缺口</h2><p>以下为保存的来源台账和文本回执。外部研报仍按原链接、日期和页码追溯；本页不包含原始 PDF 全文。MISSING / PARTIAL 保持原义。</p>')
 for name,body in receipts.items():out.append('<details><summary>'+esc(name)+'</summary><pre>'+esc(body)+'</pre></details>')
 for name,body in [('sector_data.json',data['sector']),('broker_data.json',data['brokers']),('原工作簿图表定义及范围',W['original_charts'])]:out.append('<details><summary>'+esc(name)+'</summary><pre>'+esc(json.dumps(body,ensure_ascii=False,indent=2))+'</pre></details>')
 out.append('<p>迁移基线 SHA-256：'+W['archive_sha256']+'</p></section>')
 out.append('<script type="application/json" id="research-data">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>')
 return ''.join(out)
CSS='''svg{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.7 ui-monospace,monospace}details{margin:12px 0;border:1px solid #dbe3e4;padding:10px 14px;border-radius:5px}summary{cursor:pointer;color:#1b666c;font-weight:600}select,input{max-width:100%;padding:8px;font:inherit}main{min-width:0}p,details,summary{overflow-wrap:anywhere}details{min-width:0}figure{min-width:0}.audit-cell td{overflow-wrap:anywhere}.vector-chart svg{display:block;width:100%}@media print{.vector-chart{break-inside:avoid}.vector-chart svg{max-height:350px}#full-data table{table-layout:fixed}#full-data select,#full-data input{display:none}}'''
