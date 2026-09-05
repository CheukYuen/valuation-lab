"""Validate P0 evidence, units, dedup boundaries, and rendered data integrity."""
import json,re,hashlib,math
from pathlib import Path

def verify(b):
 d=json.loads((b/'p0_data.json').read_text());page=(b/'index.html').read_text()
 embedded=re.search(r'<script type="application/json" id="p0-data">(.*?)</script>',page,re.S)[1]
 assert json.loads(embedded)==d
 assert d['as_of']=='2026-09-05' and d['valuation_date']=='2026-09-02'
 for s in d['sources'].values():
  assert s['date']<=d['as_of'] and s['pages'] and s['verification']
  assert hashlib.sha256(Path(s['path']).read_bytes()).hexdigest()==s['sha256']
 for key,t in d['tables'].items():
  assert f'id="p0-{key}"' in page,key
  assert all(len(r)==len(t['columns']) for r in t['rows']),key
  assert t['note'] and all(r[-1] for r in t['rows'])
 for c in d['charts']:
  rows=d['tables'][c['table']]['rows']
  for col,allowed in c.get('where',{}).items():rows=[r for r in rows if r[int(col)] in allowed]
  assert rows
  assert f'id="p0-chart-{c["id"]}"' in page
 # Manually checked PDF sentinels catch incorrect transcription and row/column shifts.
 prices=d['tables']['prices']['rows']
 get=lambda period,region,currency:next(r[4] for r in prices if r[0]==period and r[1]==region and r[2]=='G.652D' and r[3]==currency)
 assert get('2026-07','中国','CNY')==81.5
 assert get('2026-07','欧洲','USD')==13
 assert get('2026-08','中国','CNY')==85.7
 assert any(r[2].startswith('G652.A1（原表') and r[4]==130.7 for r in prices)
 cap=d['tables']['capacity']['rows']
 announced=cap[:15];assert sum(r[4] for r in announced)==19400
 assert sum(r[4] for r in announced if r[1]=='中国')==14700
 assert cap[15][4]=='800–1000' and '不累加' in cap[15][7]
 assert cap[-1][4]=='带状光缆翻倍' and cap[-1][5]!='吨'
 asp=d['tables']['asp']['rows']
 assert asp[0][1:5]==[104.9,160,21.2,70] and asp[-1][1:4]==[60.5,55,23.4]
 for r in asp:
  assert math.isclose(r[5],r[1]-r[3],abs_tol=1e-8)
  assert math.isclose(r[6],r[2]-r[3],abs_tol=1e-8)
 for c in d['calculations'].values():
  for t,r,col in c['inputs']:assert isinstance(d['tables'][t]['rows'][r][col],(float,int))
 assert d['tables']['tender']['rows'][3][2:4]==[53.85,'元/芯千米，含VAT']
 assert d['tables']['tender']['rows'][9][2:4]==[7100,'百万元，不含税']
 for v in d['verification']:assert (b/v['receipt']).exists()
 print('P0 PASS: sources, transcription sentinels, units, dedup, formulas, embedded data')
if __name__=='__main__':verify(Path(__file__).resolve().parent)
