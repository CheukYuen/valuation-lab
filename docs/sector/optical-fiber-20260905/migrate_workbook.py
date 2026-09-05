"""One-time archive migration. Normal HTML builds never require the workbook."""
import json, hashlib, datetime
from pathlib import Path
from zipfile import ZipFile
import openpyxl
B=Path(__file__).resolve().parent
p=B.parents[2]/'outputs/sector-overview-20260905/行业数据与估值附录.xlsx'
a=openpyxl.load_workbook(p,data_only=False);b=openpyxl.load_workbook(p,data_only=True)
def value(v): return v.isoformat() if isinstance(v,(datetime.datetime,datetime.date)) else v
sheets=[]
for s in a:
 cells=[]
 for row in s:
  for c in row:
   if c.value is None and not c.comment:continue
   cells.append(dict(ref=c.coordinate,value=value(b[s.title][c.coordinate].value),formula=c.value[1:] if c.data_type=='f' else None,comment=c.comment.text if c.comment else None,format=c.number_format))
 sheets.append(dict(name=s.title,cells=cells,merges=[str(x) for x in s.merged_cells.ranges]))
with ZipFile(p) as z: charts={n:z.read(n).decode() for n in z.namelist() if '/charts/chart' in n and n.endswith('.xml')}
out=dict(archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),sheets=sheets,original_charts=charts)
out['counts']={k:sum(test(c) for s in sheets for c in s['cells']) for k,test in [('cells',lambda c:True),('formulas',lambda c:bool(c['formula'])),('comments',lambda c:bool(c['comment']))]}
(B/'workbook_data.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out['counts'])
