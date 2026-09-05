// Archived generator: excluded from the HTML workflow.
if(!process.argv.includes('--archive-rebuild'))throw new Error('Archived: use python3 build_html.py; rebuilding the old workbook requires --archive-rebuild');
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const base=process.argv[2] || path.dirname(fileURLToPath(import.meta.url));
const out=path.resolve(base,'../../../outputs/sector-overview-20260905');
const qa=path.join(out,'qa/xlsx');await fs.mkdir(qa,{recursive:true});
const d=JSON.parse(await fs.readFile(path.join(base,'sector_data.json'),'utf8'));
const monthly=JSON.parse(await fs.readFile(path.join(base,'raw/choice-peer-monthly.json'),'utf8'));
const brokers=JSON.parse(await fs.readFile(path.join(base,'broker_data.json'),'utf8'));
const wb=Workbook.create();wb.comments.setSelf({displayName:'来源与口径'});
const names=['公司财务','行业需求','估值快照','历史估值','来源与缺口','投行研报'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const blue='#285F8F',teal='#168583',green='#00804A',light='#E8EFF5';
const num='#,##0.00;[Red](#,##0.00);"—"';const pct='0.0%;[Red](0.0%);"—"';
function style(s,lastCol,lastRow,title,note){
 s.showGridLines=false;s.freezePanes.freezeRows(6);s.tabColor=blue;
 s.getRange(`A1:${lastCol}${lastRow}`).format={font:{name:'Arial',size:10,color:'#172B4D'},rowHeight:24,columnWidth:13,verticalAlignment:'center'};
 s.getRange(`A1:${lastCol}2`).merge();s.getRange('A1').values=[[title]];s.getRange('A1').format={font:{size:18,bold:true,color:'#000000'}};
 s.getRange(`A3:${lastCol}4`).merge();s.getRange('A3').values=[[note]];s.getRange('A3').format={wrapText:true,font:{size:10,color:'#475569'}};
 s.getRange(`A5:${lastCol}5`).merge();s.getRange('A5').values=[['研究 2026-09-05 | 估值 2026-09-02 | 金额人民币亿元，特别注明除外 | 缺失不填零']];s.getRange('A5').format.font.size=9;
}
function header(s,range,vals){s.getRange(range).values=[vals];s.getRange(range).format={fill:blue,font:{color:'#FFFFFF',bold:true},wrapText:true,rowHeight:42};}
function comment(s,cell,text){wb.comments.addThread({cell:s.getRange(cell)},text);}
function formula(s,cell,text,cross=false){s.getRange(cell).formulas=[[text]];s.getRange(cell).format.font.color=cross?green:'#000000';}
function bands(s,start,end,col){for(let r=start;r<=end;r++)if(r%2===0)s.getRange(`A${r}:${col}${r}`).format.fill='#F3F6F9';}
let s=sheets['公司财务'];
style(s,'L',32,'七家公司财务比较','W3：收入与反推法 EBITDA；L3：H1冻结比例。反推法尚未正常化，不等于经常性经营利润。');
header(s,'A6:L6',['公司','代码','分组','2025A收入','2026H1收入','H1收入同比','H1反推EBITDA','H1 EBITDA率','H1毛利率','H1现金/净利','H1资本开支/收入','来源与性质']);
d.companies.forEach((c,i)=>{let r=i+7;s.getRange(`A${r}:L${r}`).values=[[c.name,c.code,c.group,c.rev25,c.rev_h1,c.growth_h1,c.ebitda_h1,null,c.gm_h1,c.ocf_np_h1,c.capex_rev_h1,'W3 / L3']];formula(s,`H${r}`,`=G${r}/E${r}`);
 for(const col of ['D','E','G'])comment(s,`${col}${r}`,`W3 raw/wind-${c.slug}-fundamentals.json；报告期以列名为准；亿元；取数2026-09-05。`);
 for(const col of ['F','I','J','K'])comment(s,`${col}${r}`,'L3 docs/yofc/13-WIND-COMPS-20260902.md；2026H1已冻结且四舍五入的比例。');
});bands(s,7,13,'L');s.getRange('D7:E13').setNumberFormat(num);s.getRange('G7:G13').setNumberFormat(num);for(const rg of ['F7:F13','H7:K13'])s.getRange(rg).setNumberFormat(pct);
s.getRange('A:A').format.columnWidth=16;s.getRange('B:B').format.columnWidth=16;s.getRange('L:L').format.columnWidth=17;
header(s,'A17:F17',['公司','H1归母净利','H1经营现金流','H1资本开支','现金流减资本开支','现金/净利']);
for(const [i,row] of [['长飞',29.25,18.26,6.71],['中天',23.87,1.48,9.43]].entries()){let r=18+i;s.getRange(`A${r}:D${r}`).values=[row];formula(s,`E${r}`,`=C${r}-D${r}`);formula(s,`F${r}`,`=C${r}/B${r}`);}
s.getRange('B18:E19').setNumberFormat(num);s.getRange('F18:F19').setNumberFormat(pct);
s.getRange('A21:L22').merge();s.getRange('A21').values=[['L1 / L4 公司财报底稿；现金流减资本开支仅为简单现金余额，不是标准 FCFF。两公司资本开支为现金购建长期资产口径。']];s.getRange('A21').format.wrapText=true;
header(s,'A25:F25',['公司','光通信/光网络','组件/电网','其他业务','集团收入','期间与来源']);
s.getRange('A26:F27').values=[['长飞',61.25485258,22.38455552,null,98.0896,'2026H1 L1/L2'],['中天',73.7,222.64,null,524.9986,'2025A L4']];for(let r=26;r<=27;r++)formula(s,`D${r}`,`=E${r}-SUM(B${r}:C${r})`);s.getRange('B26:E27').setNumberFormat(num);
s.getRange('A29:L30').merge();s.getRange('A29').values=[['业务构成期间不同，只用于观察各自构成。全部七家公司同分母市场份额为 MISSING；不得将集团收入当作光纤收入。']];s.getRange('A29').format.wrapText=true;

s=sheets['行业需求'];style(s,'L',49,'行业需求与供给参照','中国生产量不是全球需求；未来数字为第三方转引或券商情景。五年 CAGR 基于绝对量，不等于官方可比口径增速。');
header(s,'A6:F6',['年度','产量 芯千米','产量 亿芯千米','官方累计同比','绝对量同比','来源']);
d.production.forEach((r,i)=>{let rr=7+i;s.getRange(`A${rr}:F${rr}`).values=[[r.year,r.fiber_km,null,r.source_yoy,null,'W1 / W2']];formula(s,`C${rr}`,`=B${rr}/100000000`);if(i)formula(s,`E${rr}`,`=B${rr}/B${rr-1}-1`);});s.getRange('B7:B12').setNumberFormat('#,##0');s.getRange('C7:C12').setNumberFormat('0.00000');s.getRange('D7:E12').setNumberFormat(pct);
s.getRange('A14:C16').values=[['2020至2025 CAGR',null,'DERIVED'],['2026年1至7月 芯千米',128184000,'W1'],['2026年1至7月 官方同比',-.098,'W2']];formula(s,'B14','=(B12/B7)^(1/5)-1');s.getRange('B14').setNumberFormat(pct);s.getRange('B16').setNumberFormat(pct);s.getRange('B15').setNumberFormat('#,##0');
header(s,'H6:L6',['旧预测地区','亿芯千米','状态','版本','来源']);
s.getRange('H7:L11').values=[['北美',1.49,'预测','2026-01-06','W6'],['亚洲除中国',.71,'预测','2026-01-06','W6'],['西欧',.53,'预测','2026-01-06','W6'],['其余含中国',null,'派生','2026-01-06','W6'],['全球',5.77,'预测','2026-01-06','W6']];formula(s,'I10','=I11-SUM(I7:I9)');s.getRange('I7:I11').setNumberFormat('0.00');
s.getRange('H14:L16').merge();s.getRange('H14').values=[['最新本地转引：2026全球需求 >6.70亿芯千米。不能与年初5.77亿混用地区结构；也不是实际同比增速。L2 COMPANY-CITED/PARTIAL']];s.getRange('H14').format.wrapText=true;
header(s,'A20:D20',['预测年度','数据中心指数','电信指数','来源']);
s.getRange('F20:H22').values=[['CAGR输入','年增长率','性质'],['数据中心',.2074,'L2 CRU转引'],['电信',.0247,'L2 CRU转引']];s.getRange('G21:G22').setNumberFormat(pct);s.getRange('G21:G22').format={font:{color:'#0000FF'},fill:'#FFF2CC'};
for(let i=0;i<6;i++){let r=21+i;s.getRange(`A${r}`).values=[[2025+i]];formula(s,`B${r}`,`=100*(1+$G$21)^(A${r}-2025)`);formula(s,`C${r}`,`=100*(1+$G$22)^(A${r}-2025)`);s.getRange(`D${r}`).values=[['指数演示']];}s.getRange('B21:C26').setNumberFormat('0.0');
s.getRange('F24:H26').values=[['杰富瑞DC需求占比','比例','性质'],['2026E',.43,'L5 单家预测'],['2027E',.55,'L5 单家预测']];s.getRange('G25:G26').setNumberFormat(pct);
header(s,'I20:L20',['新增预制棒规划','吨','性质','来源']);s.getRange('I21:L24').values=[['中国',14700,'2026至2028规划','L5'],['日本',3200,'2026至2028规划','L5'],['美国',1500,'2026至2028规划','L5'],['合计',null,'非有效供给','DERIVED']];formula(s,'J24','=SUM(J21:J23)');s.getRange('J21:J24').setNumberFormat('#,##0');
const chart=s.charts.add('line',s.getRange('A20:C26'));chart.title='需求增速指数演示 2025 = 100';chart.setPosition('A30','H47');chart.xAxis={axisType:'textAxis'};chart.yAxis={numberFormatCode:'0',numberFormatSourceLinked:false};
s.getRange('I30:L35').merge();s.getRange('I30').values=[['指数图可随 CAGR 输入变化，不构成预测承诺。两类需求没有基期数量，不能加总为总市场。黄色输入为文献预测参数，可编辑；不是公司指引。']];s.getRange('I30').format.wrapText=true;
s.getRange('A:A').format.columnWidth=25;s.getRange('B:B').format.columnWidth=18;s.getRange('H:H').format.columnWidth=20;s.getRange('I:I').format.columnWidth=20;

s=sheets['估值快照'];style(s,'L',35,'估值快照及 A H 股权桥','EV 分母统一明确为 2025A，非 TTM。2026E P/E 为 L3 冻结输入；Choice TTM 单独列示。EV完整桥仍为 PARTIAL。');
header(s,'A6:L6',['公司','Wind EV 亿元','2025A EBITDA','2025A收入','EV/2025A EBITDA','EV/2025A收入','2026E P/E冻结','Choice TTM P/E','Choice EV原值','Choice EV/1e8','EV跨源差','状态']);
d.companies.forEach((c,i)=>{let r=i+7;const cv=d.choice_snapshot.find(x=>x.CODES===c.code);s.getRange(`A${r}:L${r}`).values=[[c.name,c.ev_vendor,c.ebitda25,null,null,null,c.forward_pe26,cv.PETTM,cv.EV2MRQ,null,null,'W4/C3 PARTIAL']];formula(s,`D${r}`,`='公司财务'!D${r}`,true);formula(s,`E${r}`,`=B${r}/C${r}`);formula(s,`F${r}`,`=B${r}/D${r}`);formula(s,`J${r}`,`=I${r}/100000000`);formula(s,`K${r}`,`=J${r}-B${r}`);
 comment(s,`B${r}`,`W4 raw/wind-${c.slug}-ev.json；2026-09-02；供应商EV亿元；未重建完整桥。`);comment(s,`C${r}`,`W3 raw/wind-${c.slug}-fundamentals.json；2025A反推法EBITDA亿元。`);comment(s,`G${r}`,'L3 已有Wind Comps冻结的2026E P/E；原始机构样本及完整分布PARTIAL。');comment(s,`I${r}`,'C3 Choice EV2MRQ原数值；按与Wind的数量级交叉核对除1e8，单位及完整桥PARTIAL。');
});bands(s,7,13,'L');s.getRange('B7:K13').setNumberFormat(num);s.getRange('I7:I13').setNumberFormat('#,##0');s.getRange('K7:K13').setNumberFormat('0.0000;[Red](0.0000);"—"');s.getRange('A:A').format.columnWidth=16;s.getRange('I:I').format.columnWidth=22;s.getRange('L:L').format.columnWidth=20;
s.getRange('A15:L16').merge();s.getRange('A15').values=[['长飞 H列为A股TTM P/E，与混合市值口径不同。Choice长飞EVTOEBITDAFT=90.7213，Wind=91.1163；保留差异。EV/2025A收入不是TTM PS。']];s.getRange('A15').format.wrapText=true;
header(s,'A19:C19',['长飞输入','数值','单位与来源']);s.getRange('A20:C25').values=[['A股价格',407.8,'元/股 L3'],['H股价格',169.4,'港元/股 L3'],['港元兑人民币',.86497,'人民币/港元 L3'],['A股数量',406338314,'股 L3'],['H股数量',421566794,'股 L3'],['2026E归母净利',66.0945,'亿元 L3']];s.getRange('B20:B25').setNumberFormat('0.00000');s.getRange('B23:B24').setNumberFormat('#,##0');
header(s,'E19:H19',['派生结果','数值','单位','含义']);s.getRange('E20:H26').values=[['A股市值',null,'亿元','A价乘A股数'],['H股市值',null,'亿元','H价乘汇率乘H股数'],['混合市值',null,'亿元','不是全股本乘A价'],['2026E每股盈利',null,'元/股','期末股本法'],['A股2026E P/E',null,'倍','同一EPS'],['H股2026E P/E',null,'倍','同一EPS'],['混合2026E P/E',null,'倍','混合市值/净利']];
for(const [cell,f] of Object.entries({F20:'=B20*B23/100000000',F21:'=B21*B22*B24/100000000',F22:'=SUM(F20:F21)',F23:'=B25*100000000/SUM(B23:B24)',F24:'=B20/F23',F25:'=B21*B22/F23',F26:'=F22/B25'}))formula(s,cell,f);s.getRange('F20:F26').setNumberFormat(num);
header(s,'I19:L19',['并购会计桥','人民币元','性质','来源']);s.getRange('I20:L25').values=[['奔腾浙江现金支付',239959832,'已披露','W7'],['预期补偿资产',6154646,'已披露','W7'],['会计合并成本',null,'派生','W7'],['取得净资产份额',212998053,'已披露','W7'],['商誉',null,'派生','W7'],['取得净资产成本比',null,'不是EV倍数','DERIVED']];formula(s,'J22','=J20-J21');formula(s,'J24','=J22-J23');formula(s,'J25','=J22/J23');s.getRange('J20:J24').setNumberFormat('#,##0');s.getRange('J25').setNumberFormat('0.00"x"');
s.getRange('A29:L31').merge();s.getRange('A29').values=[['完整TTM EV桥 MISSING：现金、金融投资、有息债务、租赁负债、少数股东权益与合并范围尚未统一核对。不得以供应商字段名替代定义。全球CR5和交易EV倍数缺口见来源页。']];s.getRange('A29').format.wrapText=true;

s=sheets['历史估值'];style(s,'N',106,'历史估值 月末固定样本','C1/C2：Choice PETTM。2020至2025历史范围72个月末点；全序列81日期。固定样本中位数不是历史成分行业指数，存在选择偏差。');
header(s,'A6:N6',['日期',...d.companies.map(c=>c.name),'沪深300','核心组中位数','AI组中位数','月份文本','来源','长飞A股图源']);
const by=new Map(monthly.map(r=>[`${r.CODES}|${r.DATES}`,r.PETTM]));
d.valuation_history.forEach((row,i)=>{let r=i+7;const dt=row.date.replaceAll('/','-');s.getRange(`A${r}:N${r}`).values=[[new Date(`${dt}T00:00:00Z`),...d.companies.map(c=>by.get(`${c.code}|${row.date}`)),row.csi300,null,null,dt.slice(0,7),'C1/C2',null]];formula(s,`J${r}`,`=MEDIAN(C${r}:E${r})`);formula(s,`K${r}`,`=MEDIAN(F${r}:H${r})`);formula(s,`N${r}`,`=B${r}`);});
s.getRange('A7:A87').setNumberFormat('yyyy-mm-dd');s.getRange('B7:K87').setNumberFormat('0.00');s.getRange('N7:N87').setNumberFormat('0.00');s.getRange('A:A').format.columnWidth=17;s.getRange('J:K').format.columnWidth=18;s.getRange('N:N').format.columnWidth=18;
header(s,'A91:F91',['样本','2020至2025最低','历史中位','历史最高','2026-09-02','历史样本数']);
for(const [i,[name,col]] of [['核心组','J'],['AI组','K'],['长飞A股','B'],['沪深300','I']].entries()){let r=92+i;s.getRange(`A${r}`).values=[[name]];for(const [c,f] of [['B',`=MIN(${col}7:${col}78)`],['C',`=MEDIAN(${col}7:${col}78)`],['D',`=MAX(${col}7:${col}78)`],['E',`=${col}87`],['F',`=COUNT(${col}7:${col}78)`]])formula(s,`${c}${r}`,f);}s.getRange('B92:E95').setNumberFormat('0.00');
s.getRange('A98:D100').values=[['相对沪深300',null,'2026-09-02','同源同TTM'],['核心组',null,'倍','DERIVED'],['AI组',null,'倍','DERIVED']];formula(s,'B99','=J87/I87');formula(s,'B100','=K87/I87');s.getRange('B99:B100').setNumberFormat('0.00"x"');
const hist=s.charts.add('line',[s.getRange('L6:L87'),s.getRange('J6:J87'),s.getRange('K6:K87'),s.getRange('N6:N87'),s.getRange('I6:I87')]);hist.title='固定样本月末 TTM P/E';hist.setPosition('A108','N130');hist.xAxis={axisType:'textAxis'};hist.yAxis={numberFormatCode:'0',numberFormatSourceLinked:false};
for(const cell of ['B6','C6','D6','E6','F6','G6','H6'])comment(s,cell,'C1 raw/choice-peer-monthly.json；Choice CSD PETTM；Period=3；日期为返回的实际月末交易日加末端2026-09-02。');comment(s,'I6','C2 raw/choice-csi300-monthly.json；Choice CSD PETTM；DelType=1；不拼接Wind。');

s=sheets['来源与缺口'];style(s,'F',29,'来源与缺口登记','ACTUAL 为公司披露；供应商事实、转引预测、派生计算与缺失分开。完整原始回执及日志位于报告目录 raw/。');
header(s,'A6:F6',['编号','期间','数据内容','状态','来源文件或网址','限制']);
const sources=[
 ['W1/W2','2020至2026-07','中国光缆产量与官方同比','WIND-FACT','raw/wind-industry-series.json；wind-production-yoy.json','芯千米；不是全球需求；官方同比与绝对量变化分开'],
 ['W3','2025A / 2026H1','七公司收入及反推EBITDA','WIND-FACT / PARTIAL','raw/wind-*-fundamentals.json','反推法未正常化；报告期以字段为准'],
 ['W4','2026-09-02','企业价值及EV倍数核对','WIND-FACT / PARTIAL','raw/wind-*-ev.json','使用EV/FY2025；完整TTM EV桥缺失'],
 ['W5','2026-09-02','沪深300交叉核对','WIND-FACT','raw/wind-csi300.json','年末返回次年首个交易日；历史排除'],
 ['W6','2026-01-06等','CRU年初需求与地区旧预测','NEWS-CITED / PARTIAL','raw/wind-market-news.json','旧5.77亿不与新6.70亿拼接'],
 ['W7','2025年报','长飞两起并购及会计成本','ACTUAL / PARTIAL','raw/wind-acquisitions.json','无行业交易EV/EBITDA；公告文本提取'],
 ['C1/C2','2020至2026-09-02','七公司及沪深300月末PETTM','CHOICE-FACT','raw/choice-peer-monthly.json；choice-csi300-monthly.json','固定样本；72历史点及81完整日期；非PIT保证'],
 ['C3','2026-09-02','Choice CSS估值快照','CHOICE-FACT / PARTIAL','raw/choice-valuation.json','EV原数值单位交叉核对；长飞倍数未完全一致'],
 ['L1/L2','2026H1等','长飞分部、三表、CRU转引','ACTUAL / COMPANY-CITED','docs/yofc/01-FINANCIAL-METRICS.md；DATA-SOURCES.md','细分规格销量ASP仍缺失'],
 ['L3','2026-09-02','冻结2026E预测和P/E','WIND-FACT / PARTIAL','docs/yofc/13-WIND-COMPS-20260902.md','机构样本和分布未完整；比率已四舍五入'],
 ['L4','2025A / 2026H1','中天业务构成及现金回款','ACTUAL / BROKER-EST','docs/ztt/DATA-SOURCES.md','券商沟通不代替正式半年报分部'],
 ['L5','2026-07 / 08','ASP、供给及份额预测','BROKER-EST / PARTIAL','docs/yofc/10-FOUR-BROKER-INDUSTRY-COMPARISON.md','各自日期、口径；不可平均或拼接'],
 ['R1','2024版在用','G.657技术标准','官方标准','https://www.itu.int/rec/t-rec-g.657','弯曲不敏感单模，不等于AI专属或空芯'],
 ['R2/R3','2023 / 2025','欧盟光缆贸易措施','官方历史事件','欧盟委员会；REPORT.md第12节直接链接','未确认2026所有企业及原产地税率'],
 ['缺口','当前','全球收入TAM、CR5、份额历史','MISSING','Wind经济及新闻、本地券商已尝试','需同口径量价与厂商数据库'],
 ['缺口','当前','有效产能、良率、实际ASP','MISSING / PARTIAL','本地扩产表与公司披露','规划吨数不等于有效供给'],
 ['日志','2026-09-05','12条追加财务/EV逐字请求','PARTIAL','raw/requests.jsonl；DATA-SOURCES.md','部分首个探针未存逐字请求，原始回执保留'],
];s.getRange(`A7:F${6+sources.length}`).values=sources;s.getRange(`A7:F${6+sources.length}`).format={wrapText:true,rowHeight:66};
const widths=[12,22,30,24,55,53];widths.forEach((w,i)=>s.getRange(`${String.fromCharCode(65+i)}:${String.fromCharCode(65+i)}`).format.columnWidth=w);bands(s,7,23,'F');
s.getRange('A26:F28').merge();s.getRange('A26').values=[['复算：build_data.py从回执归一化，build_workbook.mjs写公式并导出。蓝字黄底仅为可编辑CAGR参数，绿字为跨表引用，黑字为其他公式。报告目录 DATA-SOURCES.md 记录完整方法、接受/排除字段及查询复现规范。']];s.getRange('A26').format.wrapText=true;

const fwd=sheets['公司财务'];
fwd.getRange('A34:L45').format={font:{name:'Arial',size:10},rowHeight:24};
header(fwd,'A34:I34',['公司','2026E收入','2026E归母净利','冻结市值','复算2026E P/E','原底稿P/E','舍入差','2026E收入增速','来源']);
d.companies.forEach((c,i)=>{const r=35+i,pr=7+i;fwd.getRange(`A${r}:I${r}`).values=[[c.name,c.forecast_rev26,c.forecast_np26,c.market_cap,null,c.forward_pe26,null,null,'L3 PARTIAL']];formula(fwd,`E${r}`,`=D${r}/C${r}`);formula(fwd,`G${r}`,`=E${r}-F${r}`);formula(fwd,`H${r}`,`=B${r}/D${pr}-1`);for(const col of ['B','C','D','F'])comment(fwd,`${col}${r}`,'L3 docs/yofc/13-WIND-COMPS-20260902.md；2026-09-02冻结输入；机构样本PARTIAL，长飞市值为A/H混合。');});
fwd.getRange('B35:G41').setNumberFormat(num);fwd.getRange('H35:H41').setNumberFormat(pct);bands(fwd,35,41,'I');
fwd.getRange('A43:L44').merge();fwd.getRange('A43').values=[['前瞻收入增速 = 2026E收入/2025A收入 − 1，不是H1同比。复算P/E与原表的微小差异来自原底稿输入与倍数精度；不同日期和来源的预测不平均。']];fwd.getRange('A43').format.wrapText=true;
const bs=sheets['投行研报'];style(bs,'J',40,'五家投行 六份报告','B1至B6保留原报告时点；目标价为投行原观点，不是本研究目标价。预测口径不同，不平均成市场共识。');
header(bs,'A6:J6',['公司','投行','报告日期','原评级','原目标价','币种','方法','主要判断','复算边界','来源']);
brokers.forEach((b,i)=>{const r=i+7;bs.getRange(`A${r}:J${r}`).values=[[b.company,b.bank,b.date,b.rating,b.target,b.currency,b.method,b.thesis,b.gap,`B${i+1}`]];comment(bs,`E${r}`,`B${i+1} ${b.source}；原报告${b.date}；币种${b.currency}；未按9月2日重新估值。`);});bs.getRange('A7:J12').format={wrapText:true,rowHeight:65};bs.getRange('E7:E12').setNumberFormat('0.00');bands(bs,7,12,'J');
header(bs,'A16:J16',['公司','投行','2026E收入','2026E净利','2027E净利','2028E净利','2026E净利率','净利润口径','状态','来源']);
brokers.forEach((b,i)=>{const r=i+17;bs.getRange(`A${r}:J${r}`).values=[[b.company,b.bank,b.revenue[0]??'MISSING',b.profit[0]??'MISSING',b.profit[1]??'MISSING',b.profit[2]??'MISSING',null,b.profit_basis,'BROKER-EST / PARTIAL',`B${i+1}`]];if(b.revenue[0]!==null)formula(bs,`G${r}`,`=D${r}/C${r}`);else bs.getRange(`G${r}`).values=[['MISSING']];for(const col of ['C','D','E','F'])comment(bs,`${col}${r}`,`B${i+1} ${b.source}；原财务百万元除100，转人民币亿元；保留${b.date}信息集及${b.profit_basis}口径。`);});bs.getRange('C17:F22').setNumberFormat(num);bs.getRange('G17:G22').setNumberFormat(pct);bs.getRange('A17:J22').format={rowHeight:45,wrapText:true};bands(bs,17,22,'J');
header(bs,'A26:G26',['中天对照','2027E收入','2027E净利','2027E EBITDA','2027E EBITDA率','WACC','永续增长']);
bs.getRange('A27:G28').values=[['大摩 2026-07-14',722.52,83.06,107.73,null,.0967,.02],['美银 2026-08-28',839.24,130.99,160.941,null,.09,.03]];for(const r of [27,28])formula(bs,`E${r}`,`=D${r}/B${r}`);bs.getRange('B27:D28').setNumberFormat(num);bs.getRange('E27:G28').setNumberFormat('0.00%');bs.getRange('A30:D31').values=[['美银相对大摩 收入',null,'净利润',null],['仅描述原报告差异',null,'不是同口径共识',null]];formula(bs,'B30','=B28/B27-1');formula(bs,'D30','=C28/C27-1');bs.getRange('B30:D30').setNumberFormat(pct);
bs.getRange('A34:J37').merge();bs.getRange('A34').values=[['野村仅披露FY27 EPS 9.75元，年度收入和净利润留MISSING。长飞报告目标价以港元计，中天以人民币计；不跨币种求均值。利润率为各自报告内派生值，ModelWare与美银调整后净利润尚未统一调整桥。B1至B6的单家案例链接及原报告页码见HTML第12与13节、broker_data.json和DATA-SOURCES.md。']];bs.getRange('A34').format.wrapText=true;
for(const [col,w] of [['A',20],['B',19],['C',17],['G',26],['H',37],['I',40],['J',14]])bs.getRange(`${col}:${col}`).format.columnWidth=w;
sheets['来源与缺口'].getRange('A25:F25').values=[['B1至B6','2026-07 / 08','五家投行六份报告','BROKER-EST / PARTIAL','broker_data.json；REPORT.md第12节','保留原日期、币种、方法和利润口径']];sheets['来源与缺口'].getRange('A25:F25').format={wrapText:true,rowHeight:55};
sheets['行业需求'].getRange('G21:G22').setNumberFormat('0.00%');
sheets['行业需求'].getRange('B14').setNumberFormat('0.00%;[Red](0.00%)');
sheets['估值快照'].getRange('E20:L26').format={wrapText:true,rowHeight:34};
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#N/A|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:200},maxChars:4000});await fs.writeFile(path.join(qa,'error-scan.json'),JSON.stringify(errors,null,2));
const checks={};for(const [name,range] of [['行业需求','A14:C16'],['估值快照','E20:H26'],['历史估值','A91:F100']])checks[name]=await wb.inspect({kind:'region',sheetId:name,range,maxChars:6000});await fs.writeFile(path.join(qa,'formula-checks.json'),JSON.stringify(checks,null,2));
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(out,'行业数据与估值附录.xlsx'));
for(const [name,range,suffix] of [['公司财务','A1:L30','full'],['公司财务','A34:L44','forecasts'],['行业需求','A1:L47','full'],['估值快照','A1:L31','full'],['历史估值','A1:N16','top'],['历史估值','A76:N100','tail'],['历史估值','A108:N130','chart'],['来源与缺口','A1:F28','full'],['投行研报','A1:J22','top'],['投行研报','A26:J37','detail']]){
 const blob=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(path.join(qa,`${name}-${suffix}.png`),new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify({output:path.join(out,'行业数据与估值附录.xlsx'),errors,checks},null,2));
