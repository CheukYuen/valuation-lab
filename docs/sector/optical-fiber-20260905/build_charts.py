"""Build static research charts from the saved data only."""
import json
import io
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.colors import ListedColormap

BASE=Path(__file__).resolve().parent
D=json.loads((BASE/'sector_data.json').read_text())
OUT=BASE/'charts';OUT.mkdir(exist_ok=True)
font=FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc')
plt.rcParams.update({'font.family':font.get_name(),'axes.spines.top':False,'axes.spines.right':False,
 'axes.titlelocation':'left','axes.titlesize':12,'font.size':10,'axes.unicode_minus':False,
 'figure.facecolor':'white','axes.labelcolor':'#334155','xtick.color':'#475569','ytick.color':'#475569'})
BLUE='#285F8F';TEAL='#168583';ORANGE='#C2783D';GRAY='#94A3B8'
CHARTS={}
def save(fig,name):
 panels=[]
 for ax in fig.axes:
  panel={'title':ax.get_title(),'xlabel':ax.get_xlabel(),'ylabel':ax.get_ylabel(),'xticks':[(float(x),t.get_text()) for x,t in zip(ax.get_xticks(),ax.get_xticklabels())],'yticks':[(float(x),t.get_text()) for x,t in zip(ax.get_yticks(),ax.get_yticklabels())],'series':[],'notes':[t.get_text() for t in ax.texts]}
  for line in ax.lines:
   panel['series'].append({'kind':'line','label':line.get_label(),'x':[str(x) if not isinstance(x,(int,float,np.number)) else float(x) for x in line.get_xdata()],'y':[float(y) for y in line.get_ydata()]})
  for patch in ax.patches:
   if hasattr(patch,'get_height'):panel['series'].append({'kind':'bar','x':float(patch.get_x()),'y':float(patch.get_y()),'width':float(patch.get_width()),'height':float(patch.get_height())})
  for collection in ax.collections:
   if not hasattr(ax,'_research_matrix'):panel['series'].append({'kind':'scatter','points':collection.get_offsets().tolist()})
  if hasattr(ax,'_research_matrix'):panel['series'].append({'kind':'matrix','values':ax._research_matrix,'meaning':{'0':'未标示覆盖，不代表无业务','1':'相关业务','2':'重点覆盖'}})
  for im in ax.images:panel['series'].append({'kind':'matrix','values':im.get_array().tolist(),'meaning':{'0':'未标示覆盖，不代表无业务','1':'相关业务','2':'重点覆盖'}})
  panels.append(panel)
 plt.rcParams['svg.fonttype']='none'
 stream=io.StringIO();fig.savefig(stream,format='svg',bbox_inches='tight',facecolor='white')
 svg=stream.getvalue();svg=svg[svg.index('<svg'):]
 CHARTS[Path(name).stem]={'svg':svg,'panels':panels}
 plt.close(fig)

fig,ax=plt.subplots(figsize=(10.2,3.4));yrs=[r['year'] for r in D['production']];v=[r['fiber_km']/1e8 for r in D['production']]
ax.bar(yrs,v,color=[GRAY]*5+[BLUE],width=.57)
for x,y in zip(yrs,v):ax.text(x,y+.06,f'{y:.2f}',ha='center')
ax.set(ylim=(0,4),ylabel='亿芯千米',xticks=yrs,title='中国光缆产量 2020—2025');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
save(fig,'production.png')

fig,ax=plt.subplots(figsize=(10.2,3.2));v=[1.49,.71,.53,3.04];bottom=0
for i,x in enumerate(v):
 ax.bar(i,x,bottom=bottom,color=TEAL if i<3 else GRAY,width=.62)
 ax.text(i,bottom+x/2,f'{x:.2f}',ha='center',va='center',color='white' if i<3 else '#172B4D',weight='bold');bottom+=x
ax.bar(4,5.77,color=BLUE,width=.62);ax.text(4,5.9,'5.77',ha='center',weight='bold')
ax.set(xticks=range(5),xticklabels=['北美','亚洲除中国','西欧','其余地区\n含中国','全球合计'],ylabel='亿芯千米',ylim=(0,6.6),title='2026 年 1 月旧预测的地区拆分');save(fig,'market_waterfall.png')

