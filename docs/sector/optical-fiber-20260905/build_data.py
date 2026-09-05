"""Normalize saved receipts without new network requests."""
import hashlib
import json
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]

def receipt(name):
    envelope = json.loads((BASE / 'raw' / name).read_text())
    assert envelope.get('ok') is not False and not envelope.get('isError')
    return json.loads(envelope['content'][0]['text'])

def records(name):
    return [dict(zip([x['name'] for x in t['columns']], row))
            for t in receipt(name)['data']['data'] for row in t['rows']]

def find_value(rows, *parts):
    hits = [v for row in rows for k, v in row.items()
            if all(p in k for p in parts) and isinstance(v, (int, float))]
    assert hits, parts
    assert len(set(hits)) == 1, (parts, hits)
    return hits[0]

companies = [
    ('yofc','长飞光纤','601869.SH','长飞',53.6,53.4,29.8,62.4,6.8,247.5174,66.0945,34.4,2274.7522),
    ('ztt','中天科技','600522.SH','核心',31.1,16.5,7.7,6.2,3.0,643.26,63.55,18.1,1148.12),
    ('hengtong','亨通光电','600487.SH','核心',31.1,16.8,7.4,-27.7,4.7,837.49,77.35,21.3,1650.02),
    ('fiberhome','烽火通信','600498.SH','核心',11.3,21.4,1.6,264.1,5.2,287.26,14.56,37.4,544.90),
    ('innolight','中际旭创','300308.SZ','AI映射',182.5,46.3,32.7,13.2,11.5,989.48,318.56,30.4,9687.13),
    ('accelink','光迅科技','002281.SZ','AI映射',26.1,25.5,8.8,-212.3,9.1,179.01,16.61,86.4,1435.82),
    ('tfc','天孚通信','300394.SZ','AI映射',15.1,60.9,42.6,83.1,10.9,88.67,35.30,77.3,2727.06),
]
out=[]
for slug,name,code,group,growth,gm,nm,ocf,capex,forecast,ni,fpe,cap in companies:
    rows=records(f'wind-{slug}-fundamentals.json')
    fy=find_value(rows,'2025年年报','营业收入')
    h1=find_value(rows,'2026年半年报','营业收入')
    ebitda25=find_value(rows,'2025年年报','EBITDA')
    ebitda26=find_value(rows,'2026年半年报','EBITDA')
    evrows=records(f'wind-{slug}-ev.json')
    ev=[v for row in evrows for k,v in row.items() if '企业价值' in k][0]
    item=dict(slug=slug,name=name,code=code,group=group,rev25=fy,rev_h1=h1,ebitda25=ebitda25,
              ebitda_h1=ebitda26,ebitda_margin_h1=ebitda26/h1,growth_h1=growth/100,
              gm_h1=gm/100,nm_h1=nm/100,ocf_np_h1=ocf/100,capex_rev_h1=capex/100,
              forecast_rev26=forecast,forecast_np26=ni,forward_pe26=fpe,market_cap=cap,
              ev_vendor=ev,ev_ebitda25=ev/ebitda25,ev_sales25=ev/fy)
    item['pe_history']={str(int(r['年份'])):next(v for k,v in r.items() if '每年末' in k and isinstance(v,(int,float)))
                        for r in rows if '年份' in r}
    out.append(item)

production=receipt('wind-industry-series.json')['metrics'][0]
yoy=receipt('wind-production-yoy.json')['metrics'][0]
assert production['meta']['code']=='S0070683' and production['meta']['unit']=='芯千米'
annual=[dict(year=int(d[:4]),fiber_km=v,source_yoy=dict(zip(yoy['date'],yoy['value']))[d]/100)
        for d,v in zip(production['date'],production['value']) if d.endswith('1231')]
monthly=json.loads((BASE/'raw/choice-peer-monthly.json').read_text())
idx=json.loads((BASE/'raw/choice-csi300-monthly.json').read_text())
pe_by_code={c[2]:{r['DATES']:r['PETTM'] for r in monthly if r['CODES']==c[2]} for c in companies}
dates=sorted(pe_by_code[companies[0][2]])
history=[]
for date in dates:
    row={'date':date,'yofc_a':pe_by_code['601869.SH'][date]}
    for group in ['核心','AI映射']:
        vals=[pe_by_code[c[2]][date] for c in companies if c[3]==group]
        assert all(v is not None and v>0 for v in vals), (date,vals)
        row[group]=statistics.median(vals)
    row['csi300']=next(r['PETTM'] for r in idx if r['DATES']==date)
    history.append(row)
historical_stats={}
for group in ['核心','AI映射','yofc_a','csi300']:
    vals=[r[group] for r in history if r['date']<'2026']
    historical_stats[group]={'min':min(vals),'median':statistics.median(vals),'max':max(vals),'observations':len(vals)}

data={'as_of':'2026-09-05','valuation_date':'2026-09-02','companies':out,
      'production':annual,'production_ytd':{'date':production['date'][-1],'fiber_km':production['value'][-1],
      'source_yoy':yoy['value'][-1]/100},'production_cagr5':(annual[-1]['fiber_km']/annual[0]['fiber_km'])**.2-1,
      'valuation_history':history,'historical_stats':historical_stats,
      'choice_snapshot':json.loads((BASE/'raw/choice-valuation.json').read_text()),
      'supply_announced':[{'region':'中国','tonnes':14700},{'region':'日本','tonnes':3200},{'region':'美国','tonnes':1500}],
      'source_labels':{'historical_financials':'WIND-FACT;反推法EBITDA;正式算法及正常化桥PARTIAL',
      'h1_ratios_and_forecasts':'2026-09-02 Wind Comps底稿;WIND-FACT/DERIVED/PARTIAL',
      'history':'CHOICE-FACT;月末和2026-09-02;固定公司样本;非历史成分行业指数',
      'ev':'WIND-FACT/DERIVED/PARTIAL;2026-09-02供应商EV除以2025A财务;非TTM;未重建完整EV桥'}}
(BASE/'sector_data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
inventory=[]
for directory in ['docs/yofc','docs/ztt']:
    for p in sorted((ROOT/directory).iterdir()):
        if p.is_file():
            inventory.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                              'role':'正文与来源核对' if p.suffix=='.md' else '模型或历史报告索引;未改变其计算假设'})
(BASE/'raw/source-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'production_cagr5':data['production_cagr5'],'latest':history[-1],
                  'historical_stats':historical_stats,
                  'companies':[{k:v for k,v in c.items() if k in ['name','ebitda_margin_h1','ev_ebitda25','ev_sales25']} for c in out]},ensure_ascii=False,indent=2))
