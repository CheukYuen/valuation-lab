"""Hand-written oracle for the twelve number formats in the optical-fibre archive workbook.

The engine lives in docs/sector/optical-fiber-20260905/html_audit.py.

Expected strings are what Excel/Numbers renders, not what openpyxl reports; openpyxl
exposes only the raw value and the format code, never the displayed text.
"""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'docs/sector/optical-fiber-20260905'))
from html_audit import render

MONEY='#,##0.00;[Red](#,##0.00);"—"'
PCT1='0.0%;[Red](0.0%);"—"'
PCT2R='0.00%;[Red](0.00%)'
FOUR='0.0000;[Red](0.0000);"—"'
CASES=[
 # value, format, expected text, expected red
 (2310.5978,MONEY,'2,310.60',False),
 (-7.949999999999999,MONEY,'(7.95)',True),
 (0,MONEY,'—',False),
 (0.45622879489772616,PCT1,'45.6%',False),
 (-0.27699999999999997,PCT1,'(27.7%)',True),
 ('2020-01-23T00:00:00','yyyy-mm-dd','2020-01-23',False),
 ('2026-09-02T00:00:00','yyyy-mm-dd','2026-09-02',False),
 (288777000,'#,##0','288,777,000',False),
 (321816000,'#,##0','321,816,000',False),
 (27.527401,'0.00','27.53',False),
 (13.216643,'0.00','13.22',False),
 (1.49,'0.0','1.5',False),
 (2.88777,'0.00000','2.88777',False),
 (2.88777,'0.0','2.9',False),
 (0.063,'0.00%','6.30%',False),
 (0.1234,'0.00%','12.34%',False),
 (-0.0123,PCT2R,'(1.23%)',True),
 (0.0123,PCT2R,'1.23%',False),
 (0.5361,FOUR,'0.5361',False),
 (-0.5361,FOUR,'(0.5361)',True),
 (1.0976869633639328,'0.00"x"','1.10x',False),
 (8.597684394722584,'0.00"x"','8.60x',False),
 (142.521,'General','142.521',False),
 ('长飞光纤','General','长飞光纤',False),
]

class FormatOracle(unittest.TestCase):
 def test_cases(self):
  for value,code,text,red in CASES:
   with self.subTest(value=value,code=code):
    self.assertEqual(render(value,code),(text,red))

 def test_blank_is_never_the_zero_placeholder(self):
  # The workbook holds no zero-valued cells, so "—" must never reach an empty cell.
  self.assertEqual(render(None,MONEY),('',False))

if __name__=='__main__':unittest.main()