fig,(a,b)=plt.subplots(1,2,figsize=(10.2,3.4),gridspec_kw={'width_ratios':[1.5,1]});x=np.arange(2025,2031)
for rate,label,col in [(.2074,'数据中心 20.74%',TEAL),(.0247,'电信 2.47%',BLUE)]:a.plot(x,100*(1+rate)**(x-2025),'o-',label=label,color=col)
a.set(title='CRU 转引 CAGR 的指数演示',ylabel='2025 年 = 100',xticks=x);a.legend(frameon=False,loc='upper left',fontsize=9);a.grid(alpha=.15)
b.bar(['2026E','2027E'],[43,55],color=[GRAY,TEAL],width=.5)
for i,y in enumerate([43,55]):b.text(i,y+2,f'{y}%',ha='center')
b.set(title='杰富瑞数据中心占比预测',ylim=(0,70),ylabel='%');fig.tight_layout(w_pad=2);save(fig,'demand_share.png')

fig,ax=plt.subplots(figsize=(10.2,3.8));m=np.array([[2,2,1,0,0],[2,2,1,0,2],[2,2,1,0,2],[1,1,1,2,0],[0,0,2,0,0],[0,0,2,0,0],[0,0,2,0,0]])
ax.pcolormesh(np.arange(6)-.5,np.arange(8)-.5,m,cmap=ListedColormap(['#F4F6F8','#B9D8E3',BLUE]),vmin=0,vmax=2);ax.invert_yaxis();ax._research_matrix=m.tolist()
ax.set(yticks=range(7),yticklabels=[c['name'] for c in D['companies']],xticks=range(5),xticklabels=['预制棒与光纤','通信光缆','器件组件及模块','通信系统设备','电力及海洋'])
ax.xaxis.tick_top();ax.tick_params(length=0)
for i in range(7):
 for j in range(5):
  if m[i,j]:ax.text(j,i,'重点覆盖' if m[i,j]==2 else '相关业务',ha='center',va='center',color='white' if m[i,j]==2 else '#22384B',fontsize=9)
for s in ax.spines.values():s.set_visible(False)
save(fig,'positioning.png')

fig,(a,b)=plt.subplots(1,2,figsize=(10.2,3.5),gridspec_kw={'width_ratios':[1.3,1]})
mix=[([61.25485258,22.38455552,98.0896-61.25485258-22.38455552],['光通信','组件','其他'],98.0896),([73.7,222.64,63.49,56.97,95.21,524.9986-512.01],['光网络','电网','海洋','新能源','铜','其他'],524.9986)]
colors=[BLUE,TEAL,ORANGE,'#A78BFA',GRAY,'#D8DFE7']
for i,(vals,labels,total) in enumerate(mix):
 left=0
 for j,(v,label) in enumerate(zip(vals,labels)):
  w=v/total*100;a.barh(i,w,left=left,color=colors[j],height=.48)
  if w>8:a.text(left+w/2,i,f'{label}\n{w:.0f}%',ha='center',va='center',fontsize=8,color='white' if j<4 else '#22384B')
  left+=w
a.set(yticks=[0,1],yticklabels=['长飞\n2026H1','中天\n2025A'],xlim=(0,100),xlabel='集团收入占比 %',title='业务构成 期间分别标注');a.invert_yaxis()
x=np.arange(2)
b.bar(x-.18,[29.25,23.87],width=.32,color=GRAY,label='归母净利润');b.bar(x+.18,[18.26,1.48],width=.32,color=TEAL,label='经营现金流')
b.set(xticks=x,xticklabels=['长飞','中天'],ylabel='亿元',ylim=(0,39),title='2026H1 现金转换');b.legend(frameon=False,fontsize=8);fig.tight_layout(w_pad=2);save(fig,'business_cash.png')

fig,ax=plt.subplots(figsize=(10.2,3.8))
for c in D['companies']:
 col=TEAL if c['group']=='AI映射' else BLUE if c['group']=='核心' else ORANGE
 ax.scatter(c['growth_h1']*100,c['forward_pe26'],s=65,color=col)
 offsets={'yofc':(5,4),'ztt':(5,-12),'hengtong':(5,3),'fiberhome':(5,4),'innolight':(-52,8),'accelink':(5,3),'tfc':(5,3)}
 ax.annotate(c['name'],(c['growth_h1']*100,c['forward_pe26']),xytext=offsets[c['slug']],textcoords='offset points',fontsize=9)
