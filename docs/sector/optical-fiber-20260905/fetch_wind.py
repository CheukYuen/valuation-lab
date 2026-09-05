"""Supplementary Wind requests; serial, stop a batch on an error envelope."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = Path(__file__).resolve().parent / 'raw'
SKILL = ROOT / '.agents/skills/wind-mcp-skill'
COMPANIES = [('ztt', '中天科技600522.SH'), ('hengtong', '亨通光电600487.SH'),
             ('fiberhome', '烽火通信600498.SH'), ('innolight', '中际旭创300308.SZ'),
             ('accelink', '光迅科技002281.SZ'), ('tfc', '天孚通信300394.SZ')]

def call(name, domain, tool, params):
    path = RAW / (name + '.json')
    if path.exists():
        return json.loads(path.read_text())
    result = subprocess.run(['node', 'scripts/cli.mjs', 'call', domain, tool,
                             json.dumps(params, ensure_ascii=False)], cwd=SKILL,
                            capture_output=True, text=True)
    path.write_text(result.stdout)
    data = json.loads(result.stdout)
    with (RAW / 'requests.jsonl').open('a') as f:
        f.write(json.dumps({'output': path.name, 'domain': domain, 'tool': tool,
                            'params': params}, ensure_ascii=False) + '\n')
    if result.returncode or data.get('ok') is False or data.get('isError'):
        raise RuntimeError(f'{name}: request failed; see raw receipt')
    print(name + ': received', flush=True)
    return data

if __name__ == '__main__':
    for slug, company in COMPANIES:
        call('wind-' + slug + '-fundamentals', 'stock_data', 'get_stock_fundamentals',
             {'question': f'查询{company}，2025年年报和2026年半年报的合并营业收入、EBIT正推法、EBIT反推法、EBITDA反推法、折旧摊销；以及2020、2021、2022、2023、2024、2025各年最后交易日和2026-09-02的PE TTM。请逐项返回报告期或交易日期、单位和字段定义，缺失留空。'})
