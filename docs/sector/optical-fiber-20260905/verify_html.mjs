import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const base=process.argv[2];if(!base)throw new Error('Provide report directory');
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
await page.context().setOffline(true);
await page.goto(pathToFileURL(path.join(base,'index.html')).href);
const status=await page.evaluate(()=>({pass:window.auditVerification.pass,formulas:window.auditVerification.checks.length,cells:document.querySelectorAll('.audit-cell').length,svg:document.querySelectorAll('svg').length,sections:document.querySelectorAll('main section').length,images:document.images.length,overflow:document.documentElement.scrollWidth>innerWidth}));
if(!status.pass||status.formulas!==379||status.cells!==2024||status.svg!==8||status.sections!==16||status.images||status.overflow)throw Error(JSON.stringify(status));
Object.assign(status,await page.evaluate(()=>({grid:document.querySelectorAll('[data-ref]').length,merges:document.querySelectorAll('.xlgrid [rowspan],.xlgrid [colspan]').length})));
// Expected grid-cell counts are derived from the embedded workbook, not hard-coded.
const expected=await page.evaluate(()=>{
 const a=JSON.parse(document.getElementById('research-data').textContent);
 const idx=r=>[...r.match(/[A-Z]+/)[0]].reduce((n,c)=>26*n+c.charCodeAt(0)-64,0);
 const row=r=>+r.match(/[0-9]+/)[0];
 let cells=0,spans=0;
 for(const sheet of a.workbook.sheets){
  const st=a.workbook.style.sheets.find(s=>s.name===sheet.name);
  const covered=new Set();
  for(const m of sheet.merges){
   const [x,y]=m.split(':');spans++;
   for(let r=row(x);r<=row(y);r++)for(let c=idx(x);c<=idx(y);c++)if(!(r===row(x)&&c===idx(x)))covered.add(r+':'+c);
  }
  cells+=st.max_row*st.max_col-covered.size;
 }
 return {cells,spans};
});
if(status.grid!==expected.cells||status.merges!==expected.spans)throw Error('Grid '+JSON.stringify({status,expected}));
// Number formats are rendered at build time, so the displayed text must match Excel exactly.
const oracle=[['公司财务!H7','45.6%'],['估值快照!B7','2,310.60'],['历史估值!A7','2020-01-23'],['行业需求!B7','288,777,000'],['估值快照!J25','1.10x'],['公司财务!J9','(27.7%)'],['公司财务!E19','(7.95)']];
for(const [ref,want] of oracle){
 const got=await page.evaluate(r=>{const c=document.querySelector(`[data-ref="${r}"]`);return c&&c.textContent.replace('ƒ','').trim();},ref);
 if(got!==want)throw Error(`Format ${ref}: ${JSON.stringify(got)} != ${want}`);}
for(const ref of ['公司财务!J9','公司财务!E19'])
 if(!await page.evaluate(r=>document.querySelector(`[data-ref="${r}"]`).classList.contains('neg'),ref))throw Error('Missing red '+ref);