ax.set(xlabel='2026H1 收入同比增长 %',ylabel='2026E P/E 倍',xlim=(0,205),ylim=(0,100),title='增长与估值 冻结的 9 月 2 日 Wind 底稿');ax.grid(alpha=.15);save(fig,'valuation_scatter.png')

from datetime import datetime
fig,ax=plt.subplots(figsize=(10.2,4));dates=[datetime.strptime(r['date'].replace('/','-'),'%Y-%m-%d') for r in D['valuation_history']]
for key,label,col in [('核心','核心组中位数',BLUE),('AI映射','AI 映射组中位数',TEAL),('yofc_a','长飞 A 股',ORANGE),('csi300','沪深 300',GRAY)]:
 ax.plot(dates,[r[key] for r in D['valuation_history']],label=label,color=col,lw=1.7)
ax.set(ylabel='TTM P/E 倍',ylim=(0,420),title='固定样本的月末估值 2020 年至 2026 年 9 月 2 日');ax.legend(ncol=2,frameon=False,fontsize=9,loc='upper left');ax.grid(alpha=.15);save(fig,'valuation_history.png')

brokers=json.loads((BASE/'broker_data.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(10.2,3.8))
for ax,company in zip(axes,['长飞光纤','中天科技']):
 for k,b in enumerate([b for b in brokers if b['company']==company and b['profit'][0] is not None]):
  ax.plot([2026,2027,2028],b['profit'],'o-',label=f"{b['bank']} {b['date'][5:]}",color=[BLUE,TEAL,ORANGE][k])
 ax.set(title=company,ylabel='报告净利润 亿元',xticks=[2026,2027,2028],xticklabels=['2026E','2027E','2028E'],ylim=(0,170));ax.legend(frameon=False,fontsize=8);ax.grid(alpha=.15)
fig.tight_layout(w_pad=2);save(fig,'broker_forecasts.png')

def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])
(BASE/'chart_data.json').write_text(json.dumps(CHARTS,ensure_ascii=False,indent=2)+'\n')
p=BASE/'REPORT.md';s=p.read_text()
if '{{COMPANY_TABLE}}' in s:
 s=s.replace('{{COMPANY_TABLE}}',table(['公司','2025A收入','2026H1收入','H1同比','H1 EBITDA率','市场份额'],[[c['name'],f"{c['rev25']:.2f}",f"{c['rev_h1']:.2f}",f"{c['growth_h1']:.1%}",f"{c['ebitda_margin_h1']:.1%}",'MISSING'] for c in D['companies']]))
 s=s.replace('{{VALUATION_TABLE}}',table(['公司','2026E P/E','供应商 EV','EV/2025A EBITDA','EV/2025A收入'],[[c['name']+(' A/H混合' if c['slug']=='yofc' else ''),f"{c['forward_pe26']:.1f}",f"{c['ev_vendor']:.2f}",f"{c['ev_ebitda25']:.2f}",f"{c['ev_sales25']:.2f}"] for c in D['companies']]))
 s=s.replace('{{HISTORY_TABLE}}',table(['样本','历史最低','历史中位','历史最高','9月2日'],[[label,*[f"{D['historical_stats'][k][v]:.2f}" for v in ['min','median','max']],f"{D['valuation_history'][-1][k]:.2f}"] for k,label in [('核心','核心组三家'),('AI映射','AI映射组三家'),('yofc_a','长飞A股'),('csi300','沪深300')]]))
if '{{BROKER_TARGETS}}' in s:
 s=s.replace('{{BROKER_TARGETS}}',table(['公司','投行与日期','原评级','原目标价','估值方法','复算边界'],[[b['company'],f"[B{i+1} {b['bank']} {b['date']}]({b['source']})",b['rating'],f"{b['target']:.2f} {b['currency']}",b['method'],b['gap']] for i,b in enumerate(brokers)]))
 s=s.replace('{{BROKER_FORECASTS}}',table(['公司与投行','2026E收入','2026E净利润','2027E净利润','2028E净利润','净利润口径'],[[b['company']+' '+b['bank'],*[('MISSING' if v is None else f'{v:.2f}') for v in [b['revenue'][0],*b['profit']]],b['profit_basis']] for b in brokers]))
p.write_text(s)
print('8 SVG charts with full plotted data generated; no PNG output')
