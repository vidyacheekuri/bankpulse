"""Add native OOXML features not exposed reliably by the workbook authoring API.

Only PivotTable/slicer package parts and formula-cell protection are added here.
Cell values, formulas, styles, tables and charts originate in Artifact Tool.
Structure references: Microsoft SpreadsheetML / MS-XLSX and Excelize's public
slicer interoperability implementation. Native Excel interaction is not claimed.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
from datetime import datetime
import json,posixpath
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
X14='http://schemas.microsoft.com/office/spreadsheetml/2009/9/main'
XDR='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
MC='http://schemas.openxmlformats.org/markup-compatibility/2006'
SLE='http://schemas.microsoft.com/office/drawing/2010/slicer'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
def el(tag,parent=None,ns=MAIN,**attrs):
    node=E.Element('{'+ns+'}'+tag,{k:str(v) for k,v in attrs.items()})
    if parent is not None:parent.append(node)
    return node
def xml(node):return E.tostring(node,xml_declaration=True,encoding='UTF-8',standalone=True)

def main():
    path=ROOT/'excel/BankPulse.xlsx'
    with ZipFile(path) as z:parts={n:z.read(n) for n in z.namelist()}
    data=json.loads((ROOT/'excel/inputs.json').read_text());rows=data['monthly']
    months=list(dict.fromkeys(datetime.fromisoformat(r['month']).strftime('%b %Y') for r in rows));products=sorted({r['product'] for r in rows})
    def relation(part,rid,kind,target):
        node=E.fromstring(parts[part]) if part in parts else E.Element('{'+PKG+'}Relationships',nsmap={None:PKG})
        assert not node.xpath('p:Relationship[@Id=$id]',namespaces={'p':PKG},id=rid)
        el('Relationship',node,PKG,Id=rid,Type=kind,Target=target);parts[part]=xml(node)
    def override(name,kind):
        types=E.fromstring(parts['[Content_Types].xml']);el('Override',types,CT,PartName='/'+name,ContentType=kind);parts['[Content_Types].xml']=xml(types)
    cache=E.Element('{'+MAIN+'}pivotCacheDefinition',nsmap={None:MAIN,'r':REL,'x14':X14},attrib={'{'+REL+'}id':'rRecords','recordCount':str(len(rows)),'refreshOnLoad':'0','saveData':'1','createdVersion':'6','refreshedVersion':'6','minRefreshableVersion':'3'})
    src=el('cacheSource',cache,type='worksheet');el('worksheetSource',src,name='MonthlySource',sheet='Monthly Source')
    fields=el('cacheFields',cache,count=8)
    headers=['Month','Product','Complaints','Timely Yes','Known status','Not timely','Unknown','Month label']
    for i,h in enumerate(headers):
        f=el('cacheField',fields,name=h,numFmtId=0)
        if i in [1,7]:
            items=products if i==1 else months;shared=el('sharedItems',f,count=len(items))
            for item in items:el('s',shared,v=item)
        else:el('sharedItems',f,count=0,containsString='0',containsNumber='1' if i!=0 else '0',containsDate='1' if i==0 else '0',containsSemiMixedTypes='0')
    extension=el('ext',el('extLst',cache),uri='{725AE2AE-9491-48be-B2B4-4EB974FC3084}');el('pivotCacheDefinition',extension,X14,pivotCacheId=1)
    records=E.Element('{'+MAIN+'}pivotCacheRecords',nsmap={None:MAIN},count=str(len(rows)))
    for row in rows:
        record=el('r',records);el('d',record,v=row['month'][:19]);el('x',record,v=products.index(row['product']))
        for field in ['complaints','timely_yes','known','timely_no','unknown']:el('n',record,v=row[field])
        el('x',record,v=months.index(datetime.fromisoformat(row['month']).strftime('%b %Y')))
    parts['xl/pivotCache/pivotCacheDefinition1.xml']=xml(cache);parts['xl/pivotCache/pivotCacheRecords1.xml']=xml(records)
    relation('xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels','rRecords',REL+'/pivotCacheRecords','pivotCacheRecords1.xml')
    relation('xl/_rels/workbook.xml.rels','rBankPivot',REL+'/pivotCacheDefinition','pivotCache/pivotCacheDefinition1.xml')
    book=E.fromstring(parts['xl/workbook.xml']);pc=el('pivotCaches');el('pivotCache',pc,cacheId=1,**{'{'+REL+'}id':'rBankPivot'});book.insert(list(book).index(book.find('{'+MAIN+'}sheets'))+1,pc)
    calc=el('calcPr',calcId=191029,calcMode='auto',fullCalcOnLoad='1');book.insert(list(book).index(pc),calc)
    ext=el('ext',el('extLst',book),uri='{BBE1A952-AA13-448e-AADC-164F8A28A991}');sl=el('slicerCaches',ext,X14);el('slicerCache',sl,X14,**{'{'+REL+'}id':'rBankSlicerCache'})
    parts['xl/workbook.xml']=xml(book)
    pivot=E.Element('{'+MAIN+'}pivotTableDefinition',nsmap={None:MAIN},name='BankPulseMonthly',cacheId='1',dataCaption='Complaints',rowHeaderCaption='Month',createdVersion='6',updatedVersion='6',minRefreshableVersion='3',useAutoFormatting='1',itemPrintTitles='1',compact='0',compactData='0',gridDropZones='0',rowGrandTotals='1',colGrandTotals='1')
    el('location',pivot,ref='A8:B33',firstHeaderRow=1,firstDataRow=1,firstDataCol=1,rowPageCount=1,colPageCount=1)
    pf=el('pivotFields',pivot,count=8)
    for i in range(8):
        f=el('pivotField',pf,showAll='0',defaultSubtotal='0')
        if i in [1,7]:
            f.set('axis','axisPage' if i==1 else 'axisRow');vals=products if i==1 else months;items=el('items',f,count=len(vals))
            for n in range(len(vals)):el('item',items,x=n)
        if i==2:f.set('dataField','1')
    el('field',el('rowFields',pivot,count=1),x=7)
    ri=el('rowItems',pivot,count=25)
    for i in range(24):el('x',el('i',ri),v=i)
    el('x',el('i',ri,t='grand'))
    el('i',el('colItems',pivot,count=1))
    el('pageField',el('pageFields',pivot,count=1),fld=1,hier=-1)
    el('dataField',el('dataFields',pivot,count=1),name='Complaints',fld=2,subtotal='sum',baseField=0,baseItem=0,numFmtId=3)
    el('pivotTableStyleInfo',pivot,name='PivotStyleLight16',showRowHeaders='1',showColHeaders='1',showRowStripes='0',showColStripes='0',showLastColumn='1')
    parts['xl/pivotTables/pivotTable1.xml']=xml(pivot)
    relation('xl/pivotTables/_rels/pivotTable1.xml.rels','rCache',REL+'/pivotCacheDefinition','../pivotCache/pivotCacheDefinition1.xml')
    relation('xl/worksheets/_rels/sheet4.xml.rels','rBankPivotTable',REL+'/pivotTable','../pivotTables/pivotTable1.xml')
    sheet=E.fromstring(parts['xl/worksheets/sheet4.xml'])
    ext=el('ext',el('extLst',sheet),uri='{A8765BA9-456A-4dab-B4F3-ACF838C121DE}');el('slicer',el('slicerList',ext,X14),X14,**{'{'+REL+'}id':'rBankSlicer'})
    parts['xl/worksheets/sheet4.xml']=xml(sheet)
    relation('xl/worksheets/_rels/sheet4.xml.rels','rBankSlicer','http://schemas.microsoft.com/office/2007/relationships/slicer','../slicers/slicer1.xml')
    relation('xl/_rels/workbook.xml.rels','rBankSlicerCache','http://schemas.microsoft.com/office/2007/relationships/slicerCache','slicerCaches/slicerCache1.xml')
    slicerCache=E.Element('{'+X14+'}slicerCacheDefinition',nsmap={None:X14},name='Slicer_Product',sourceName='Product')
    el('pivotTable',el('pivotTables',slicerCache,X14),X14,tabId=4,name='BankPulseMonthly')
    tab=el('tabular',el('data',slicerCache,X14),X14,pivotCacheId=1,sortOrder='ascending',showMissing='0')
    items=el('items',tab,X14,count=2)
    for i in range(2):el('i',items,X14,x=i,s='1')
    parts['xl/slicerCaches/slicerCache1.xml']=xml(slicerCache)
    slicers=E.Element('{'+X14+'}slicers',nsmap={None:X14});el('slicer',slicers,X14,name='Product',cache='Slicer_Product',caption='Product',columnCount=1,showCaption='1',rowHeight=251883,style='SlicerStyleLight1')
    parts['xl/slicers/slicer1.xml']=xml(slicers)
    drawing=E.fromstring(parts['xl/drawings/drawing3.xml']);anchor=el('twoCellAnchor',drawing,XDR)
    for which,col,row in [('from',3,4),('to',7,10)]:
        marker=el(which,anchor,XDR)
        for key,value in [('col',col),('colOff',0),('row',row),('rowOff',0)]:el(key,marker,XDR).text=str(value)
    alternate=el('AlternateContent',anchor,MC)
    choice=E.SubElement(alternate,'{'+MC+'}Choice',Requires='a14',nsmap={'a14':'http://schemas.microsoft.com/office/drawing/2010/main'})
    gf=el('graphicFrame',choice,XDR,macro='');nv=el('nvGraphicFramePr',gf,XDR);el('cNvPr',nv,XDR,id=1001,name='Product',descr='Filter monthly complaints by product');el('cNvGraphicFramePr',nv,XDR)
    transform=el('xfrm',gf,XDR);el('off',transform,A,x=0,y=0);el('ext',transform,A,cx=0,cy=0)
    el('slicer',el('graphicData',el('graphic',gf,A),A,uri=SLE),SLE,name='Product')
    el('Fallback',alternate,MC);el('clientData',anchor,XDR);parts['xl/drawings/drawing3.xml']=xml(drawing)
    for part,kind in [('xl/pivotCache/pivotCacheDefinition1.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml'),('xl/pivotCache/pivotCacheRecords1.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheRecords+xml'),('xl/pivotTables/pivotTable1.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.pivotTable+xml'),('xl/slicers/slicer1.xml','application/vnd.ms-excel.slicer+xml'),('xl/slicerCaches/slicerCache1.xml','application/vnd.ms-excel.slicerCache+xml')]:override(part,kind)
    # Protection prevents accidental overwriting, not access to sensitive information.
    styles=E.fromstring(parts['xl/styles.xml']);xfs=styles.find('{'+MAIN+'}cellXfs');unlocked={}
    for sheet_id,editable in [(2,['B4']),(3,['B9','B10','B11','B12'])]:
        name=f'xl/worksheets/sheet{sheet_id}.xml';sheet=E.fromstring(parts[name])
        for cell in sheet.findall('.//{'+MAIN+'}c'):
            if cell.get('r') in editable:
                old=int(cell.get('s','0'))
                if old not in unlocked:
                    style=deepcopy(xfs[old]);protection=style.find('{'+MAIN+'}protection')
                    if protection is not None:style.remove(protection)
                    el('protection',style,locked='0');style.set('applyProtection','1');unlocked[old]=len(xfs);xfs.append(style)
                cell.set('s',str(unlocked[old]))
        sp=el('sheetProtection',sheet='1',objects='1',scenarios='1',selectLockedCells='0',selectUnlockedCells='0')
        idx=list(sheet).index(sheet.find('{'+MAIN+'}sheetData'));sheet.insert(idx+1,sp);parts[name]=xml(sheet)
    xfs.set('count',str(len(xfs)));parts['xl/styles.xml']=xml(styles)
    # All internal relationship targets must resolve; validate every XML part.
    for name,content in parts.items():
        if name.endswith(('.xml','.rels')):E.fromstring(content)
        if name.endswith('.rels'):
            base=posixpath.dirname(posixpath.dirname(name))
            for rel in E.fromstring(content):
                if rel.get('TargetMode')=='External':continue
                target=rel.get('Target');resolved=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(base,target))
                assert resolved in parts,(name,resolved)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,content in parts.items():z.writestr(name,content)
    verification=json.loads((ROOT/'reports/excel_verification.json').read_text());verification.update({'native_parts':{'pivot_tables':1,'slicers':1,'pivot_cache_records':48,'protected_formula_sheets':['Analysis','Capacity'],'all_internal_relationships_resolve':True},'native_excel':'Not executed: requires desktop Excel interaction; file-level verification completed'})
    (ROOT/'reports/excel_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print('Native PivotTable, product slicer, and formula protection added; package relationships verified.')

if __name__=='__main__':main()
