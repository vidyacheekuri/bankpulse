"""Validate exported workbook contracts without relying on Excel desktop."""
from pathlib import Path
from zipfile import ZipFile
import json,posixpath
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def package():
    with ZipFile(ROOT/'excel/BankPulse.xlsx') as z:return {n:z.read(n) for n in z.namelist()}

def value(parts,sheet,cell):
    root=ET.fromstring(parts[f'xl/worksheets/sheet{sheet}.xml'])
    return root.find(f'.//s:c[@r="{cell}"]/s:v',NS).text

def test_relationship_integrity_and_no_formula_error_values():
    parts=package()
    for name,content in parts.items():
        if name.endswith(('.xml','.rels')):ET.fromstring(content)
        if name.endswith('.rels'):
            base=posixpath.dirname(posixpath.dirname(name))
            for rel in ET.fromstring(content):
                if rel.get('TargetMode')=='External':continue
                target=rel.get('Target')
                dest=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(base,target))
                assert dest in parts,(name,dest)
        if name.startswith('xl/worksheets/') and name.endswith('.xml'):
            assert not ET.fromstring(content).findall('.//s:c[@t="e"]',NS),name

def test_saved_workbook_values_reconcile_with_pipeline():
    p=package();q=json.loads((ROOT/'reports/quality.json').read_text())
    assert float(value(p,2,'B35'))==q['complete']['complaints']
    assert float(value(p,2,'D35'))==q['complete']['known']
    assert abs(float(value(p,2,'E35'))-q['complete']['timely_rate'])<1e-12
    for cell in ['J18','J19','J20']:assert float(value(p,2,cell))==0
    assert float(value(p,3,'E8'))==60
    assert float(value(p,3,'E10'))==0
    assert float(value(p,4,'B33'))==q['complete']['complaints']

def test_pivot_cache_matches_full_monthly_population():
    p=package();payload=json.loads((ROOT/'excel/inputs.json').read_text())
    cache=ET.fromstring(p['xl/pivotCache/pivotCacheRecords1.xml'])
    assert len(cache)==int(cache.get('count'))==len(payload['monthly'])==48
    assert sum(float(row[2].get('v')) for row in cache)==payload['summary']['complete']['complaints']
    pivot=ET.fromstring(p['xl/pivotTables/pivotTable1.xml'])
    assert pivot.get('name')=='BankPulseMonthly'
    assert pivot.find('s:pageFields/s:pageField',NS).get('fld')=='1'
    assert pivot.find('s:rowFields/s:field',NS).get('x')=='7'
    assert pivot.find('s:dataFields/s:dataField',NS).get('fld')=='2'
    assert 'xl/slicerCaches/slicerCache1.xml' in p and 'xl/slicers/slicer1.xml' in p

def test_formula_protection_and_editable_inputs():
    p=package();styles=ET.fromstring(p['xl/styles.xml']).find('s:cellXfs',NS)
    for sheet,inputs,formula in [(2,['B4'],'B35'),(3,['B9','B10','B11','B12'],'E8')]:
        xml=ET.fromstring(p[f'xl/worksheets/sheet{sheet}.xml'])
        assert xml.find('s:sheetProtection',NS).get('sheet')=='1'
        for address in inputs:
            cell=xml.find(f'.//s:c[@r="{address}"]',NS)
            assert styles[int(cell.get('s','0'))].find('s:protection',NS).get('locked')=='0'
        cell=xml.find(f'.//s:c[@r="{formula}"]',NS)
        assert cell.find('s:f',NS) is not None
        protection=styles[int(cell.get('s','0'))].find('s:protection',NS)
        assert protection is None or protection.get('locked','1')=='1'

def test_charts_have_live_range_references_and_uat_is_unsigned():
    p=package();charts=[n for n in p if '/charts/chart' in n and n.endswith('.xml')]
    assert len(charts)==3
    ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
    for n in charts:
        formulas=ET.fromstring(p[n]).findall('.//c:f',ns)
        assert formulas and all('!' in f.text for f in formulas)
    uat=json.loads((ROOT/'excel/uat.json').read_text())
    assert len(uat)==24 and all(x['Status']=='Not run' and not x['Reviewer'] for x in uat)
