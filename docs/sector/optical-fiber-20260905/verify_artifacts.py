"""Offline completeness checks. --archive additionally compares the original XLSX."""
import json,math,re,sys,hashlib
from pathlib import Path
from html.parser import HTMLParser
B=Path(__file__).resolve().parent
class Page(HTMLParser):
 def __init__(self):super().__init__();self.data='';self.capture=False;self.svg=0;self.sections=0;self.resources=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='script' and a.get('id')=='research-data':self.capture=True
  if tag=='svg':self.svg+=1
  if tag=='section':self.sections+=1
  for k in ('src','xlink:href'):
   if a.get(k) and not a[k].startswith('#'):self.resources.append(a[k])
 def handle_endtag(self,tag):
  if tag=='script':self.capture=False
 def handle_data(self,d):
  if self.capture:self.data+=d
p=Page();p.feed((B/'index.html').read_text());d=json.loads(p.data)
for k,f in [('workbook','workbook_data.json'),('charts','chart_data.json'),('sector','sector_data.json'),('brokers','broker_data.json')]:assert d[k]==json.loads((B/f).read_text()),f
for name,body in d['receipts'].items():assert body==(B/name).read_text(),name
expected={str(p.relative_to(B)) for p in (B/'raw').rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl','.md','.txt')}
assert expected<=set(d['receipts'])
assert (p.svg,p.sections,p.resources)==(8,16,[]),(p.svg,p.sections,p.resources)
w=d['workbook'];assert len(w['sheets'])==6
assert len(d['sector']['companies'])==7 and len(d['sector']['valuation_history'])==81 and len(d['brokers'])==6
cells={(s['name'],c['ref']):c for s in w['sheets'] for c in s['cells']}
assert len(cells)==w['counts']['cells']==2024
assert sum(bool(c['formula']) for c in cells.values())==379
assert sum(bool(c['comment']) for c in cells.values())==143
near=lambda a,b:math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-8)
# Both original workbook charts are fully covered by the SVG series.
for col,line in zip('BC',d['charts']['demand_share']['panels'][0]['series']):
 assert all(near(cells['行业需求',f'{col}{r}']['value'],v) for r,v in zip(range(21,27),line['y']))
for col,line in zip('JKNI',d['charts']['valuation_history']['panels'][0]['series']):
 assert len(line['y'])==81
 assert all(near(cells['历史估值',f'{col}{r}']['value'],v) for r,v in zip(range(7,88),line['y']))
if '--archive' in sys.argv:
 import openpyxl,datetime
 path=B.parents[2]/'outputs/sector-overview-20260905/行业数据与估值附录.xlsx'
 assert hashlib.sha256(path.read_bytes()).hexdigest()==w['archive_sha256']
 a=openpyxl.load_workbook(path,data_only=False);cached=openpyxl.load_workbook(path,data_only=True);seen=set()
 for s in a:
  for row in s:
   for c in row:
    if c.value is None and not c.comment:continue
    key=(s.title,c.coordinate);seen.add(key);v=cached[s.title][c.coordinate].value
    if isinstance(v,(datetime.datetime,datetime.date)):v=v.isoformat()
    assert cells[key]==dict(ref=c.coordinate,value=v,formula=c.value[1:] if c.data_type=='f' else None,comment=c.comment.text if c.comment else None,format=c.number_format),key
 assert seen==set(cells)
print(json.dumps({'status':'PASS',**w['counts'],'receipts':len(d['receipts']),'SVG':8,'original_charts_covered':2,'archive_compared':'--archive' in sys.argv},ensure_ascii=False))
