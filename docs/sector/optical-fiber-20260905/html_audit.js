const audit=JSON.parse(document.getElementById('research-data').textContent);
const cellMap=new Map(audit.workbook.sheets.flatMap(s=>s.cells.map(c=>[s.name+'!'+c.ref,{...c,sheet:s.name}])));
const results=new Map(),dependencies=new Map();
function calculate(key,stack=new Set()){
 if(results.has(key))return results.get(key);
 const cell=cellMap.get(key);if(!cell)throw Error('Missing cell '+key);
 if(!cell.formula)return cell.value;
 if(stack.has(key))throw Error('Circular '+key);stack=new Set(stack).add(key);
 const expr=cell.formula.replaceAll('$','');let pos=0;const deps=[];
 function ws(){while(/\s/.test(expr[pos]||'')&&pos<expr.length)pos++;}
 function take(s){ws();if(expr.slice(pos,pos+s.length)===s){pos+=s.length;return true;}return false;}
 function ref(r,s=cell.sheet){const k=s+'!'+r;const v=calculate(k,stack);deps.push({key:k,value:v});return v;}
 function primary(){ws();if(take('(')){const x=add();if(!take(')'))throw Error(')');return x;}if(take('-'))return -primary();if(take('+'))return primary();
 let m=expr.slice(pos).match(/^(SUM|MEDIAN|MIN|MAX|COUNT)\(/);if(m){pos+=m[0].length;let args=[];do{args.push(add());}while(take(','));if(!take(')'))throw Error('function )');const nums=args.flat().filter(v=>typeof v==='number');if(m[1]==='SUM')return nums.reduce((a,b)=>a+b,0);if(m[1]==='COUNT')return nums.length;if(m[1]==='MIN')return Math.min(...nums);if(m[1]==='MAX')return Math.max(...nums);nums.sort((a,b)=>a-b);return nums.length%2?nums[(nums.length-1)/2]:(nums[nums.length/2-1]+nums[nums.length/2])/2;}
 m=expr.slice(pos).match(/^(?:'([^']+)'!)?([A-Z]+\d+)(?::([A-Z]+\d+))?/);if(m){pos+=m[0].length;if(!m[3])return ref(m[2],m[1]);const col=n=>[...n].reduce((a,c)=>26*a+c.charCodeAt(0)-64,0);const letters=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};const a=m[2].match(/([A-Z]+)(\d+)/),b=m[3].match(/([A-Z]+)(\d+)/),v=[];for(let r=+a[2];r<=+b[2];r++)for(let c=col(a[1]);c<=col(b[1]);c++)v.push(ref(letters(c)+r,m[1]));return v;}
 m=expr.slice(pos).match(/^\d+(?:\.\d+)?/);if(m){pos+=m[0].length;return Number(m[0]);}throw Error('Unsupported formula '+expr.slice(pos));}
 function power(){let v=primary();if(take('^'))v=v**power();return v;}
 function mul(){let v=power();for(;;){if(take('*'))v*=power();else if(take('/'))v/=power();else return v;}}
 function add(){let v=mul();for(;;){if(take('+'))v+=mul();else if(take('-'))v-=mul();else return v;}}
 const value=add();ws();if(pos!==expr.length||!Number.isFinite(value))throw Error('Invalid '+key);results.set(key,value);dependencies.set(key,deps);return value;
}
const checks=[];for(const [key,c] of cellMap)if(c.formula){const actual=calculate(key);checks.push({key,expected:c.value,actual,pass:Math.abs(actual-c.value)<=Math.max(1e-8,Math.abs(c.value)*1e-9)});}
window.auditVerification={...audit.workbook.counts,checks,pass:checks.every(c=>c.pass)};
document.getElementById('calc-status').textContent=`${checks.length} 个公式复算：${checks.every(c=>c.pass)?'全部与原缓存一致':'存在差异，请核查'}`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function provenance(key,seen=new Set()){if(seen.has(key))return [];seen.add(key);const c=cellMap.get(key);return [c?.comment,...(dependencies.get(key)||[]).flatMap(d=>provenance(d.key,seen))].filter(Boolean);}
for(const [key,c] of cellMap)if(c.formula){const el=document.getElementById('calcbody-'+key);const deps=dependencies.get(key);el.innerHTML=`<p>公式：<code>${esc(c.formula)}</code></p><p>代入值：${deps.map(d=>`${esc(d.key)} = ${esc(d.value)}`).join('；')}</p><p>计算结果：${esc(results.get(key))}；原缓存：${esc(c.value)}</p><p>输入来源批注：${esc([...new Set(provenance(key))].join('；')||'输入未附单元格批注，见同表口径和来源台账；不补造来源。')}</p>`;}
function filterRows(){const q=document.getElementById('data-search').value.toLowerCase(),sheet=document.getElementById('sheet-filter').value;let n=0;document.querySelectorAll('.audit-cell').forEach(r=>{r.hidden=(sheet&&r.dataset.sheet!==sheet)||!r.textContent.toLowerCase().includes(q);if(!r.hidden)n++;});document.getElementById('data-count').textContent=n+' 个单元格';document.querySelectorAll('#full-data > details[data-sheet-block]').forEach(d=>{d.hidden=!!sheet&&d.dataset.sheetBlock!==sheet;});if(q||sheet)document.querySelectorAll('#full-data > details[data-sheet-block]').forEach(d=>{const hit=!!d.querySelector('.audit-cell:not([hidden])');d.open=hit;const l=d.querySelector('details.ledger');if(l)l.open=hit&&!!q;});document.querySelectorAll('.xlgrid .xs').forEach(c=>c.classList.toggle('hit',!!q&&(c.dataset.raw||'').toLowerCase().includes(q)));}
document.getElementById('data-search').addEventListener('input',filterRows);document.getElementById('sheet-filter').addEventListener('change',filterRows);filterRows();
// The ƒ marks in the grid link to <details> blocks, which do not open on navigation by themselves.
const openHashTarget=()=>{if(!location.hash)return;const el=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(el&&el.tagName==='DETAILS'){el.open=true;el.scrollIntoView({block:'center'});}};
addEventListener('hashchange',openHashTarget);openHashTarget();
let printState=[];addEventListener('beforeprint',()=>{printState=[...document.querySelectorAll('details')].map(d=>[d,d.open]);document.querySelectorAll('details.print-open').forEach(d=>d.open=true);});addEventListener('afterprint',()=>printState.forEach(([d,o])=>d.open=o));

// Grid interaction for the static worksheet tables: sort a block by one of its columns,
// filter rows, drag column widths, pin the first column. No library; the markup stays a
// real <table>, so Ctrl+F, printing and copy-into-Excel keep working.
(()=>{
const colIndex=ref=>[...ref.split('!').pop().match(/[A-Z]+/)[0]].reduce((n,c)=>26*n+c.charCodeAt(0)-64,0);
const colLetter=ref=>ref.split('!').pop().match(/[A-Z]+/)[0];
const num=v=>{const n=Number(v);return v!==''&&v!==null&&v!==undefined&&Number.isFinite(n)?n:null;};

for(const wrap of document.querySelectorAll('.grid-wrap')){
 const table=wrap.querySelector('table.xlgrid');if(!table)continue;
 const body=table.tBodies[0];if(!body)continue;
 [...body.rows].forEach((tr,i)=>tr.dataset.order=i);

 const tools=document.createElement('div');
 tools.className='grid-tools';
 tools.innerHTML='<label>筛选本表 <input type="search" placeholder="值、公司或来源"></label>'
  +'<label><input type="checkbox"> 冻结首列</label>'
  +'<button type="button">还原顺序</button>'
  +'<span class="count" role="status"></span>';
 wrap.before(tools);
 const [search,pin]=tools.querySelectorAll('input'),reset=tools.querySelector('button'),count=tools.querySelector('.count');

 const dataRows=()=>[...body.querySelectorAll('tr[data-kind="data"]')];
 const report=()=>{const all=dataRows();count.textContent=all.filter(r=>!r.hidden).length+' / '+all.length+' 行';};

 const filter=()=>{const q=search.value.trim().toLowerCase();
  for(const tr of dataRows())tr.hidden=!!q&&!tr.textContent.toLowerCase().includes(q);
  report();};
 search.addEventListener('input',filter);

 pin.addEventListener('change',()=>table.classList.toggle('freeze-col',pin.checked));

 // Sorting is per block: a dark header band starts a block, and only that block's rows move.
 // Row numbers travel with their data so every data-ref stays truthful.
 let sortState=null;
 const place=(rows,ordered)=>{const parent=rows[0].parentNode;
  const slots=rows.map(r=>{const c=document.createComment('');parent.replaceChild(c,r);return c;});
  ordered.forEach((r,i)=>parent.replaceChild(r,slots[i]));};
 const clearMarks=()=>table.querySelectorAll('.sorted-asc,.sorted-desc').forEach(e=>e.classList.remove('sorted-asc','sorted-desc'));
 const sortBlock=(block,letter,cell)=>{
  const rows=[...body.querySelectorAll('tr[data-kind="data"][data-block="'+block+'"]')];
  if(rows.length<2)return;
  const dir=sortState&&sortState.block===block&&sortState.letter===letter?sortState.dir+1:1;
  clearMarks();
  if(dir>2){sortState=null;place(rows,[...rows].sort((a,b)=>a.dataset.order-b.dataset.order));report();return;}
  sortState={block,letter,dir};
  cell.classList.add(dir===1?'sorted-asc':'sorted-desc');
  const key=tr=>{const td=tr.querySelector('[data-ref$="!'+letter+tr.dataset.row+'"]');
   if(!td)return null;
   return td.dataset.raw!==undefined?td.dataset.raw:td.textContent.trim();};
  const sorted=[...rows].sort((a,b)=>{
   const x=key(a),y=key(b);
   if(x===null||x==='')return y===null||y===''?a.dataset.order-b.dataset.order:1;
   if(y===null||y==='')return -1;
   const nx=num(x),ny=num(y);
   const c=nx!==null&&ny!==null?nx-ny:String(x).localeCompare(String(y),'zh');
   return (c||a.dataset.order-b.dataset.order)*(dir===1?1:-1);});
  place(rows,sorted);report();};

 table.addEventListener('click',e=>{
  const cell=e.target.closest('tr[data-kind="head"] .xs');
  if(!cell||!cell.dataset.ref)return;
  const block=cell.parentElement.dataset.block;
  if(block)sortBlock(block,colLetter(cell.dataset.ref),cell);});

 reset.addEventListener('click',()=>{clearMarks();sortState=null;search.value='';
  const rows=[...body.rows];place(rows,[...rows].sort((a,b)=>a.dataset.order-b.dataset.order));
  rows.forEach(r=>r.hidden=false);report();});

 // Column resize by dragging the right edge of the column-letter header.
 const cols=[...table.querySelectorAll('colgroup col')];
 table.querySelectorAll('.rz').forEach(handle=>{
  handle.addEventListener('pointerdown',e=>{
   e.preventDefault();e.stopPropagation();
   const th=handle.parentElement,i=[...th.parentElement.children].indexOf(th),col=cols[i];
   if(!col)return;
   const x0=e.clientX,w0=th.getBoundingClientRect().width;
   handle.setPointerCapture(e.pointerId);
   const move=ev=>{col.style.width=Math.max(28,Math.round(w0+ev.clientX-x0))+'px';};
   const up=()=>{handle.removeEventListener('pointermove',move);handle.removeEventListener('pointerup',up);};
   handle.addEventListener('pointermove',move);handle.addEventListener('pointerup',up);});});

 report();
}
})();
