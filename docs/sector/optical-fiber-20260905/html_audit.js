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
for(const [key,c] of cellMap)if(c.formula){const el=document.getElementById('calc-'+key);const deps=dependencies.get(key);el.innerHTML=`<p>公式：<code>${esc(c.formula)}</code></p><p>代入值：${deps.map(d=>`${esc(d.key)} = ${esc(d.value)}`).join('；')}</p><p>计算结果：${esc(results.get(key))}；原缓存：${esc(c.value)}</p><p>输入来源批注：${esc([...new Set(provenance(key))].join('；')||'输入未附单元格批注，见同表口径和来源台账；不补造来源。')}</p>`;}
function filterRows(){const q=document.getElementById('data-search').value.toLowerCase(),sheet=document.getElementById('sheet-filter').value;let n=0;document.querySelectorAll('.audit-cell').forEach(r=>{r.hidden=(sheet&&r.dataset.sheet!==sheet)||!r.textContent.toLowerCase().includes(q);if(!r.hidden)n++;});document.getElementById('data-count').textContent=n+' 个单元格';if(q||sheet)document.querySelectorAll('#full-data > details').forEach(d=>{d.open=!!d.querySelector('.audit-cell:not([hidden])');});}
document.getElementById('data-search').addEventListener('input',filterRows);document.getElementById('sheet-filter').addEventListener('change',filterRows);filterRows();
let printState=[];addEventListener('beforeprint',()=>{printState=[...document.querySelectorAll('details')].map(d=>[d,d.open]);document.querySelectorAll('details.print-open').forEach(d=>d.open=true);});addEventListener('afterprint',()=>printState.forEach(([d,o])=>d.open=o));