if(!await page.evaluate(()=>document.querySelector('[data-ref="公司财务!D7"]').title.length))throw Error('Missing source comment on grid cell');
// Frozen header rows must actually stick inside the scroll container.
{
 // Column widths come from the workbook. Layout is auto, so a column may grow when a cell's
 // text exceeds it — Excel spills such text into the empty neighbour instead. Neither hides it.
 const widths=await page.evaluate(()=>{
  document.querySelectorAll('#full-data > details[data-sheet-block]').forEach(d=>d.open=true);
  const narrow=[],wide=[];
  for(const d of document.querySelectorAll('#full-data > details[data-sheet-block]')){
   const t=d.querySelector('table.xlgrid');if(!t)continue;
   const cols=[...t.querySelectorAll('colgroup col')],th=[...t.querySelectorAll('thead tr.axis th')];
   cols.forEach((c,i)=>{if(!i)return;const want=parseFloat(c.style.width);if(!want)return;
    const got=th[i].getBoundingClientRect().width;
    if(got<want-1)narrow.push(d.dataset.sheetBlock+'!'+th[i].textContent);
    else if(got>want+1)wide.push(d.dataset.sheetBlock+'!'+th[i].textContent);});}
  return {narrow,wide};});
 if(widths.narrow.length)throw Error('Columns narrower than the workbook: '+widths.narrow);
 if(widths.wide.join()!=='行业需求!F,行业需求!K')throw Error('Unexpected widened columns: '+JSON.stringify(widths.wide));
 // Grid tools: sorting stays inside its own block, filtering hides only data rows,
 // pinning makes column A sticky, and dragging a header edge resizes that column.
 const grid=await page.evaluate(async()=>{
  const S='#full-data > details[data-sheet-block="公司财务"]';
  const read=l=>[...document.querySelectorAll(S+' .xlgrid tr[data-kind="data"][data-block="1"]')]
   .filter(r=>!r.hidden).map(r=>{const c=r.querySelector('[data-ref$="!'+l+r.dataset.row+'"]');return c&&c.dataset.raw;});
  const head=document.querySelector(S+' .xlgrid tr[data-kind="head"] [data-ref="公司财务!D6"]');
  const other=()=>[...document.querySelectorAll(S+' .xlgrid tr[data-block="2"][data-kind="data"]')].map(r=>r.dataset.row).join();
  const before=read('D'),otherBefore=other();
  head.click();const asc=read('D');
  head.click();const desc=read('D');
  head.click();const restored=read('D');
  const box=document.querySelector(S+' .grid-tools input[type=search]');
  box.value='AI映射';box.dispatchEvent(new Event('input',{bubbles:true}));
  const filtered=read('A').length;
  box.value='';box.dispatchEvent(new Event('input',{bubbles:true}));
  const pin=document.querySelector(S+' .grid-tools input[type=checkbox]');
  pin.click();
  const pinned=getComputedStyle(document.querySelector('[data-ref="公司财务!A7"]')).position;
  pin.click();
  return {sortedAsc:String(asc)===String([...before].sort((a,b)=>a-b)),
   sortedDesc:String(desc)===String([...before].sort((a,b)=>b-a)),
   restored:String(restored)===String(before),
   blockIsolated:other()===otherBefore,filtered,pinned,
   marks:document.querySelectorAll(S+' .sorted-asc,'+S+' .sorted-desc').length};});
 if(!grid.sortedAsc||!grid.sortedDesc||!grid.restored)throw Error('Grid sort '+JSON.stringify(grid));
 if(!grid.blockIsolated)throw Error('Sort leaked into another block');
 if(grid.filtered!==3)throw Error('Grid filter kept '+grid.filtered+' rows');
 if(grid.pinned!=='sticky')throw Error('Pin first column did not stick');
 if(grid.marks!==0)throw Error('Sort indicator left behind after restore');
 const handle=page.locator('#full-data > details[data-sheet-block="公司财务"] .xlgrid th[data-col="A"] .rz');
 await handle.scrollIntoViewIfNeeded();
 const hb=await handle.boundingBox();
 const colWidth=()=>page.evaluate(()=>document.querySelector('#full-data > details[data-sheet-block="公司财务"] .xlgrid colgroup col:nth-child(2)').style.width);
 const w0=await colWidth();
 await page.mouse.move(hb.x+3,hb.y+hb.height/2);await page.mouse.down();
 await page.mouse.move(hb.x+83,hb.y+hb.height/2,{steps:4});await page.mouse.up();
 const w1=await colWidth();
 if(parseFloat(w1)-parseFloat(w0)<60)throw Error('Column resize '+w0+' -> '+w1);
 await page.evaluate(()=>document.querySelector('#full-data > details[data-sheet-block="公司财务"] .grid-tools button').click());

 // ƒ marks must actually open the calculation they point at.
 const opened=await page.evaluate(async()=>{const a=document.querySelector('.xlgrid .fmark');a.click();
  await new Promise(r=>setTimeout(r,100));
  return document.getElementById(decodeURIComponent(a.hash.slice(1))).open;});
 if(!opened)throw Error('Formula mark did not open its calculation');
 const frozen=await page.evaluate(()=>{const d=document.querySelector('#full-data > details[data-sheet-block="历史估值"]');d.open=true;const w=d.querySelector('.grid-wrap');w.scrollTop=900;const h=w.querySelector('[data-ref="历史估值!A6"]');return Math.round(h.getBoundingClientRect().top-w.getBoundingClientRect().top);});
 if(frozen<0||frozen>260)throw Error('Freeze pane offset '+frozen);
}
for(const [name,n] of [['长飞光纤',4],['中天科技',2],['全部',6]]){await page.getByRole('button',{name,exact:true}).click();if(await page.locator('.broker-table').first().locator('tbody tr:visible').count()!==n)throw Error('Broker filter');}
await page.selectOption('#sheet-filter','公司财务');await page.fill('#data-search','长飞');if(!await page.evaluate(()=>[...document.querySelectorAll('.audit-cell:not([hidden])')].every(r=>r.dataset.sheet==='公司财务'&&r.textContent.includes('长飞'))))throw Error('Data filter');
if(await page.locator('.audit-cell:not([hidden])').count()===0)throw Error('Empty filter');
await page.selectOption('#sheet-filter','');await page.fill('#data-search','');
await page.locator('#calculations details').first().locator('summary').click();if(!await page.locator('#calculations details').first().textContent().then(s=>s.includes('代入值')&&s.includes('计算结果')))throw Error('Formula detail');
await page.locator('#sources details').first().locator('summary').click();
await page.setViewportSize({width:390,height:844});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
await page.emulateMedia({media:'print'});if(await page.locator('svg').count()!==8)throw Error('Print charts');
// Printing narrows the grid columns, so grid cells must wrap and never clip on paper.
await page.evaluate(()=>dispatchEvent(new Event('beforeprint')));
await page.waitForTimeout(600);
const printGrid=await page.evaluate(()=>{
 const bad=[];
 for(const td of document.querySelectorAll('.xlgrid td.xs,.xlgrid th.xs')){
  const cs=getComputedStyle(td);
  if(cs.overflow!=='visible'||cs.whiteSpace==='nowrap'){bad.push(td.dataset.ref);if(bad.length>3)break;}}
 return {bad,open:document.querySelectorAll('#full-data > details[data-sheet-block][open]').length};});
if(printGrid.bad.length)throw Error('Grid clips in print: '+printGrid.bad);
if(printGrid.open!==6)throw Error('Print did not open every sheet: '+printGrid.open);
if(errors.length||requests.length!==1)throw Error(JSON.stringify({errors,requests}));
console.log(JSON.stringify({status:'PASS',...status,offline:true,mobile:true,filters:true,details:true,print_css:true,requests:requests.length,errors}));await browser.close();
